# Drift Racer 2D

A racing game with drifting mechanics, refactored into MVC architecture.

## Quick Start

```bash
cd python/control/arcade_games/drift_racer
conda run -n myenv python main.py
```

## Game Commands

### Run Game
```bash
# Default track
python main.py
# Specific track                    
python main.py --track simple_oval       
# List available tracks
python main.py --list-tracks      
```

### Manual play (run from codebase/, needs display)
```bash
# Any shipped track
conda run -n myenv python main.py --track infinity_loop
# Generated holdout track (listed as proc_99)
conda run -n myenv python main.py --track holdout_99
# Fresh random single-loop track, then play it
conda run -n myenv python training/gen_track.py --seed 42 --lobes 1 --out tracks/proc_42.json
conda run -n myenv python main.py --track proc_42
# Or skip files entirely — new procedural layout every launch:
conda run -n myenv python main.py --random-track
conda run -n myenv python main.py --random-track --shape spline --seed 7
# Shape families: ellipse | rect | stadium | spline (default: random mix)
conda run -n myenv python training/gen_track.py --seed 50 --shape rect --out tracks/rect_50.json
conda run -n myenv python training/gen_track.py --seed 60 --shape spline --out tracks/spline_60.json
# --reverse forces clockwise; otherwise 30% of layouts are reversed.
# Note: laps are sequence-gated — pass all checkpoint boxes in order.
```

### Run Training

> **Agents: never start a training run (`train_nn.py` without `--eval-only`/`--visualize`) without the user's explicit permission.** Training is slow (25+ min/generation multi-track), burns CPU, and a fresh/seeded run can overwrite saved weights. Eval (`--eval-only`), visualization (`--visualize`), and trajectory plots are always allowed. If a run is needed, propose the exact command first and wait for approval.
```bash
# Headless training (default, fast)
python train_nn.py 
# With visualization               
python train_nn.py --headless=False 
# Visualize trained model (exact — both flags required, run from codebase/)
cd codebase && conda run -n myenv python training/train_nn.py --headless=False --visualize --viz-seconds 20
# NOTE: omitting --headless=False runs the loop with no visible window.
# Other track (default: simple_oval):
cd codebase && conda run -n myenv python training/train_nn.py --headless=False --visualize --track infinity_loop --viz-seconds 20
# Trajectory plot (car locations over track, for inspection — run from codebase/)
conda run -n myenv python training/train_nn.py --eval-only --eval-laps 1 --track infinity_loop --traj-out /tmp/opencode/inf.csv
conda run -n myenv python training/plot_traj.py /tmp/opencode/inf.csv tracks/infinity_loop.json /tmp/opencode/traj_inf.png
# o = spawn, x = episode end; legend shows laps per episode. --eval-laps caps each episode at N laps.
# Use 8 parallel environments    
python train_nn.py --num_envs 8
```

### Phase-3: generalist training (run from codebase — needs user approval first, see guardrail above)
```bash
# Detached launch with live log (use for ANY approved run, writes training/models/):
LOG=/tmp/opencode/p3.log ./training/run_train.sh --fresh --generations 30 \
  --proc-tracks 2 --proc-seed 11
tail -f /tmp/opencode/p3.log   # follow; run_train.sh refuses if one is already up
# Cheap validation smoke (isolated dir, ~2 min, never touches real weights):
LOG=/tmp/opencode/smoke.log ./training/run_train.sh --pop-size 4 --episodes 1 \
  --generations 1 --fresh --model-dir /tmp/opencode/smoke --proc-tracks 0 --tracks simple_oval
# Pool = --track + procedural seeds (default proc 11,12, generated into tracks/).
# infinity_loop is NEVER in training pools (not single-loop) — use --tracks a,b to override.
# Eval the canonical model on any track (incl. holdout, never trained on):
conda run -n myenv python training/train_nn.py --eval-only --eval-laps 1 \
  --track holdout_99 --traj-out /tmp/opencode/hold.csv
# Canonical weights: training/models/drift_policy_model{,_best}.pth (--model-dir overrides, legacy training/, phase3/, codebase/ copies are read-only fallback).
```

### Run Tests
```bash
# From the parent directory (Hello):
cd /home/manigupt/Hello/python/control/arcade_games/drift_racer/codebase 
conda run -n myenv python -m pytest tests/ -v
```

## Game Controls

