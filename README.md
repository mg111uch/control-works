**Solvers:** 
Equation,Snake cube, Minesweeper, 
Free cell, Go, 
Hidoku, Jodici, Kakuro, Klotski, Latin squares, 
Lights out, MagicCube, MagicHyperCube, 
Magic square, Magic number, Magic Triangle, 
Nonogram, Pentomino, Connect four

**Arcade:**   Mario, Super Contra,  Mappy,  
Goonies,  City connect, Bomber man, Base ball
Alladin, Donkey Kong, Excide bike, Batman, Soccer,
Binary land, Circus, Dr Mario, Othello, Gradius, 
Life force, NFS, Somari, Tennis, Tiny toon, 
Battle city , Ice climber, Checker board

3D Maze navigation Webot Bug Algo
Self driving Car
Robot arm control
Bipedal Walker
Acrobot agent
Spider robot walking on uneven terrain
Humanoid runner on track with obstacles
Drone navigation in 3D avoiding obstacles
Cheetah running agent
Robot arm Block stacking
FiFa playing agent
Pvtol agent
Rocket and missile GNS
Satellite altitude control

## Agent Instructions (policy research: drift_racer, dota2, rocket)

1. Orient: read `roadmap.md` (`Now` marker) + kernel topic
   `controlworks_policy_playbook` (6 transferable lessons) before touching code.
2. Per-subdir tags: `controlworks_arcade_games` | `controlworks_dota2` |
   `controlworks_rocket`. Playbook topic is sim-agnostic; subdir topics hold evidence.
3. Mandatory verify: claim results only from deterministic eval
   (noise 0, fixed seed) + trajectory log with positions and crash summary.
   Never rank or report on noisy-rollout fitness.
4. Anti-pattern checklist: action-space parity, clean-eval selection,
   diversity pressure, activity-before-survival gate, failure penalty >
   max bonus, CI-safe entry (no prompts, anchored paths, seed flags).
5. Close the loop: log decisions + corrections (not just wins) to the
   subdir kernel topic; superseded claims get a correction node, never silent edits.
6. Small scope: <=3 files per change; shared `myenv`; no installs without approval.

**Todos:**
- Integrate PyTorch Neural Network Control.Involves RL training, model conversion via ONNX.js, and real-time inference.
- Add obstacles in swing up control.
- Implement an MPC controller to optimize cart movement using predictive dynamics. Requires solving optimization problems in real-time.
- Multi-Agent RL Interaction. Add a second cart-pole system, with both carts coordinating to balance their poles.
- Use WebXR to render the CartPole in Augmented Reality (AR) Mode, viewable on mobile devices.
- Plot the pole’s tip trajectory as a 3D curve, updating dynamically.
- Adaptive Physics Parameters.Allow users to adjust gravity, pole mass, or length via sliders, affecting Cannon.js dynamics.
- Add haptic feedback (via Gamepad API) when dragging the cart, simulating resistance.
- Tree search in real-time. Implement Monte Carlo Tree Search (MCTS) to plan cart actions, balancing exploration and exploitation.

