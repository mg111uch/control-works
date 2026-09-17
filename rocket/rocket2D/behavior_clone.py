"""Behavior-clone ActorCritic (train.py) from scripted PD rollouts.

Collects (obs11, raw-action) pairs with the PD controller, fits policy mean
with MSE, saves warm-start weights to models/rocket_policy_bc.pth.
Usage: `python behavior_clone.py [--eps 120 --epochs 30]`.
"""
import argparse
import random
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
from main import RocketEnv  # noqa: E402
from train import ActorCritic, obs_with_target  # noqa: E402
from pd_controller import pd_action, run_pd, to_raw  # noqa: E402


def collect(eps=120, max_steps=1000, seed=0, fuels=(0.35, 0.675, 1.0)):
    env = RocketEnv(render=False)
    XS, AS, reach = [], [], 0
    for k in range(eps):
        random.seed(seed + k)
        np.random.seed(seed + k)
        env.sample_target()
        obs = obs_with_target(env, env.reset())
        env.target_y = env.y_reset + env.target_alt
        env.propMass = env.propMass_initial * fuels[k % len(fuels)]
        done, steps = False, 0
        while not done and steps < max_steps:
            a = pd_action(env)
            XS.append(obs)
            AS.append(to_raw(a))
            obs, _, done, _ = env.step(a)
            obs = obs_with_target(env, obs)
            steps += 1
        dist = float(np.hypot(env.target_x - env.x, env.target_y - env.y))
        reach += dist < 50
    print(f"PD demo reach rate: {reach}/{eps} = {reach / eps:.2f} ({len(XS)} steps)")
    return (torch.tensor(np.array(XS), dtype=torch.float32),
            torch.tensor(np.array(AS), dtype=torch.float32), reach / eps)


def clone(X, A, epochs=30, mb=256, lr=1e-3, seed=0):
    torch.manual_seed(seed)
    policy = ActorCritic()
    opt = torch.optim.Adam(policy.parameters(), lr=lr)
    loss_fn = nn.MSELoss()
    n = len(X)
    for e in range(epochs):
        tot, nb = 0.0, 0
        for i in torch.randperm(n).split(mb):
            mean, _, _ = policy.forward(X[i])
            loss = loss_fn(mean, A[i])
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(policy.parameters(), 0.5)
            opt.step()
            tot += loss.item()
            nb += 1
        if (e + 1) % 5 == 0 or e == 0:
            print(f"epoch {e + 1}/{epochs} mse {tot / nb:.4f}")
    with torch.no_grad():
        final = loss_fn(policy.forward(X)[0], A).item()
    return policy, final


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--eps", type=int, default=120)
    p.add_argument("--epochs", type=int, default=30)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--out", type=str, default=str(BASE_DIR / "models" / "rocket_policy_bc.pth"))
    a = p.parse_args()
    X, A, rate = collect(a.eps, seed=a.seed)
    policy, loss = clone(X, A, epochs=a.epochs, seed=a.seed)
    torch.save(policy.state_dict(), a.out)
    print(f"saved {a.out} clone_mse={loss:.4f} pd_reach={rate:.2f}")


if __name__ == "__main__":
    main()
