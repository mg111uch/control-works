"""Random-target policy training (drift lessons applied). Usage: python train.py [--episodes N]"""
import argparse
import csv
import random
import sys
import time
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
from main import RocketEnv

X_RANGE = (-350, 350)
ALT_RANGE = (100, 500)
N_ACTIONS = 2
OBS_DIM = 11

class ActorCritic(nn.Module):
    """Shared-trunk PPO actor-critic. Layer names match main.PolicyNetwork for partial loads."""
    def __init__(self, input_dim=OBS_DIM, hidden_dim=128, action_dim=N_ACTIONS):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.mean_head = nn.Linear(hidden_dim, action_dim)
        self.log_std = nn.Parameter(torch.zeros(action_dim))
        self.value_head = nn.Linear(hidden_dim, 1)

    def forward(self, x):
        h = torch.relu(self.fc1(x))
        h = torch.relu(self.fc2(h))
        return self.mean_head(h), torch.exp(self.log_std).expand_as(self.mean_head(h)), self.value_head(h).squeeze(-1)

    def _batch(self, x):
        return x.unsqueeze(0) if x.dim() == 1 else x

    def sample(self, x):
        xb = self._batch(x)
        mean, std, _ = self.forward(xb)
        d = torch.distributions.Normal(mean, std)
        a = d.sample()
        lp = d.log_prob(a).sum(-1)
        return (a.squeeze(0), lp.squeeze(0)) if x.dim() == 1 else (a, lp)

    def value(self, x):
        xb = self._batch(x)
        return self.forward(xb)[2].squeeze(0) if x.dim() == 1 else self.forward(xb)[2]

    def evaluate(self, states, actions_raw):
        mean, std, vals = self.forward(states)
        d = torch.distributions.Normal(mean, std)
        lp = d.log_prob(actions_raw).sum(-1)
        ent = d.entropy().sum(-1)
        return lp, ent, vals

