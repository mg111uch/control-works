"""PPO via pufferlib vectorization. Usage: python puffer_train.py [--num-envs 8] [--updates 30]"""
import argparse
import random
import sys
import time
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import gymnasium
import pufferlib
import pufferlib.vector
import pufferlib.emulation

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
from main import RocketEnv
from train import ActorCritic, eval_clean, obs_with_target, diversity

OBS_DIM = 11


class RocketGym(gymnasium.Env):
    def __init__(self, curriculum_p=1.0, max_steps=1000):
        self.env = RocketEnv(render=False)
        self.curriculum_p = curriculum_p
        self.max_steps = max_steps
        self.observation_space = gymnasium.spaces.Box(
            low=-5, high=5, shape=(OBS_DIM,), dtype=np.float32)
        self.action_space = gymnasium.spaces.Box(
            low=-3, high=3, shape=(2,), dtype=np.float32)
        self._steps = 0

    def seed(self, seed):
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)

    def reset(self, seed=None):
        if seed is not None:
            self.seed(seed)
        p = self.curriculum_p
        xr = (-60 - 290 * p, 60 + 290 * p) if p < 1 else (-350, 350)
        ar = (80, 160 + 340 * p) if p < 1 else (100, 500)
        self.env.target_x = random.uniform(*xr)
        self.env.target_alt = random.uniform(*ar)
        base = self.env.reset()
        self.env.propMass = self.env.propMass_initial * random.uniform(0.35, 0.35 + 0.65 * p)
        self._steps = 0
        self._prev = abs(self.env.target_x - self.env.x) + abs(self.env.target_y - self.env.y)
        self._up = False
        return obs_with_target(self.env, base).astype(np.float32), {}

    def step(self, action):
        a = np.asarray(action, dtype=np.float32).ravel()
        act = [float(np.tanh(a[0]) * 30), float(1 / (1 + np.exp(-a[1])))]
        base, r, done, _ = self.env.step(act)
        dist = abs(self.env.target_x - self.env.x) + abs(self.env.target_y - self.env.y)
        r += 2.0 * (self._prev - dist) / 1000.0
        self._prev = dist
        if self.env.has_launched and not self._up:
            r += 2.0
            self._up = True
        r += 0.2 * (self.env.y - self.env.y_reset) / 1000.0
        self._steps += 1
        trunc = self._steps >= self.max_steps
        return obs_with_target(self.env, base).astype(np.float32), float(r), bool(done), bool(trunc), {}


def make_creator(p=1.0, max_steps=1000):
    def fn(buf=None):
        return pufferlib.emulation.GymnasiumPufferEnv(
            env_creator=lambda: RocketGym(curriculum_p=p, max_steps=max_steps), buf=buf)
    return fn


def ppo_update_vec(policy, opt, states, raws, logps, adv, rets, epochs=4, mb=512):
    n = len(adv)
    tot = [0.0, 0.0, 0.0, 0]
    for _ in range(epochs):
        for i in torch.randperm(n).split(mb):
            lp, ent, v = policy.evaluate(states[i], raws[i])
            ratio = torch.exp(lp - logps[i])
            pg = torch.min(ratio * adv[i], torch.clamp(ratio, 0.8, 1.2) * adv[i]).mean()
            vl = ((v - rets[i]) ** 2).mean()
            loss = -pg + 0.5 * vl - 0.01 * ent.mean()
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(policy.parameters(), 0.5)
            opt.step()
            tot[0] += pg.item()
            tot[1] += vl.item()
            tot[2] += (logps[i] - lp).mean().item()
            tot[3] += 1
    return tot[0] / tot[3], tot[1] / tot[3], tot[2] / tot[3]


