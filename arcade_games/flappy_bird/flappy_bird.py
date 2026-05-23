import pygame
import random
import sys
import os

# Usage: python flappy_bird.py
# The game will prompt for manual or AI play mode.

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (135, 206, 235)
YELLOW = (255, 255, 0)
GREEN = (0, 128, 0)

# Bird properties
BIRD_WIDTH = 30
BIRD_HEIGHT = 30
BIRD_X = 50
BIRD_Y = SCREEN_HEIGHT // 2
BIRD_VEL = 0
# Best manually playable gravity 0.3
GRAVITY = 0.3  # Very low gravity for easier control
# Best manually playable strength -5
FLAP_STRENGTH = -5  # Very strong flap

# Pipe properties
PIPE_WIDTH = 60
PIPE_GAP = 180  # Larger gap for easier learning
PIPE_SPEED = 2  # Slower pipe speed for easier learning

# Font
FONT = pygame.font.SysFont(None, 36)

# Screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Flappy Bird Clone")

clock = pygame.time.Clock()

class Bird:
    def __init__(self):
        self.x = BIRD_X
        self.y = BIRD_Y
        self.vel = BIRD_VEL

    def flap(self):
        self.vel = FLAP_STRENGTH

    def update(self):
        self.vel += GRAVITY
        self.y += self.vel

    def draw(self):
        pygame.draw.rect(screen, YELLOW, (self.x, self.y, BIRD_WIDTH, BIRD_HEIGHT))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, BIRD_WIDTH, BIRD_HEIGHT)

class Pipe:
    def __init__(self, x):
        self.x = x
        self.height = random.randint(50, SCREEN_HEIGHT - PIPE_GAP - 50)
        self.top_rect = pygame.Rect(self.x, 0, PIPE_WIDTH, self.height)
        self.bottom_rect = pygame.Rect(self.x, self.height + PIPE_GAP, PIPE_WIDTH, SCREEN_HEIGHT - self.height - PIPE_GAP)
        self.passed = False

    def update(self):
        self.x -= PIPE_SPEED
        self.top_rect.x = self.x
        self.bottom_rect.x = self.x

    def draw(self):
        pygame.draw.rect(screen, GREEN, self.top_rect)
        pygame.draw.rect(screen, GREEN, self.bottom_rect)

class GameEnv:
    def __init__(self):
        self.reset()

    def reset(self):
        self.bird = Bird()
        self.pipes = []
        self.score = 0
        self.done = False
        return self.get_state()

    def get_state(self):
        # Find the next pipe that hasn't been passed yet
        next_pipe = None
        for pipe in self.pipes:
            if pipe.x + PIPE_WIDTH > self.bird.x:  # Pipe is still ahead of bird
                next_pipe = pipe
                break
        
        if next_pipe:
            pipe_x = next_pipe.x
            pipe_h = next_pipe.height
            gap_center = next_pipe.height + PIPE_GAP / 2
        else:
            pipe_x = SCREEN_WIDTH
            pipe_h = SCREEN_HEIGHT // 2
            gap_center = SCREEN_HEIGHT / 2
        
        # Better normalized state features:
        # 1. Bird's vertical position (0 to 1)
        # 2. Bird's velocity normalized (typically -7 to +6 range, normalize to ~-1 to 1)
        # 3. Horizontal distance to next pipe (0 to 1)
        # 4. Vertical distance to gap center (normalized, can be negative)
        bird_y_norm = self.bird.y / SCREEN_HEIGHT
        bird_vel_norm = self.bird.vel / 7.0  # Adjust normalization for new gravity
        pipe_dist_norm = (pipe_x - self.bird.x) / SCREEN_WIDTH
        gap_dist_norm = (self.bird.y - gap_center) / SCREEN_HEIGHT  # Negative = above gap, Positive = below gap
        
        return [bird_y_norm, bird_vel_norm, pipe_dist_norm, gap_dist_norm]

    def step(self, action):
        reward = 0.1  # Small base survival reward
        
        if action == 1:
            self.bird.flap()
        self.bird.update()

        if len(self.pipes) == 0 or self.pipes[-1].x < SCREEN_WIDTH - 300:
            self.pipes.append(Pipe(SCREEN_WIDTH))

        for pipe in self.pipes[:]:
            pipe.update()
            if pipe.x + PIPE_WIDTH < 0:
                self.pipes.remove(pipe)

        bird_rect = self.bird.get_rect()
        
        # Check for death conditions
        died = False
        if self.bird.y < 0 or self.bird.y + BIRD_HEIGHT > SCREEN_HEIGHT:
            self.done = True
            died = True
            reward = -1.0  # Strong penalty for dying
            
        for pipe in self.pipes:
            if bird_rect.colliderect(pipe.top_rect) or bird_rect.colliderect(pipe.bottom_rect):
                self.done = True
                died = True
                reward = -1.0

        # Score for passing pipes
        for pipe in self.pipes:
            if not pipe.passed and pipe.x + PIPE_WIDTH < self.bird.x:
                pipe.passed = True
                self.score += 1
                reward += 20.0  # Large reward for passing pipe

        # Reward shaping (only if not dead)
        if not died:
            # Find next pipe (one that hasn't been passed)
            next_pipe = None
            for pipe in self.pipes:
                if pipe.x + PIPE_WIDTH > self.bird.x:
                    next_pipe = pipe
                    break
            
            if next_pipe:
                gap_center = next_pipe.height + PIPE_GAP / 2
            else:
                gap_center = SCREEN_HEIGHT / 2
            
            # Reward for vertical positioning relative to gap center
            # This is the KEY reward for learning to hover at the right height
            bird_center = self.bird.y + BIRD_HEIGHT / 2
            vertical_distance = abs(bird_center - gap_center)
            max_dist = SCREEN_HEIGHT / 2
            
            # Normalized vertical reward: 1.0 when perfectly centered, 0 when at edge
            vertical_reward = max(0, 1.0 - (vertical_distance / max_dist))
            reward += vertical_reward * 0.5  # Up to 0.5 reward for being centered
            
            # Reward for staying in safe vertical zone (not too close to edges)
            margin = 50  # pixels from edge
            if self.bird.y > margin and self.bird.y + BIRD_HEIGHT < SCREEN_HEIGHT - margin:
                reward += 0.2  # Bonus for staying in safe zone
            
            # Small reward for controlled velocity (not falling/rising too fast)
            if abs(self.bird.vel) < 5:
                reward += 0.1  # Reward for controlled movement

        return self.get_state(), reward, self.done

