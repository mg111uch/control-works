# RESUME_POINT
- Status: Tasks 1-4 completed.
- Active Task: Task 5.
- Next Step: Implement Mid-Lane Environment & Creep AI - Mid-lane tower entities, Creep spawning system, Simple Rule-based AI for creeps.

# PROJECT: dota2_gym Development Plan
## Phase 1: Foundation & Core Movement
- [x] **Task 1: Project Skeleton & Config Engine**
    - Subtasks: Setup folder structure; Implement YAML/JSON parsers for Hero (SF) and Items; Create base ECS Registry; Implement Main Menu screen with Config toggle (FoW on/off).
    - Test: Verify config values load correctly; Verify ECS can create/destroy a basic entity.

- [x] **Task 2: Physics & Deterministic Movement**
    - Subtasks: Implement `MovementSystem` using NumPy; Simple linear interpolation for movement; Spatial Hashing for entity lookups; Right-click to move logic (Human Controller).
    - Test: Headless test verifying entity reaches target coordinates in X ticks.

## Phase 2: Networking & Combat Basics
- [x] **Task 3: Lockstep Networking Foundation**
    - Subtasks: Authoritative Server logic; Client input packet handling; State snapshot broadcasting; "Headless" mode CLI flag.
    - Test: Run server and 2 headless clients; verify state synchronization of position.

- [x] **Task 4: Basic Combat & Shadow Fiend Stats**
    - Subtasks: SF attribute logic (Str/Agi/Int); Basic Attack system (Projectile entities); Necromastery soul collection logic (on-kill trigger).
    - Test: Attack a dummy entity; verify projectile collision and HP deduction.

## Phase 3: The Lane & AI
- [ ] **Task 5: Mid-Lane Environment & Creep AI**
    - Subtasks: Mid-lane tower entities; Creep spawning system (every 30s); Simple Rule-based AI for creeps (Move to lane -> Attack nearest).
    - Test: Verify creeps spawn and move toward enemy Ancient.

- [ ] **Task 6: Shadow Fiend Abilities (QWE + R)**
    - Subtasks: Shadowraze (3 stacks) relative to hero facing; Requiem of Souls logic (souls-to-lines formula); Ability cooldown system with UI text timers.
    - Test: Cast Raze; verify AOE damage in a specific vector from hero.

## Phase 4: Economy & Items
- [ ] **Task 7: Item System & Shop (The 16 Items)**
    - Subtasks: Implement all 16 items (stats + actives); Global shop interface; Inventory management (6 slots); Gold/XP reward logic for last-hits/denies.
    - Test: Buy Blink Dagger; test active teleportation. Buy BKB; test magic immunity flag.

## Phase 5: World Expansion & Vision
- [ ] **Task 8: Full Map, Vision & Runes**
    - Subtasks: Expand map to 3 lanes; Implement static Tree blockers; Fog of War (NumPy grid mask); Power Rune spawning logic in river.
    - Test: Verify units are hidden in Fog; verify Rune pick-up applies Haste/DD buffs.

## Phase 6: Intelligence & Finalization
- [ ] **Task 9: Gymnasium Interface & Observation Space**
    - Subtasks: Implement `dota_gym_env.py` wrapper; Construct 2000-dim NumPy observation vector; Implement Hybrid Action Space (Continuous Mouse + Discrete Keys).
    - Test: Run 1000 steps of "Random Action" agent in headless mode at max speed.
- [ ] **Task 10: Win Conditions, Scoreboard & Snapshots**
    - Subtasks: Win/Loss logic (First tower falls); Final Scoreboard (KDA/CS); `save_snapshot()` and `load_snapshot()` functionality.
    - Test: Destroy tower; verify game-over state. Save game, move hero, load game, verify hero reverted to saved position.

# ARCHIVE
- **Task 1: Project Skeleton & Config Engine** (Completed)
  - Duration: 172 seconds
  - Folder structure set up with engine/model/ecs/, config/, tests/
  - ConfigLoader implemented for YAML/JSON loading
  - Base ECS EntityManager created
  - Main Menu screen with Config toggle (FoW on/off) using Pygame
  - Tests pass: config loading and ECS entity create/destroy
- **Task 2: Physics & Deterministic Movement** (Completed)
  - Duration: 1035 seconds
  - MovementSystem implemented with NumPy linear interpolation
  - SpatialHash for entity lookups
  - HumanController with right-click to move
  - PygameView for visual demo of movement
  - Tests pass: entity reaches target in ticks, state determinism
- **Task 3: Lockstep Networking Foundation** (Completed)
  - Duration: 1103 seconds
  - Authoritative Server logic with asyncio
  - Client input packet handling with binary serialization
  - State snapshot broadcasting
  - "Headless" mode CLI flag
  - Tests pass: packet serialization, server runs, client connects
- **Task 4: Basic Combat & Shadow Fiend Stats** (Completed)
  - Duration: 1618 seconds
  - SF attribute logic implemented (HP/MP calc, attack damage/range with souls)
  - Basic Attack system with projectile entities
  - Necromastery soul collection on-kill
  - Tests pass: stats calc, attack projectiles, soul collection, state determinism
