import pygame
import torch
import torch.nn as nn

# Initialize Pygame
pygame.init()
pygame.font.init()

# Set up colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

class Paddle:
    def __init__(self, x, y, width, height, speed=5):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.speed = speed

    def move(self, keys):
        if keys[pygame.K_LEFT] and self.x > 0:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] and self.x < SCREEN_WIDTH - self.width:
            self.x += self.speed

    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, (self.x, self.y, self.width, self.height))

class Ball:
    def __init__(self, x, y, radius, dx=5, dy=-5):
        self.x = x
        self.y = y
        self.radius = radius
        self.dx = dx
        self.dy = dy

    def move(self):
        self.x += self.dx
        self.y += self.dy
        # Bounce off top
        if self.y - self.radius <= 0:
            self.dy = -self.dy

    def draw(self, screen):
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.radius)

class Brick:
    def __init__(self, x, y, width, height, color):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.visible = True

    def draw(self, screen):
        if self.visible:
            pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))

class PolicyNet(nn.Module):
    def __init__(self, state_size=55, action_size=3):
        super(PolicyNet, self).__init__()
        self.fc1 = nn.Linear(state_size, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, action_size)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)
        return x

    def random_action(self):
        return torch.randint(0, 3, (1,)).item()

    def load_model(self, path):
        self.load_state_dict(torch.load(path))

def get_state(game):
    state = []
    # Normalize ball position and velocity
    state.append(game.ball.x / SCREEN_WIDTH)
    state.append(game.ball.y / SCREEN_HEIGHT)
    state.append(game.ball.dx / 10)  # Assume max speed 10
    state.append(game.ball.dy / 10)
    # Paddle position
    state.append(game.paddle.x / SCREEN_WIDTH)
    # Bricks visibility
    for brick in game.bricks:
        state.append(1.0 if brick.visible else 0.0)
    return torch.tensor(state, dtype=torch.float32).unsqueeze(0)

