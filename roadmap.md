# control-works Roadmap

> Control / RL / deep-learning algorithms across games, robots, and
> simulators. Working algorithms feed PIE cognition as reusable methods
> (policies, controllers, planners) under per-subdir kernel tags.

Kernel tags: `controlworks_arcade_games` | `controlworks_dota2` |
`controlworks_oai_gym` | `controlworks_rocket` | `controlworks_tclab` |
`controlworks_theorymethods`.

## Now

- value: "integration — no algo slice selected yet"
- This leg wires docs + paths + dependency audit only. No algorithm code
  changes until the first slice is selected (candidate: oai_gym cart-pole).

---

## Backlog by subdir

### oai_gym (`controlworks_oai_gym`)

Classic control + RL playground (cart-pole variants, pendulum, FrozenLake).

- PyTorch NN control: RL training → ONNX.js conversion → realtime inference
  (needs `onnx` package — currently MISSING, see Dep audit).
- MPC cart-pole: predictive dynamics, realtime optimization.
- Multi-agent RL: second cart-pole, coordinated balancing.
- MCTS planning: realtime tree search, explore/exploit balance.
- Adaptive physics: gravity / mass / length sliders driving dynamics.
- Obstacles in swing-up control.

### rocket (`controlworks_rocket`)

- GNS (guidance, navigation, control) for rockets and missiles.
- `rocket2D.py` / `rocket3D.py`: 2D and 3D flight models.
- `lunar_lander.py`: pygame lunar-lander game env (deps installed).

### tclab (`controlworks_tclab`)

- MPC / MHE temperature-control labs (deps: `tclab`, `gekko` installed).
- `labB/C/F.py` + `lab_theory/`: controller experiments with logged runs
  (CSVs + result plots already in dir).

### theorymethods (`controlworks_theorymethods`)

Control-theory library (deps: `do_mpc`, `casadi`, `control` installed):

- LQR (`lqr1.py`), MPC (`dompc.py`, `opt_gekko.py`).
- PINN (`pinn1.py`), lane-change (`lanechg.py`), satellite (`satellite.py`).
- Supporting models: `pvtol.py`, `DualTank.py`, `msd.py`, `lvlReg.py`,
  `circuitPWM.py`.

### arcade_games (`controlworks_arcade_games`)

- `tower_defence/` + `allgames/`, `break_out/`, `drift_racer/`, `flappy_bird/`:
  game environment harness for agent play and training.
- Harnesses double as fast RL envs once Gym-wrapped.

### dota2 (`controlworks_dota2`)

Per `dota2/project_manifesto.md` — goal in 3 lines:

1. Complete modular 1v1 Shadow Fiend MOBA training env in Python:
   human-playable, Gymnasium/PettingZoo compatible, renderer-agnostic.
2. Fixed spec: 15-tick sim, vectorised NumPy + ECS, 16 items, hybrid
   action space, lockstep multiplayer + observer mode.
3. Deliverables: folder structure, working `main.py` (HvH, HvAI, headless
   self-play, server/clients), full Gym env, YAML/JSON hero+items.

---

## Deferred (not now)

- WebXR / AR rendering of envs.
- Haptic feedback (Gamepad API resistance).
- 3D tip-trajectory plots.

---

## Rules

- Small scope: ≤3 files per change; ≤500 lines per file.
- Conda env `myenv` shared with PIE; install NOTHING without user approval.
- Content-hash lineage only; SQLite/kernel writes stay inside the PIE repo,
  never in control-works.

## Dep audit (2026-09-08, `myenv`)

- cartPole.py needs gymnasium/scipy/numpy → all INSTALLED.
- lunar_lander.py needs pygame → INSTALLED (2.5.2).
- dompc.py needs do_mpc/casadi/numpy → all INSTALLED.
- Also INSTALLED: torch, gym, mujoco, gekko, tclab, control.
- MISSING: onnx (blocks ONNX.js export step only).