| Key | Action |
|-----|--------|
| UP | Accelerate |
| DOWN | Brake |
| LEFT | Turn left |
| RIGHT | Turn right |
| SPACE | Drift |
| R | Restart game |

## Actions (AI Training)

| Code | Action |
|------|--------|
| 0 | No action |
| 1 | Accelerate |
| 2 | Turn left |
| 3 | Turn right |
| 4 | Drift |
| 5 | Accelerate + Turn left |
| 6 | Accelerate + Turn right |
| 7 | Brake |
| 8 | Engine brake |

## AI Training Features

### Observation Space (15 dimensions)
- **Car State (5)**: x, y, angle, speed, drift_angle (all normalized 0-1)
- **Ray Distances (10)**: Distances to track boundaries in 10 directions

### Reward System
The AI agent learns through a shaped reward function:

| Component | Formula | Purpose |
|-----------|---------|---------|
| Forward Progress | `delta_distance × 10.0` | Primary reward - encourages forward movement |
| Living Penalty | `-0.1` per step | Encourages speed and efficiency |
| Drift Reward | `sin(drift_angle) × speed² × 0.5 × combo` | Rewards controlled drifting |
| Lap Bonus | `+750` | Completing a lap |
| Off-Track Penalty | `-1000` + episode end | Discourages leaving the track |

### Combo Multiplier System
- Grows with consecutive drift ticks (max 5x)
- Resets when not drifting or braking
- Multiplies drift reward for sustained drifting

### Drift Detection
- Drift angle = angle between velocity vector and car heading
- Minimum drift angle threshold: 10 degrees
- Real-time calculation during gameplay

### Vectorized Training
- Multiple parallel environments for faster training
- Configurable via `--num_envs` parameter
- Averages results across environments for stable learning

## Findings (phase-2, 2026-09-09/10)

- Deterministic eval (`--eval-only --eval-episodes 3 --eval-noise 0.0`): 8 laps x 3 eps, bit-identical trajectories. Car covers full track.
- `car.drift_angle` corrupts mid-episode: `car.angle` never wraps (hits ~2949 deg), single-wrap normalize in `models/car.py:_calculate_drift_angle` then yields negative values (e.g. -2566 deg). Affects training `drift_steps`, combo economics, gen-log `drift=`. Fix: wrap heading (`angle % 360`) before diff.
- Visual check 2026-09-10: car visibly drifts on autoplay. Naïve CSV drift% (~99.7%) is an artifact of the bug above — do not trust until fixed.
- `--track` added to `train_nn.py` (train/eval/visualize; invalid name lists available).
- `infinity_loop.json` spawn was inside the infield hole (200,200 = hole center → instant off-track death). Fixed to (115,200), mid-asphalt mirroring oval geometry. Post-fix: oval policy survives, 1 lap in 458 steps, then dies — policy gap remains, track is now valid.

## Findings (phase-3 generalist, 2026-09-10)

- Observation is now egocentric (`car.get_state(next_cp)`): speed, drift, sin/cos bearing + dist to next checkpoint, 10 rays. Absolute x/y/heading removed — old `.pth` weights are incompatible (fresh training into `training/phase3/`, never overwrite phase-2).
- Laps are sequence-gated: all required boxes in order + line cross. Checkpoint boxes re-authored onto the driving line in travel order on both tracks (old edge boxes were unreachable from the fast inner line). `+50` per new box (`CP_BONUS`).
- `training/gen_track.py`: procedural closed loops (1–2 lobes) with rejection rules (spawn/lens/boxes on asphalt). Validity tests in `tests/test_gen_track.py`.
- Multi-track GA: one pool track per env, rank key adds `min_laps` (worst-track pressure). Holdout `tracks/holdout_99.json` (seed 99, never in pool) for transfer checks.
- Track variability (single-loop only): eccentric holes (varying width/pinches), reverse layouts, 4/6-box variants; shape families ellipse/rect-ring/stadium/spline-polygon (`--shape`, default random mix); rotated elements (`angle` in collision + renderer, pixel-verified 99.9%). New shapes need no obs/reward changes (egocentric state + sampling-based rays).
- Perf: polygon tracks rasterize collision to a 2px grid at load (~0.4s once) + bbox early-reject everywhere — spline steps now match oval speed (~1ms).
- Phase-3 pilot (2 gens, fresh, pool = oval + proc_11 spline, 25.5 min): best laps=0.0/minlap=0.0/steps=146/deaths=12/drift=0.91 — a spinner exploiting the unwrapped-angle drift metric, not a driver. Traj: follows checkpoint bearing up the left side, cuts into the hole at top-right (dies step ~175). Next: fix drift_angle wrap (car.py) so fitness stops rewarding spins, then full run. Timing: ~11–14 min/gen early, grows with survival.

