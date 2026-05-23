import pygame
import random
import sys
import time
import os
import math

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

CAR_WIDTH = 20
CAR_HEIGHT = 10
GRAVITY = 0.1
ACCELERATION = 0.5
FRICTION = 0.02
GOAL_X = 550

FONT = pygame.font.SysFont(None, 36)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Mountain Car")

clock = pygame.time.Clock()

class Car:
    def __init__(self):
        self.x = 50
        self.y = self.get_mountain_y(self.x)
        self.vel_x = 0
        self.vel_y = 0

    def get_mountain_y(self, x):
        # Sinusoidal mountain
        return SCREEN_HEIGHT - 100 - 50 * math.sin(x / 100) - 20 * math.sin(x / 50)

    def update(self, accelerate):
        if accelerate:
            self.vel_x += ACCELERATION
        self.vel_x -= FRICTION * self.vel_x  # friction
        self.x += self.vel_x
        if self.x < 0:
            self.x = 0
            self.vel_x = 0
        mountain_y = self.get_mountain_y(self.x)
        if self.y < mountain_y:
            self.y = mountain_y
            self.vel_y = 0
        else:
            self.vel_y += GRAVITY
            self.y += self.vel_y
            if self.y > mountain_y:
                self.y = mountain_y
                self.vel_y = 0

    def draw(self):
        pygame.draw.rect(screen, RED, (self.x - CAR_WIDTH // 2, self.y - CAR_HEIGHT, CAR_WIDTH, CAR_HEIGHT))

def draw_mountain():
    points = []
    for x in range(0, SCREEN_WIDTH, 5):
        y = SCREEN_HEIGHT - 100 - 50 * math.sin(x / 100) - 20 * math.sin(x / 50)
        points.append((x, y))
    pygame.draw.lines(screen, GREEN, False, points, 3)

def draw_goal():
    pygame.draw.line(screen, YELLOW, (GOAL_X, 0), (GOAL_X, SCREEN_HEIGHT), 5)

def draw_score(score):
    text = FONT.render(f"Max X: {score}", True, BLACK)
    screen.blit(text, (10, 10))

def game_over_screen(score, won):
    screen.fill(BLUE)
    if won:
        text = FONT.render("You Win!", True, GREEN)
    else:
        text = FONT.render("Game Over!", True, RED)
    screen.blit(text, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 - 50))
    score_text = FONT.render(f"Max X: {score}", True, BLACK)
    screen.blit(score_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2))
    restart_text = FONT.render("Press SPACE to restart", True, BLACK)
    screen.blit(restart_text, (SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 50))
    pygame.display.flip()

def main():
    car = Car()
    max_x = 50
    running = True
    game_over = False
    won = False

    while running:
        screen.fill(BLUE)
        draw_mountain()
        draw_goal()

        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and game_over:
                    car = Car()
                    max_x = 50
                    game_over = False
                    won = False

        if not game_over:
            accelerate = keys[pygame.K_SPACE]
            car.update(accelerate)
            max_x = max(max_x, car.x)
            if car.x >= GOAL_X:
                won = True
                game_over = True
            elif car.x <= 0 and car.vel_x < 0.1:
                game_over = True
            car.draw()
            draw_score(int(max_x))
        else:
            game_over_screen(int(max_x), won)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()