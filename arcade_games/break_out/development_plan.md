# Breakout Arcade Game Development Plan

This plan outlines the iterative development of a Breakout arcade game using Pygame. The game will include both manual play and AI modes using PyTorch for reinforcement learning.

## Iterative Feature List

- [x] **Basic Pygame Window Setup**
    - Initialize Pygame
    - Create a window with fixed dimensions (e.g., 800x600)
    - Set up basic colors and a simple game loop
    - Display a title and handle quit events
    - Goal: Plain window that opens and closes properly

- [x] **Add Paddle**
    - Create a Paddle class with position, size, and movement
    - Implement left/right movement using arrow keys
    - Draw the paddle on screen
    - Add boundary checks to prevent paddle from going off-screen
    - Goal: Controllable paddle at the bottom of the screen

- [x] **Add Ball**
    - Create a Ball class with position, velocity, and radius
    - Implement basic movement and bouncing off top/bottom walls
    - Draw the ball on screen
    - Add gravity or constant speed movement
    - Goal: Ball that moves and bounces within the play area

- [x] **Ball-Paddle Collision**
    - Implement collision detection between ball and paddle
    - Adjust ball velocity based on collision point (angle reflection)
    - Add sound effect for collision (optional)
    - Handle ball going below paddle (game over condition)
    - Goal: Ball can be bounced back by the paddle

- [x] **Add Bricks**
    - Create a Brick class with position, size, and color
    - Generate a grid of bricks at the top of the screen
    - Draw bricks on screen
    - Add different brick types/colors for variety
    - Goal: Static brick layout ready for collision

- [x] **Ball-Brick Collision**
    - Implement collision detection between ball and bricks
    - Remove bricks when hit by ball
    - Adjust ball velocity on brick collision
    - Add scoring system (points per brick)
    - Add sound effects for brick destruction
    - Goal: Bricks can be destroyed, game progresses

- [x] **Game States and UI**
    - Implement game states: menu, playing, game over
    - Add start menu with manual/AI mode selection
    - Display score, lives, and game over screen
    - Add restart functionality
    - Handle win condition (all bricks cleared)
    - Goal: Complete game flow with proper state management

- [x] **Lives and Difficulty**
    - Add lives system (3 lives by default)
    - Reset ball position on life loss
    - Increase difficulty (ball speed) as bricks are cleared
    - Add level progression with different brick layouts
    - Goal: Multi-life gameplay with increasing challenge

- [x] **AI Mode Setup (PyTorch)**
    - Define state representation (ball position, velocity, paddle position, brick layout)
    - Create PolicyNet class using PyTorch.
    - Implement basic random action AI for testing
    - Add model loading from saved file (policy_model.pth)
    - Goal: AI can control the paddle using the neural network

- [x] **Training Infrastructure**
    - Create GameEnv class for reinforcement learning
    - Implement step() and reset() methods
    - Define reward system (positive for brick hits, negative for misses)
    - Add training loop with experience collection
    - Save trained model parameters
    - Goal: Framework for training AI to play Breakout

- [ ] **Advanced AI Features**
    - Implement experience replay buffer
    - Add epsilon-greedy exploration
    - Fine-tune reward shaping for better learning
    - Train model to achieve high scores
    - Goal: Competent AI that can play the game effectively

- [ ] **Polish and Extras**
    - Add particle effects for brick destruction
    - Implement power-ups (multi-ball, paddle size changes)
    - Add background music and sound effects
    - Create different themes/color schemes
    - Add high score persistence
    - Goal: Polished, engaging game experience

## Technical Considerations

- Use a modular class structure (GameEnv, Paddle, Ball, Brick classes)
- Implement normalized state features for AI training
- Implement proper collision detection and physics
- Ensure smooth 60 FPS gameplay
- Handle edge cases (ball stuck, perfect alignments)

## Testing Strategy

- Test each feature incrementally
- Verify collision detection accuracy
- Ensure AI can learn basic paddle control
- Balance difficulty for both human and AI play