class GameEnv:
    def __init__(self):
        self.game = Game()
        self.done = False
        self.prev_score = 0

    def reset(self):
        self.game.restart()
        self.done = False
        self.prev_score = self.game.score
        return get_state(self.game)

    def step(self, action):
        # Action: 0 left, 1 stay, 2 right
        if action == 0:
            keys = {pygame.K_LEFT: True, pygame.K_RIGHT: False}
        elif action == 1:
            keys = {pygame.K_LEFT: False, pygame.K_RIGHT: False}
        elif action == 2:
            keys = {pygame.K_LEFT: False, pygame.K_RIGHT: True}
        else:
            keys = {pygame.K_LEFT: False, pygame.K_RIGHT: False}

        # Simulate one frame
        self.game.paddle.move(keys)
        self.game.ball.move()

        # Check collisions
        for brick in self.game.bricks:
            if brick.visible and (self.game.ball.x + self.game.ball.radius > brick.x and self.game.ball.x - self.game.ball.radius < brick.x + brick.width and
                                  self.game.ball.y + self.game.ball.radius > brick.y and self.game.ball.y - self.game.ball.radius < brick.y + brick.height):
                brick.visible = False
                self.game.ball.dy = -self.game.ball.dy

        if (self.game.ball.x > self.game.paddle.x and self.game.ball.x < self.game.paddle.x + self.game.paddle.width and
            self.game.ball.y + self.game.ball.radius >= self.game.paddle.y and self.game.ball.y - self.game.ball.radius <= self.game.paddle.y + self.game.paddle.height):
            self.game.ball.dy = -self.game.ball.dy

        if self.game.ball.y - self.game.ball.radius > SCREEN_HEIGHT:
            self.game.lives -= 1
            if self.game.lives == 0:
                self.done = True
            else:
                self.game.ball.x = SCREEN_WIDTH // 2
                self.game.ball.y = SCREEN_HEIGHT // 2
                self.game.ball.dx = 5
                self.game.ball.dy = -5

        if all(not brick.visible for brick in self.game.bricks):
            self.done = True

        reward = self.game.score - self.prev_score
        self.prev_score = self.game.score

        next_state = get_state(self.game)
        return next_state, reward, self.done

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Breakout")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36)
        self.state = 'menu'
        self.lives = 3
        self.score = 0
        self.level = 1
        self.last_cleared = 0
        self.paddle = Paddle(SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 30, 100, 10)
        self.ball = Ball(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, 10)
        self.bricks = []
        self.create_bricks()

    def create_bricks(self):
        self.bricks = []
        rows = 5 + self.level - 1  # Increase rows with level
        cols = 10
        brick_width = 80
        brick_height = 30
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)]
        for row in range(rows):
            for col in range(cols):
                x = col * brick_width
                y = row * brick_height
                color = colors[row % len(colors)]
                self.bricks.append(Brick(x, y, brick_width, brick_height, color))

    def start_game(self):
        self.state = 'playing'

    def check_win(self):
        if all(not brick.visible for brick in self.bricks):
            self.level += 1
            self.create_bricks()
            self.ball.x = SCREEN_WIDTH // 2
            self.ball.y = SCREEN_HEIGHT // 2
            self.ball.dx = 5 + self.level
            self.ball.dy = - (5 + self.level)
            self.paddle.x = SCREEN_WIDTH // 2 - 50
            # Continue playing

    def check_game_over(self):
        if self.lives == 0:
            self.state = 'game_over'

    def restart(self):
        self.state = 'playing'
        self.score = 0
        self.lives = 3
        self.level = 1
        self.last_cleared = 0
        self.ball.x = SCREEN_WIDTH // 2
        self.ball.y = SCREEN_HEIGHT // 2
        self.ball.dx = 5
        self.ball.dy = -5
        self.paddle.x = SCREEN_WIDTH // 2 - 50
        self.create_bricks()

    def update(self):
        if self.state == 'playing':
            keys = pygame.key.get_pressed()
            self.paddle.move(keys)
            self.ball.move()

            # Check ball-brick collisions
            for brick in self.bricks:
                if brick.visible and (self.ball.x + self.ball.radius > brick.x and self.ball.x - self.ball.radius < brick.x + brick.width and
                                      self.ball.y + self.ball.radius > brick.y and self.ball.y - self.ball.radius < brick.y + brick.height):
                    brick.visible = False
                    self.ball.dy = -self.ball.dy
                    self.score += 10

            # Increase difficulty based on cleared bricks
            cleared = sum(1 for b in self.bricks if not b.visible)
            if cleared > self.last_cleared and cleared % 20 == 0:
                self.ball.dx *= 1.1
                self.ball.dy *= 1.1
                self.last_cleared = cleared

            # Check ball-paddle collision
            if (self.ball.x > self.paddle.x and self.ball.x < self.paddle.x + self.paddle.width and
                self.ball.y + self.ball.radius >= self.paddle.y and self.ball.y - self.ball.radius <= self.paddle.y + self.paddle.height):
                self.ball.dy = -self.ball.dy

            # Check game over
            if self.ball.y - self.ball.radius > SCREEN_HEIGHT:
                self.lives -= 1
                if self.lives == 0:
                    self.state = 'game_over'
                else:
                    # Reset ball
                    self.ball.x = SCREEN_WIDTH // 2
                    self.ball.y = SCREEN_HEIGHT // 2
                    self.ball.dx = 5
                    self.ball.dy = -5

            self.check_win()

    def draw(self):
        self.screen.fill(BLACK)

        if self.state == 'menu':
            text = self.font.render("Press SPACE to Start", True, WHITE)
            self.screen.blit(text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))
        elif self.state == 'playing':
            self.paddle.draw(self.screen)
            self.ball.draw(self.screen)
            for brick in self.bricks:
                brick.draw(self.screen)
            score_text = self.font.render(f"Score: {self.score}", True, WHITE)
            self.screen.blit(score_text, (10, 10))
            lives_text = self.font.render(f"Lives: {self.lives}", True, WHITE)
            self.screen.blit(lives_text, (10, 50))
            level_text = self.font.render(f"Level: {self.level}", True, WHITE)
            self.screen.blit(level_text, (10, 90))
        elif self.state == 'game_over':
            text = self.font.render("Game Over! Press R to Restart", True, WHITE)
            self.screen.blit(text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2))
        elif self.state == 'win':
            text = self.font.render("You Win! Press R to Restart", True, WHITE)
            self.screen.blit(text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2))

        pygame.display.flip()

# Create window
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
game = Game()

# Game loop
running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if game.state == 'menu' and event.key == pygame.K_SPACE:
                game.start_game()
            elif game.state in ['game_over', 'win'] and event.key == pygame.K_r:
                game.restart()

    game.update()
    game.draw()

    # Cap frame rate
    game.clock.tick(60)

# Quit Pygame
pygame.quit()