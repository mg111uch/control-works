# rocket2D — 2D rocket guidance (GNC)

Fly a Starship-class rocket to a random viewport target. Manual play + RL training in one dir.

## Files

| File | Lines | Purpose |
|---|---|---|
| `main.py` | 473 | `RocketEnv` physics + pygame manual play + legacy fixed-target `train()` |
| `train.py` | 273 | Random-target PPO (`ActorCritic`, GAE, curriculum, clean-eval gates) |
| `puffer_train.py` | 193 | Same PPO via pufferlib 2.0.6 vectorization (`RocketGym` + Serial×N) |
| `imgs/` | — | `falcon9_2d_thrust.png` sprite |

## Quick start (conda env `myenv`)

```bash
cd control-works/rocket/rocket2D
# Manual play (fly to the green crosshair)
conda run -n myenv python main.py        # choose 1
# Single-env PPO (weights → models/, --model-dir overrides)
conda run -n myenv python -u train.py --episodes 120 --seed 11
# Puffer vectorized PPO (8 envs)
conda run -n myenv python -u puffer_train.py --num-envs 8 --updates 30 --seed 11
# Detached with file log:
LOG=logs/train.log conda run --no-capture-output -n myenv python -u train.py --episodes 120 --seed 11 &
```

Manual controls: `Left/Right` tilt, `Up/Down` throttle, `R` new random target.

## Env (`RocketEnv`, `main.py`)

- Fixed physics `dt=0.02` (never wall-clock). Starship scale: dry 120t, prop 1200t, 13.8MN (T/W ~1.06 — liftoff needs throttle >0.94, intentionally hard).
- Target: `x∈[-350,350]m`, `alt∈[100,500]m`, drawn as green crosshair + HUD distance.
- Obs 9D normalized (+2D rel-target in trainers = 11D). Actions: gimbal ±30°, throttle 0–1 (trainers sample Gaussian → `tanh`/`sigmoid`).
- Reward: `-dist/1000`, `+1000` reach (<50m), `-100` crash/out-of-fuel. Trainers add liftoff +2 / progress / climb shaping.
- Wind: 0.8–1.0MN gusts every 5–15s sim-time (the "drift left on takeoff" cause).

## Training notes (`train.py`)

- Throttle-bias init +2.0 (prior 0.88) + fuel curriculum (35%→full) — unbiased policies never lift; see kernel `rocket_liftoff_discovery`.
- Clean eval: 5 seeded random targets, scored by (success rate, return); best-model on that.
- Gates: PAD-SIT (avg clean disp <5m twice → stop), stale-eval early-stop (`--patience 4`).
- PPO: shared-trunk actor-critic, GAE λ=0.95, clip 0.2, 4 epochs, returns /100. GAE gotcha logged as `ppo_gae_double_count` (never fold λ-accumulator into δ).

## Puffer port (`puffer_train.py`)

Needs `pufferlib==2.0.6` — already installed in `myenv` (`python -c "import pufferlib"` → 2.0.6; reinstall with `pip install "pufferlib==2.0.6"` if needed). 2.x line provides `emulation` + `vector`; 3.x/4.x are CUDA-native. `RocketGym` wraps the env (Box spaces), `vector.make(..., Serial)` batches rollouts; PPO update reused from `train.py`.

## Artifacts

`models/` (weights + run outputs: `rocket_policy_random.pth` last, `rocket_policy_best.pth` best clean, `puffer_policy.pth`, `traj_last.csv`, `train_curve.png`; `--model-dir` overrides). `logs/` (shell `train*.log` redirects). `main.py` legacy `rocket_policy.pth` path is dormant (file never saved; falls back to manual mode).

## Status

Single-env REINFORCE → parked (hover exploit). PPO flies in training (disp to ~2000m) but eval success rate 0.00 on full fuel — curriculum/eval mismatch open. Prior art that shaped this: kernel topics `controlworks_arcade_games` (drift_racer) + `controlworks_policy_playbook`.

## Next

- [x] 1. Fair eval: grade on curriculum fuel mix (light→full), not full-fuel only — current metric tests what training never practices.
- [x] 2. Widen success: tolerance <50m → staged (250m/100m/50m) bonus so random aim earns partial gradient.
- [x] 4. Warm-start: behavior-clone a scripted PD controller (or manual-play logs) before PPO — solves the <50m discovery problem directly. (`pd_controller.py` reach 0.70, `behavior_clone.py` MSE 0.0027 → `models/rocket_policy_bc.pth`; `train.py` auto-loads it when present.)
- [ ] 3. Multiprocessing backend in `puffer_train.py` (Serial ≈1.3× here; physics is cheap, batch PPO is the prize).
- [ ] 5. Warm-start PPO run: `myenv/bin/python -u train.py --episodes 120 --seed 11` (direct binary, never `conda run`), then per-fuel-bucket clean-eval breakdown. Baseline 120ep from scratch: hover exploit (1000 steps pinned pad, flat-zero curve with lottery spikes to 300k); staged bonuses alone made no gradient.
- [ ] 6. Sweep throttle-bias/curriculum-length once 3–5 land; log winner to `controlworks_policy_playbook`.