## Findings (phase-4 optimization + curriculum, 2026-09-11)

- **Paths canonical**: weights only in `codebase/training/models/` (`MODEL_DIR` abspath, legacy fallback); proc layouts generate into `codebase/tracks/` (loader-visible); `plot_traj.py` handles polygon tracks. `module.json` onboarded (topic `controlworks_arcade_games`, task/commands/gates for the research loop).
- **Reward/selection fixes** (`models/game_state.py`, `training/train_nn.py:_fit_key`): drift_angle wrapped to [0,180]; off-track death forfeits accrued drift gains (suicide +5k vs −1k fixed); rank now `(laps,min_laps,reward,dist,steps,-deaths,drift,unique,entropy)` after a survival-first key crowned a parker (100% action 0); 600-tick no-checkpoint stagnation kill (laps reset too), counted as death.
- **Speed** (`run_train.sh`, `train_nn.py`, `utils/ray_caster.py`, `models/track.py`): `--no-capture-output` live logs; `--workers` process pool over agents (default cpu−1, per-(gen,agent) seeds); numpy batch collision, bit-identical, 3.11→1.02ms/call; honest exact-substep TPS. 1-gen: ~14 → ~5 min.
- **6-gen curriculum run** (43 min, oval-only throughout — mastery 3.0 never hit, no expansion): gen1 mover → gen2 slider → **gen3 breakthrough 2-lap oval driver** (uniq 4, ent 1.07) → gens4–6 champ frozen, avg laps 0.06→0.09. Canonical best: oval 2 laps/2525 steps; proc_11 unseen (stagnates 693). Full run still deferred.
- Kernel: 13 nodes in `controlworks_arcade_games` + 5 playbook lessons (`controlworks_policy_playbook`).

## Findings (phase-5 curriculum expansion, 2026-09-12)

- **Gen7 single** (482s, detached `training/logs/curric_gen7.log`): best clean 2.0 laps, avg 0.09; noisy rollout (35×10×4 eps) ≈93% of wall time, clean-eval + breed/save negligible — confirmed bottleneck for estimates.
- **Gens 8–12** (34.6m total, ~6.9min/gen, `training/logs/curric12.log`): **gen8 breakthrough 4.0 laps → CURRICULUM EXPANDED** to `[simple_oval,proc_11,proc_12]`; gens 9–12 best 2.0/2.0/4.0/3.0 but `minlap 0.0` throughout (still dies on a pool track).
- **Transfer check** (new 4-lap champ): oval 1 lap/515 steps (much faster than gen-7's ~1260/lap) but proc_11 dies step 161 off-track, holdout_99 dies step 159 — faster oval line, harder overfit; diversity collapsing (uniq 3→1, ent 0.49).
- Kernel: gens 8–12 node logged on `controlworks_arcade_games`; false contradiction blocks on same-topic follow-ups traced to the kernel similarity gate and fixed (opposition-required, referent scoping, pop-topic verdict guard).

## Next (resume here)

1. **Curric24 completed** (2026-09-13, 39.1m, gens 21-24): Gen21 4.0 / Gen22 **4.5** peak / Gen23 4.0 / Gen24 4.0 laps, **minlap 0.0 all 24 gens** (honest minlap, `_fit_key` min_laps-first, wall-braking fixes did not create generalist). Deterministic eval (`--eval-laps 1`, noise 0): simple_oval 1/1 (590 steps), proc_11 1/1 (616 steps) pass; **proc_12 0/1 (68 steps off-track 140,126)** and holdout_99 0/1 (804 steps stagnation 281,198) fail. Gates `min_laps 1 / max_deaths 0` still failing. Logs: `training/logs/curric24.log`, trajectories `training/logs/curric24_{track}.csv`.
2. **Restructure trigger**: minlap flat 0 after 8+ gens → per early note, next is not more generations but architecture: **per-track breeding pools** (3 subpopulations) or **frozen-trunk warm-start** (freeze oval trunk, train head for proc_12). Also audit proc_12 geometry (spline pinch causing 68-step death).
3. Transfer eval remains baseline for any new candidate — same 4-track matrix + `plot_traj.py`.