def draw_score(score):
    text = FONT.render(f"Score: {score}", True, BLACK)
    screen.blit(text, (10, 10))

def get_state(bird, pipes):
    # Find the next pipe that hasn't been passed yet
    next_pipe = None
    for pipe in pipes:
        if pipe.x + PIPE_WIDTH > bird.x:  # Pipe is still ahead of bird
            next_pipe = pipe
            break
    
    if next_pipe:
        pipe_x = next_pipe.x
        gap_center = next_pipe.height + PIPE_GAP / 2
    else:
        pipe_x = SCREEN_WIDTH
        gap_center = SCREEN_HEIGHT / 2
    
    # Better normalized state features:
    bird_y_norm = bird.y / SCREEN_HEIGHT
    bird_vel_norm = bird.vel / 7.0  # Adjust normalization for new gravity
    pipe_dist_norm = (pipe_x - bird.x) / SCREEN_WIDTH
    gap_dist_norm = (bird.y - gap_center) / SCREEN_HEIGHT
    
    return [bird_y_norm, bird_vel_norm, pipe_dist_norm, gap_dist_norm]

def game_over_screen(score):
    screen.fill(BLUE)
    text = FONT.render("Game Over", True, BLACK)
    screen.blit(text, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 - 50))
    score_text = FONT.render(f"Score: {score}", True, BLACK)
    screen.blit(score_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2))
    restart_text = FONT.render("Press UP ARROW to restart", True, BLACK)
    screen.blit(restart_text, (SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 + 50))
    pygame.display.flip()

def show_menu():
    screen.fill(BLUE)
    title = FONT.render("Flappy Bird", True, BLACK)
    screen.blit(title, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 - 100))
    manual_text = FONT.render("Press M for Manual Play", True, BLACK)
    screen.blit(manual_text, (SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 - 50))
    ai_text = FONT.render("Press A for AI Play", True, BLACK)
    screen.blit(ai_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))
    pygame.display.flip()

def main():
    ai_mode = False
    model = None

    show_menu()
    menu_running = True
    while menu_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    ai_mode = False
                    menu_running = False
                elif event.key == pygame.K_a:
                    model_path = 'flappy_bird.pth'
                    if os.path.exists(model_path):
                        import torch
                        import torch.nn as nn
                        class PolicyNet(nn.Module):
                            def __init__(self):
                                super(PolicyNet, self).__init__()
                                self.fc1 = nn.Linear(4, 64)
                                self.fc2 = nn.Linear(64, 32)
                                self.fc3 = nn.Linear(32, 2)
                            def forward(self, x):
                                x = torch.relu(self.fc1(x))
                                x = torch.relu(self.fc2(x))
                                x = self.fc3(x)
                                return x
                        model = PolicyNet()
                        model.load_state_dict(torch.load(model_path))
                        model.eval()
                        ai_mode = True
                        menu_running = False
                    else:
                        error_text = FONT.render("No trained model found!", True, BLACK)
                        screen.blit(error_text, (SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 + 50))
                        pygame.display.flip()
                        pygame.time.wait(2000)
                        show_menu()

    bird = Bird()
    pipes = []
    score = 0
    running = True
    game_over = False

    while running:
        screen.fill(BLUE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    if game_over:
                        # Restart
                        bird = Bird()
                        pipes = []
                        score = 0
                        game_over = False
                    else:
                        if not ai_mode:
                            bird.flap()

        if not game_over:
            if ai_mode:
                s = get_state(bird, pipes)
                state_tensor = torch.tensor(s, dtype=torch.float32)
                logits = model(state_tensor)
                probs = torch.softmax(logits, dim=0)
                action = 1 if probs[1] > 0.5 else 0
                if action == 1:
                    bird.flap()
            bird.update()

            # Add pipes
            if len(pipes) == 0 or pipes[-1].x < SCREEN_WIDTH - 300:
                pipes.append(Pipe(SCREEN_WIDTH))

            # Update pipes
            for pipe in pipes[:]:
                pipe.update()
                if pipe.x + PIPE_WIDTH < 0:
                    pipes.remove(pipe)

            # Check collisions
            bird_rect = bird.get_rect()
            if bird.y < 0 or bird.y + BIRD_HEIGHT > SCREEN_HEIGHT:
                game_over = True
            for pipe in pipes:
                if bird_rect.colliderect(pipe.top_rect) or bird_rect.colliderect(pipe.bottom_rect):
                    game_over = True

            # Check score
            for pipe in pipes:
                if not pipe.passed and pipe.x + PIPE_WIDTH < bird.x:
                    pipe.passed = True
                    score += 1

            # Draw
            bird.draw()
            for pipe in pipes:
                pipe.draw()
            draw_score(score)

        else:
            game_over_screen(score)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()