# dota2_gym
A modular 1v1 MOBA environment for Reinforcement Learning and Human Play.

## Architecture Overview
- **Pattern:** Hierarchical MVC + ECS
- **Logic:** NumPy-based vectorization
- **View:** Pygame (Geometric minimalist)
- **RL:** Gymnasium-compatible wrapper

## Quick Start
- Headless: `conda run -n myenv python -m pytest tests/`
- Ensure Conda environment is active: `conda activate myenv`
- Run the game: `python main.py` 

## Progress Log
(The agent will append details here after every successful loop iteration)
### Task 1: Project Skeleton & Config Engine - SUCCESS
- Duration: 1.0 seconds
- Project skeleton with folder structure
- YAML/JSON config parsers for heroes and items
- Base ECS registry for entity management
- Main Menu screen with Config toggle (FoW on/off) using Pygame
### Task 2: Physics & Deterministic Movement - SUCCESS
- Duration: 1035 seconds
- MovementSystem with NumPy linear interpolation
- SpatialHash for efficient entity lookups
- HumanController with right-click to move
- PygameView for visual demo of movement
### Task 3: Lockstep Networking Foundation - SUCCESS
- Duration: 1103 seconds
- Authoritative Server logic with asyncio
- Client input packet handling with binary serialization
- State snapshot broadcasting
- "Headless" mode CLI flag

### Task 4: Basic Combat & Shadow Fiend Stats - SUCCESS
- Duration: 1618 seconds
- SF attribute logic (HP/MP calc with Str/Int, attack damage/range with souls)
- Basic Attack system with projectile entities and collision
- Necromastery soul collection on-kill trigger
- Tests pass: stats verification, projectile attacks, soul collection, state determinism
## Next Tasks
- Networking Foundation
- Basic Combat & Shadow Fiend Stats