"""Scripted PD controller for Rocket2D warm-start (no learning).

Uses env state directly: gimbal PD on tilt toward a lean angle demanded by
lateral position/velocity error; throttle = hover feedforward + vertical PD.
Physical actions out: [gimbal_deg (-30..30), throttle (0..1)].
Headless smoke: `python pd_controller.py [--eps N]`.
"""
import argparse
import math
import random
import sys
from pathlib import Path

import numpy as np

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
from main import RocketEnv  # noqa: E402

KP_X, KD_X, TH_MAX = 0.0012, 0.008, 0.25   # lateral -> lean-angle demand (rad)
KP_TH, KD_TH = 2.5, 1.2                    # tilt PD -> gimbal (rad gains)
KP_ALT, KD_ALT = 0.0015, 0.009             # vertical PD -> throttle
GIMBAL_LIM, RAW_CLIP = 30.0, 0.9667


def hover_throttle(env):
    m = env.dryMass + env.propMass
    g = env.G * env.M_earth / (env.R_earth + env.y) ** 2
    return float(m * g / env.Raptor_thrust)


def pd_action(env):
    ex, ey = env.target_x - env.x, env.target_y - env.y
    theta_des = float(np.clip(KP_X * ex - KD_X * env.dx, -TH_MAX, TH_MAX))
    gimbal = (KP_TH * (theta_des - env.theta) - KD_TH * env.dtheta) * 180 / math.pi
    thr = hover_throttle(env) + KP_ALT * ey - KD_ALT * env.dy
    return [float(np.clip(gimbal, -GIMBAL_LIM, GIMBAL_LIM)), float(np.clip(thr, 0, 1))]


def to_raw(act):
    g = float(np.clip(act[0] / GIMBAL_LIM, -RAW_CLIP, RAW_CLIP))
    t = float(np.clip(act[1], 0.02, 0.98))
    return [math.atanh(g), math.log(t / (1 - t))]


def run_pd(env, max_steps=1000, fuel_frac=None):
    obs, acts, done, steps = env.reset(), [], False, 0
    if fuel_frac is not None:
        env.propMass = env.propMass_initial * fuel_frac
    while not done and steps < max_steps:
        a = pd_action(env)
        obs, r, done, _ = env.step(a)
        acts.append(a)
        steps += 1
    dist = math.hypot(env.target_x - env.x, env.target_y - env.y)
    return r, dist, steps, acts


def smoke(eps=20, max_steps=1000, seed=0, fuels=(0.35, 0.675, 1.0)):
    env = RocketEnv(render=False)
    reach, dists = 0, []
    for k in range(eps):
        random.seed(seed + k)
        np.random.seed(seed + k)
        env.sample_target()
        fuel = fuels[k % len(fuels)]
        r, dist, steps, _ = run_pd(env, max_steps, fuel_frac=fuel)
        ok = dist < 50
        reach += ok
        dists.append(dist)
        print(f"ep {k} tgt=({env.target_x:.0f},{env.target_alt:.0f}) "
              f"end=({env.x:.0f},{env.y - env.y_reset:.0f}) dist={dist:.0f} "
              f"steps={steps} {'REACH' if ok else ''}")
    print(f"PD reach rate: {reach}/{eps} = {reach / eps:.2f}, mean dist {sum(dists) / len(dists):.0f}m")
    return reach / eps


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--eps", type=int, default=20)
    p.add_argument("--steps", type=int, default=1000)
    p.add_argument("--seed", type=int, default=0)
    a = p.parse_args()
    smoke(a.eps, a.steps, a.seed)