def seed_all(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

def sample_target(env, p=1.0):
    # Curriculum: p=0 close/low, p=1 full viewport
    xr = (-350, 350)
    ar = (100, 500)
    if p < 1.0:
        xr = (-60 - 290 * p, 60 + 290 * p)
        ar = (80, 160 + 340 * p)
    env.target_x = random.uniform(*xr)
    env.target_alt = random.uniform(*ar)

def obs_with_target(env, base_obs):
    dx = (env.target_x - env.x) / 1000.0
    dy = (env.target_y - env.y) / 1000.0
    return np.concatenate([base_obs, np.array([dx, dy], dtype=np.float32)])

def diversity(actions):
    if not actions:
        return 0, 0.0
    bins = [0 if a < -10 else (2 if a > 10 else 1) for a, _ in actions]
    uniq = len(set(bins))
    p = np.bincount(bins, minlength=3) / len(bins)
    ent = float(-(p[p > 0] * np.log(p[p > 0])).sum())
    return uniq, ent

def run_episode(env, policy, max_steps, log_path=None, shaping=True, curriculum_p=1.0):
    sample_target(env, curriculum_p)
    obs = obs_with_target(env, env.reset())
    # Fuel curriculum: light early (T/W easy) → full late
    env.propMass = env.propMass_initial * random.uniform(0.35, 0.35 + 0.65 * curriculum_p)
    log_probs, rewards, actions = [], [], []
    states, raws, vals, dones = [], [], [], []
    x0, y0 = env.x, env.y
    path, traj = 0.0, []
    done, steps = False, 0
    px, py = env.x, env.y
    prev_dist = abs(env.target_x - env.x) + abs(env.target_y - env.y)
    was_up = False
    with torch.no_grad():
        while not done and steps < max_steps:
            t = torch.tensor(obs, dtype=torch.float32)
            a, lp = policy.sample(t)
            v = policy.value(t) if hasattr(policy, "value") else torch.tensor(0.0)
            act = [float(np.tanh(a[0].item()) * 30), float(torch.sigmoid(a[1]).item())]
            base, r, done, _ = env.step(act)
            if shaping:
                dist = abs(env.target_x - env.x) + abs(env.target_y - env.y)
                r += 2.0 * (prev_dist - dist) / 1000.0  # progress bonus
                prev_dist = dist
                if env.has_launched and not was_up:
                    r += 2.0  # one-time liftoff bonus
                    was_up = True
                r += 0.2 * (env.y - env.y_reset) / 1000.0  # climb shaping
            path += abs(env.x - px) + abs(env.y - py)
            px, py = env.x, env.y
            if log_path is not None:
                traj.append([steps, env.x, env.y, env.dx, env.dy, env.theta, act[0], act[1], r])
            obs = obs_with_target(env, base)
            log_probs.append(lp)
            rewards.append(r)
            actions.append(act)
            states.append(t)
            raws.append(a.detach())
            vals.append(v.detach())
            dones.append(done)
            steps += 1
    if not done:
        with torch.no_grad():
            boot = policy.value(torch.tensor(obs, dtype=torch.float32)) if hasattr(policy, "value") else torch.tensor(0.0)
    else:
        boot = torch.tensor(0.0)
    if log_path is not None:
        with open(log_path, "w", newline="") as f:
            csv.writer(f).writerow(["step", "x", "y", "dx", "dy", "theta", "gimbal", "thr", "rew"])
            csv.writer(f).writerows(traj)
    uniq, ent = diversity(actions)
    disp = abs(env.x - x0) + abs(env.y - y0)
    ok = 1 if rewards and rewards[-1] > 500 else 0
    batch = {"states": torch.stack(states), "raws": torch.stack(raws),
             "logps": torch.stack(log_probs), "vals": torch.stack(vals),
             "rewards": torch.tensor(rewards, dtype=torch.float32),
             "dones": torch.tensor(dones, dtype=torch.float32), "boot": boot}
    return batch, rewards, {"succ": ok, "disp": disp, "path": path, "uniq": uniq, "ent": ent, "steps": steps}

def ppo_update(policy, opt, batch, gamma=0.99, lam=0.95, clip=0.2, epochs=4, mb=256):
    n = len(batch["rewards"])
    if n < 2:
        return 0.0, 0.0, 0.0
    with torch.no_grad():
        # Scale: raw returns hit ~1000 (sparse bonus) which blows up shared-trunk value grads
        scale = 100.0
        rw = batch["rewards"] / scale
        vv = torch.cat([batch["vals"] / scale, (batch["boot"] / scale).unsqueeze(0)])
        adv, rets, g, l = [], [], 0.0, 0.0
        for i in reversed(range(len(rw))):
            mask = 1.0 - batch["dones"][i].item()
            g = rw[i].item() + gamma * mask * g
            d = rw[i].item() + gamma * mask * vv[i + 1].item() - vv[i].item()
            l = d + gamma * lam * mask * l
            adv.insert(0, d)
            rets.insert(0, g)
        adv = torch.tensor(adv, dtype=torch.float32)
        rets = torch.tensor(rets, dtype=torch.float32)
        adv = (adv - adv.mean()) / (adv.std() + 1e-8)
    n = len(adv)
    tot_pl, tot_vl, tot_kl, nb = 0.0, 0.0, 0.0, 0
    for _ in range(epochs):
        for i in torch.randperm(n).split(mb):
            lp, ent, v = policy.evaluate(batch["states"][i], batch["raws"][i])
            ratio = torch.exp(lp - batch["logps"][i])
            pg = torch.min(ratio * adv[i], torch.clamp(ratio, 1 - clip, 1 + clip) * adv[i]).mean()
            vl = ((v - rets[i]) ** 2).mean()
            loss = -pg + 0.5 * vl - 0.01 * ent.mean()
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(policy.parameters(), 0.5)
            opt.step()
            tot_pl += pg.item()
            tot_vl += vl.item()
            tot_kl += (batch["logps"][i] - lp).mean().item()
            nb += 1
    return tot_pl / nb, tot_vl / nb, tot_kl / nb

def eval_clean(env, policy, eps=5, max_steps=1000, seed=0, fuel_fracs=(0.35, 0.675, 1.0)):
    tot, succ, disp = [], 0, []
    n_buckets = len(fuel_fracs)
    for k in range(eps):
        seed_all(seed + k)
        sample_target(env, 1.0)
        obs = obs_with_target(env, env.reset())
        env.propMass = env.propMass_initial * fuel_fracs[k % n_buckets]  # fuel-mix eval: cycle seeds across buckets
        R, acts, steps, done = 0.0, [], 0, False
        x0, y0 = env.x, env.y
        while not done and steps < max_steps:
            with torch.no_grad():
                a, _ = policy.sample(torch.tensor(obs, dtype=torch.float32))
            act = [float(np.tanh(a[0].item()) * 30), float(torch.sigmoid(a[1]).item())]
            base, r, done, _ = env.step(act)
            obs = obs_with_target(env, base)
            R += r
            acts.append(act)
            steps += 1
        ok = 1 if R > 500 else 0
        succ += ok
        disp.append(abs(env.x - x0) + abs(env.y - y0))
        tot.append(R)
    return sum(tot) / len(tot), {"rate": succ / eps, "disp": sum(disp) / len(disp)}

def train(episodes=500, max_steps=1000, gamma=0.99, lr=3e-4, seed=7, model_dir=None,
          patience=4, min_delta=1.0):
    seed_all(seed)
    out = Path(model_dir) if model_dir else BASE_DIR / "models"
    out.mkdir(parents=True, exist_ok=True)
    env = RocketEnv(render=False)
    policy = ActorCritic()
    assert policy.mean_head.out_features == N_ACTIONS == 2, "parity: policy outs != env actions"
    with torch.no_grad():
        policy.mean_head.bias[1] += 2.0  # throttle prior ~0.88: near hover so liftoff is discoverable
    _bc = BASE_DIR / "models" / "rocket_policy_bc.pth"
    if _bc.exists():
        policy.load_state_dict(torch.load(str(_bc), map_location="cpu", weights_only=True))
        print(f"warm-start: loaded behavior-cloned weights from {_bc.name}", flush=True)
    opt = optim.Adam(policy.parameters(), lr=lr)
    hist, best, best_ep, stale = [], -1e18, -1, 0
    best_score, pad_strikes = (0.0, -1e18), 0
    last_loss = (0.0, 0.0, 0.0)
    for ep in range(episodes):
        p = min(1.0, ep / max(1, episodes // 3))  # curriculum: full range by 1/3 of run
        batch, rews, m = run_episode(env, policy, max_steps, curriculum_p=p,
            log_path=str(out / "traj_last.csv") if ep == episodes - 1 else None)
        if not rews:
            continue
        last_loss = ppo_update(policy, opt, batch, gamma=gamma)
        tot = sum(rews)
        hist.append(tot)
        if (ep + 1) % 50 == 0:
            clean, info = eval_clean(env, policy)
            score = (info["rate"], clean)
            if score[0] > best_score[0] or (score[0] == best_score[0] and clean > best + min_delta):
                best, best_ep, best_score, stale = clean, ep, score, 0
                torch.save(policy.state_dict(), str(out / "rocket_policy_best.pth"))
                improved = "IMPROVED"
            else:
                stale += 1
                improved = f"stale {stale}/{patience}"
            pad = info["disp"] < 5.0
            print(f"ep {ep} rew {tot:.1f} clean {clean:.1f} rate {info['rate']:.2f} disp {info['disp']:.0f} pl {last_loss[0]:.3f} vl {last_loss[1]:.1f} kl {last_loss[2]:.4f} best {best:.1f}@{best_ep} {improved}")
            if pad:
                pad_strikes += 1
                print(f"PAD-SIT gate: avg clean disp {info['disp']:.1f}m ({pad_strikes}/2)")
            else:
                pad_strikes = 0
            if pad_strikes >= 2:
                print("early-stop: policy sitting on pad twice in a row — inspect env/reward")
                break
            if stale >= patience:
                print(f"early-stop: no clean gain >{min_delta} for {patience} evals ({patience*50} eps)")
                break
        else:
            print(f"ep {ep} rew {tot:.1f} succ {m['succ']} disp {m['disp']:.0f} uniq {m['uniq']} ent {m['ent']:.2f}")
    torch.save(policy.state_dict(), str(out / "rocket_policy_random.pth"))
    plt.plot(hist)
    plt.xlabel("episode")
    plt.ylabel("return")
    plt.savefig(str(out / "train_curve.png"))
    print(f"saved best_ep={best_ep} clean={best:.1f}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--episodes", type=int, default=500)
    p.add_argument("--steps", type=int, default=1000)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--model-dir", type=str, default=None)
    p.add_argument("--patience", type=int, default=4)
    args = p.parse_args()
    train(args.episodes, args.steps, seed=args.seed, model_dir=args.model_dir, patience=args.patience)