def train(num_envs=8, steps_per_env=256, updates=30, gamma=0.99, lam=0.95,
          lr=3e-4, seed=11, backend="serial", model_dir=None):
    out = Path(model_dir) if model_dir else BASE_DIR / "models"
    out.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(seed)
    np.random.seed(seed)
    be = pufferlib.vector.Serial if backend == "serial" else pufferlib.vector.Multiprocessing
    vec = pufferlib.vector.make(make_creator(), backend=be, num_envs=num_envs)
    n = vec.num_envs
    policy = ActorCritic()
    with torch.no_grad():
        policy.mean_head.bias[1] += 2.0
    opt = optim.Adam(policy.parameters(), lr=lr)
    vec.async_reset(seed=seed)
    obs, *_ = vec.recv()
    obs = np.asarray(obs, dtype=np.float32)
    logps = np.zeros(n, dtype=np.float32)
    vals = np.zeros(n, dtype=np.float32)
    with torch.no_grad():
        t = torch.tensor(obs)
        _, lp0 = policy.sample(t)
        logps = lp0.numpy()
        vals = policy.value(t).numpy()
    succ_hist = []
    for u in range(updates):
        p = min(1.0, u / max(1, updates // 3))
        for e in vec.envs:
            e.env.curriculum_p = p
        S, A, LP, R, D, V = [], [], [], [], [], []
        ep_rew, ep_n, ep_succ = 0.0, 0, 0
        for _ in range(steps_per_env):
            with torch.no_grad():
                t = torch.tensor(obs)
                a, lp = policy.sample(t)
                v = policy.value(t)
            arr = a.numpy()
            if hasattr(vec, "send"):
                vec.send(arr)
                obs2, rew, term, trunc, *_ = vec.recv()
            else:
                obs2, rew, term, trunc, *_ = pufferlib.vector.step(vec, arr)
            done = np.logical_or(term, trunc)
            S.append(obs.copy())
            A.append(arr.copy())
            LP.append(lp.numpy().copy())
            R.append(np.asarray(rew, dtype=np.float32).copy())
            D.append(done.astype(np.float32).copy())
            V.append(v.numpy().copy())
            obs = np.asarray(obs2, dtype=np.float32)
            with torch.no_grad():
                t = torch.tensor(obs)
                _, lp = policy.sample(t)
                logps = lp.numpy()
                vals = policy.value(t).numpy()
        S = torch.tensor(np.array(S), dtype=torch.float32)
        A = torch.tensor(np.array(A), dtype=torch.float32)
        LP = torch.tensor(np.array(LP), dtype=torch.float32)
        R = np.array(R, dtype=np.float32) / 100.0
        D = np.array(D, dtype=np.float32)
        V = np.array(V, dtype=np.float32)
        with torch.no_grad():
            last_v = policy.value(torch.tensor(obs, dtype=torch.float32)).numpy()
        adv = np.zeros_like(R)
        lastgaelam = np.zeros(n, dtype=np.float32)
        for t in reversed(range(steps_per_env)):
            nxt_v = last_v if t == steps_per_env - 1 else V[t + 1]
            mask = 1.0 - D[t]
            delta = R[t] + gamma * mask * nxt_v - V[t]
            lastgaelam = delta + gamma * lam * mask * lastgaelam
            adv[t] = lastgaelam
        rets = adv + V
        adv = torch.tensor(adv, dtype=torch.float32)
        rets = torch.tensor(rets, dtype=torch.float32)
        adv = (adv - adv.mean()) / (adv.std() + 1e-8)
        pl, vl, kl = ppo_update_vec(policy, opt, S.reshape(-1, OBS_DIM), A.reshape(-1, 2),
                                    LP.reshape(-1), adv.reshape(-1), rets.reshape(-1))
        print(f"upd {u} p={p:.2f} pl {pl:.4f} vl {vl:.3f} kl {kl:.5f} steps {steps_per_env * n}", flush=True)
        if (u + 1) % 10 == 0:
            from train import eval_clean as ev
            env0 = RocketEnv(render=False)
            c, info = ev(env0, policy)
            print(f"EVAL upd {u} clean {c:.1f} rate {info['rate']:.2f} disp {info['disp']:.0f}", flush=True)
            torch.save(policy.state_dict(), str(out / "puffer_policy.pth"))
    torch.save(policy.state_dict(), str(out / "puffer_policy.pth"))
    print("saved puffer_policy.pth")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--num-envs", type=int, default=8)
    p.add_argument("--steps-per-env", type=int, default=256)
    p.add_argument("--updates", type=int, default=30)
    p.add_argument("--seed", type=int, default=11)
    p.add_argument("--backend", type=str, default="serial")
    args = p.parse_args()
    train(args.num_envs, args.steps_per_env, args.updates, seed=args.seed, backend=args.backend)
