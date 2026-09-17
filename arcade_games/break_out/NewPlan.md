## Task: Build a Minimal Breakout Game

Build a complete, runnable **Breakout/Arkanoid game** from scratch using **Python + Pygame**. Follow the architecture and file specification exactly; do not redesign the architecture.

### Project structure

Create:

```text
breakout/
├── main.py
├── game.py
├── entities.py
├── config.py
├── collision.py
├── renderer.py
├── input.py
├── tests/
│   ├── test_collision.py
│   ├── test_entities.py
│   └── test_game.py
└── README.md
```

### Architecture

* `config.py`: screen dimensions, FPS, colors, paddle/ball/brick constants.
* `entities.py`: `Paddle`, `Ball`, and `Brick` classes; state and movement only.
* `collision.py`: pure collision/detection functions; no rendering or Pygame event handling.
* `input.py`: keyboard input abstraction.
* `renderer.py`: all drawing/rendering.
* `game.py`: `Game` class, game state, update loop, scoring, lives, level completion and reset logic.
* `main.py`: minimal application entry point and Pygame loop.
* `tests/`: automated tests for collision, entity behavior and core game state.
* `README.md`: installation, execution and controls.

### Game requirements

Implement:

* 800×600 window
* paddle controlled by Left/Right arrows
* bouncing ball
* rectangular brick grid
* ball/brick collision destroys brick and increases score
* ball/paddle collision
* wall bouncing
* 3 lives
* losing the ball costs one life
* game-over state
* win state when all bricks are destroyed
* `R` restarts after win/game-over
* score display
* clean separation between game logic and rendering

### Verification requirement

After implementation:

1. Run the automated tests.
2. Run the game.
3. Inspect/fix any runtime errors or behavioral bugs discovered.
4. Run the tests again.
5. Verify the final project structure and README.
6. Do not stop until the project is runnable and tests pass.

Use the filesystem and execution tools extensively. Work autonomously and iterate until verification succeeds.
