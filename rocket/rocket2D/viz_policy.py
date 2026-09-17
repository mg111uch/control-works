"""Viz trained rocket policy (inspection only, no training).

Loads models/rocket_policy_best.pth into train.ActorCritic (exact arch),
renders deterministic-mean flight on display :0, exits after --seconds.
Usage: myenv/bin/python viz_policy.py --seconds 60 --seed 7
"""
import argparse
import sys
import time

import numpy as np
import torch

from main import RocketEnv
from train import ActorCritic, seed_all, sample_target, obs_with_target

BASE = __import__("pathlib").Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, default=60.0)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--weights", type=str, default=str(BASE / "models" / "rocket_policy_best.pth"))
    args = ap.parse_args()

    seed_all(args.seed)
    policy = ActorCritic()
    policy.load_state_dict(torch.load(args.weights, map_location="cpu", weights_only=True))
    policy.eval()

    env = RocketEnv(render=True)
    sample_target(env, 1.0)
    obs = obs_with_target(env, env.reset())
    print(f"Viz {args.weights} -> target ({env.target_x:.0f}, {env.target_alt:.0f})", flush=True)

    t_end = time.time() + args.seconds
    with torch.no_grad():
        while time.time() < t_end:
            mean = policy.forward(torch.tensor(obs, dtype=torch.float32))[0]
            act = [float(np.tanh(mean[0].item()) * 30), float(torch.sigmoid(mean[1]).item())]
            obs, _, done, _ = env.step(act)
            obs = obs_with_target(env, obs)
            env.render()
            if done:
                sample_target(env, 1.0)
                obs = obs_with_target(env, env.reset())
    print("Viz ended.", flush=True)


if __name__ == "__main__":
    sys.exit(main())
