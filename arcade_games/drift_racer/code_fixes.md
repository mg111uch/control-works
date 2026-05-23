# Fixes for `train_nn.py` to Enable Reliable Basic Driving Training (Phase 1)

**Date:** February 13, 2026  
**Objective:** Modify the current genetic algorithm training script so the agent reliably learns to stay on track and drive forward consistently. Focus on survival and forward progress as fitness — ignore drifting entirely for now. Ensure training progress is visible in real-time on the terminal.

Implement fixes one at a time, test after each, and verify agent behavior improves (longer survival, more laps).

### Critical Issue Fixes (Do These First)

1. **Fix Terminal Progress Display**
   - Force immediate flushing of all print statements.
   - Add timestamp or generation counter to every progress line.
   - Print a short summary after every generation (best laps, average survival steps, off-track deaths count).
   - Add a progress line inside the evaluation loop (e.g., every 5 agents evaluated).

2. **Switch Fitness Metric from Drift Score to Driving Survival/Progress**
   - Stop using `env.score` (drift_score) as primary fitness.
   - New primary fitness: `laps_completed` (higher = better).
   - Secondary fitness: total steps survived (longer episodes = better).
   - Tertiary: negative penalty for off-track deaths (count deaths per evaluation).
   - In sorting: sort by `(laps, steps, -deaths)` descending.

3. **Enforce Off-Track = Death in Environment**
   - In `GameEnv.step()`, if off-track → immediately set `done=True` and return large negative reward (-1000).
   - Ensure reset happens on done.
   - Track number of off-track deaths during evaluation for fitness penalty.

### Exploration & Training Stability Improvements

4. **Increase Exploration During Fitness Evaluation**
   - During evaluation rollouts, use higher action noise: 30–50% chance of random action (instead of 5% epsilon).
   - This helps discover driving behaviors early; pure greedy may trap in local optima (e.g., spinning in place).
   - Keep deterministic (0% noise) only for final best model visualization.

5. **Improve Genetic Algorithm Dynamics**
   - Increase population size to 30–40 (better diversity).
   - Increase elitism to 4–5 (preserve good drivers).
   - Reduce random injection rate to 0.1–0.2 (too high kills good genes).
   - Add small Gaussian action noise during some rollouts for robustness.
   - Run more episodes per agent during evaluation (8–10 episodes per env) for stable fitness estimates.

6. **Add Forward Progress Reward in Environment (Temporary for Phase 1)**
   - Even without centerline yet, approximate progress using change in x-position or distance from start.
   - Add small positive reward per step based on speed × cos(angle error) (encourage forward motion aligned with track).
   - Combine with lap completion bonus (+1000 per lap).

### Evaluation & Safety Improvements

7. **Better Episode Management**
   - Limit max steps per episode to 3000–5000 (prevent infinite drifting in place).
   - On timeout, treat as death (negative reward).
   - Track and display average laps per agent and crash rate per generation.

8. **Early Stopping & Milestone Checks**
   - Stop early if best agent achieves 5+ consistent laps.
   - After every 20 generations, run a clean (no noise) evaluation of top 3 agents and print detailed stats.
