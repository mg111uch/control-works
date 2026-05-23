## Project overview
- Breakout game script is breakout.py
- train_nn.py script trains a neural network to play the game.
- Use Genetic Algorithm (GA).
- Population size: 20, Generations: 50 (Total 1000 episodes).
- Used simple additive Gaussian mutation (std=0.02) on model weights.
- Sorting agents primarily by Game Score, secondarily by Total Reward.

## System instruction Rules
- Do not change the game physics to fit the training.
- Training episodes should be limited to 1000.
- Add the approaches tried and their test status in the methods_tried.md file after testing the method and approach that failed. Keep the format consistent.

## Current Project State
- Basic Pygame Window Setup: Implemented. The game now has a basic 800x600 window with a game loop that handles quit events and runs at 60 FPS.
- Add Paddle: Implemented. Paddle class added with position, size, movement via arrow keys, boundary checks, and drawing on screen.
- Add Ball: Implemented. Ball class added with position, velocity, radius, movement, bouncing off top/bottom walls, and drawing on screen.
- Ball-Paddle Collision: Implemented. Collision detection between ball and paddle, velocity adjustment on collision, game over when ball goes below paddle.
- Add Bricks: Implemented. Brick class added with position, size, color, grid generation at top of screen, and drawing.
- Ball-Brick Collision: Implemented. Collision detection between ball and bricks, brick removal on hit, ball velocity adjustment, scoring system.
- Game States and UI: Implemented. Game states (menu, playing, game over, win), UI for score and lives, restart functionality, win condition.
- Lives and Difficulty: Implemented. Lives system with reset on loss, difficulty increase (ball speed) as bricks are cleared, level progression with more rows.
- AI Mode Setup (PyTorch): Implemented. State representation (ball pos/vel, paddle pos, brick layout), PolicyNet class with PyTorch NN, random action AI, model loading from policy_model.pth.
- Training Infrastructure: Implemented. GameEnv class with step() and reset() methods, reward system (positive for brick hits, negative for misses), framework for training AI.

