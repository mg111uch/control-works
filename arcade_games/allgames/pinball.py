import pygame
import random
import sys
import time
import os

pygame.init()

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (135, 206, 235)
YELLOW = (255, 255, 0)
GREEN = (0, 128, 0)
GRAY = (128, 128, 128)
RED = (255, 0, 0)

BALL_RADIUS = 10
GRAVITY = 0.2
FRICTION = 0.99
FLIPPER_LENGTH = 60
FLIPPER_ANGLE = 30
BUMPER_RADIUS = 20

FONT = pygame.font.SysFont(None, 36)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pinball")

clock = pygame.time.Clock()

class Ball:
    def __init__(self):
        self.x = SCREEN_WIDTH // 2
        self.y = 50
        self.vx = random.uniform(-2, 2)
        self.vy = 0

    def update(self):
        self.vy += GRAVITY
        self.vx *= FRICTION
        self.vy *= FRICTION
        self.x += self.vx
        self.y += self.vy

        # Bounce off walls
        if self.x - BALL_RADIUS < 0 or self.x + BALL_RADIUS > SCREEN_WIDTH:
            self.vx = -self.vx
            self.x = max(BALL_RADIUS, min(SCREEN_WIDTH - BALL_RADIUS, self.x))

    def draw(self):
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), BALL_RADIUS)

class Flipper:
    def __init__(self, x, y, is_left):
        self.x = x
        self.y = y
        self.is_left = is_left
        self.angle = 0

    def update(self, active):
        if active:
            self.angle = FLIPPER_ANGLE if self.is_left else -FLIPPER_ANGLE
        else:
            self.angle = 0

    def draw(self):
        end_x = self.x + FLIPPER_LENGTH * (1 if self.is_left else -1)
        end_y = self.y - FLIPPER_LENGTH * 0.1
        pygame.draw.line(screen, RED, (self.x, self.y), (end_x, end_y), 5)

class Bumper:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def draw(self):
        pygame.draw.circle(screen, YELLOW, (self.x, self.y), BUMPER_RADIUS)

def collides_ball_bumper(ball, bumper):
    dx = ball.x - bumper.x
    dy = ball.y - bumper.y
    dist = (dx**2 + dy**2)**0.5
    return dist < BALL_RADIUS + BUMPER_RADIUS

def bounce_ball_bumper(ball, bumper):
    dx = ball.x - bumper.x
    dy = ball.y - bumper.y
    dist = (dx**2 + dy**2)**0.5
    if dist == 0:
        return
    nx = dx / dist
    ny = dy / dist
    ball.vx += nx * 3
    ball.vy += ny * 3

def draw_score(score):
    text = FONT.render(f"Score: {score}", True, BLACK)
    screen.blit(text, (10, 10))

def game_over_screen(score):
    screen.fill(BLUE)
    text = FONT.render("Ball Lost!", True, RED)
    screen.blit(text, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 - 50))
    score_text = FONT.render(f"Score: {score}", True, BLACK)
    screen.blit(score_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2))
    restart_text = FONT.render("Press SPACE to restart", True, BLACK)
    screen.blit(restart_text, (SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 50))
    pygame.display.flip()

def main():
    ball = Ball()
    left_flipper = Flipper(200, SCREEN_HEIGHT - 50, True)
    right_flipper = Flipper(400, SCREEN_HEIGHT - 50, False)
    bumpers = [Bumper(150, 150), Bumper(450, 150), Bumper(300, 250)]
    score = 0
    running = True
    game_over = False

    while running:
        screen.fill(BLACK)

        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and game_over:
                    ball = Ball()
                    score = 0
                    game_over = False

        if not game_over:
            left_active = keys[pygame.K_LEFT]
            right_active = keys[pygame.K_RIGHT]
            left_flipper.update(left_active)
            right_flipper.update(right_active)

            ball.update()

            for bumper in bumpers:
                if collides_ball_bumper(ball, bumper):
                    bounce_ball_bumper(ball, bumper)
                    score += 10

            # Check if ball is lost
            if ball.y > SCREEN_HEIGHT:
                game_over = True

            ball.draw()
            left_flipper.draw()
            right_flipper.draw()
            for bumper in bumpers:
                bumper.draw()
            draw_score(score)
        else:
            game_over_screen(score)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()