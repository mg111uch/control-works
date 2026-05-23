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

PADDLE_WIDTH = 10
PADDLE_HEIGHT = 60
BALL_SIZE = 10
PADDLE_SPEED = 5
BALL_SPEED = 3

FONT = pygame.font.SysFont(None, 36)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pong")

clock = pygame.time.Clock()

class Paddle:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def move_up(self):
        self.y -= PADDLE_SPEED
        if self.y < 0:
            self.y = 0

    def move_down(self):
        self.y += PADDLE_SPEED
        if self.y + PADDLE_HEIGHT > SCREEN_HEIGHT:
            self.y = SCREEN_HEIGHT - PADDLE_HEIGHT

    def draw(self):
        pygame.draw.rect(screen, WHITE, (self.x, self.y, PADDLE_WIDTH, PADDLE_HEIGHT))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, PADDLE_WIDTH, PADDLE_HEIGHT)

class Ball:
    def __init__(self):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT // 2
        self.vx = BALL_SPEED * random.choice([-1, 1])
        self.vy = BALL_SPEED * random.choice([-1, 1])

    def update(self):
        self.x += self.vx
        self.y += self.vy

        if self.y <= 0 or self.y >= SCREEN_HEIGHT - BALL_SIZE:
            self.vy = -self.vy

    def draw(self):
        pygame.draw.rect(screen, WHITE, (self.x, self.y, BALL_SIZE, BALL_SIZE))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, BALL_SIZE, BALL_SIZE)

    def reset(self):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT // 2
        self.vx = BALL_SPEED * random.choice([-1, 1])
        self.vy = BALL_SPEED * random.choice([-1, 1])

def ai_move(paddle, ball):
    if paddle.y + PADDLE_HEIGHT // 2 < ball.y:
        paddle.move_down()
    elif paddle.y + PADDLE_HEIGHT // 2 > ball.y:
        paddle.move_up()

def draw_score(left_score, right_score):
    left_text = FONT.render(str(left_score), True, WHITE)
    screen.blit(left_text, (SCREEN_WIDTH // 4, 20))
    right_text = FONT.render(str(right_score), True, WHITE)
    screen.blit(right_text, (3 * SCREEN_WIDTH // 4, 20))

def main():
    left_paddle = Paddle(20, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2)
    right_paddle = Paddle(SCREEN_WIDTH - 30, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2)
    ball = Ball()
    left_score = 0
    right_score = 0
    running = True

    while running:
        screen.fill(BLACK)

        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if keys[pygame.K_w]:
            left_paddle.move_up()
        if keys[pygame.K_s]:
            left_paddle.move_down()

        ai_move(right_paddle, ball)

        ball.update()

        if ball.get_rect().colliderect(left_paddle.get_rect()) and ball.vx < 0:
            ball.vx = -ball.vx
        if ball.get_rect().colliderect(right_paddle.get_rect()) and ball.vx > 0:
            ball.vx = -ball.vx

        if ball.x < 0:
            right_score += 1
            ball.reset()
        if ball.x > SCREEN_WIDTH:
            left_score += 1
            ball.reset()

        left_paddle.draw()
        right_paddle.draw()
        ball.draw()
        draw_score(left_score, right_score)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()