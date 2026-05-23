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

GROUND_Y = 350
CAR_WIDTH = 40
CAR_HEIGHT = 20
GRAVITY = 0.5
JUMP_VEL = -10
OBSTACLE_WIDTH = 20
OBSTACLE_HEIGHT = 40

FONT = pygame.font.SysFont(None, 36)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Car Jump")

clock = pygame.time.Clock()

class Car:
    def __init__(self):
        self.x = 50
        self.y = GROUND_Y - CAR_HEIGHT
        self.vy = 0
        self.on_ground = True

    def jump(self):
        if self.on_ground:
            self.vy = JUMP_VEL
            self.on_ground = False

    def update(self):
        self.vy += GRAVITY
        self.y += self.vy
        if self.y >= GROUND_Y - CAR_HEIGHT:
            self.y = GROUND_Y - CAR_HEIGHT
            self.vy = 0
            self.on_ground = True

    def draw(self):
        pygame.draw.rect(screen, RED, (self.x, self.y, CAR_WIDTH, CAR_HEIGHT))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, CAR_WIDTH, CAR_HEIGHT)

class Obstacle:
    def __init__(self, x):
        self.x = x
        self.y = GROUND_Y - OBSTACLE_HEIGHT

    def update(self):
        self.x -= 5

    def draw(self):
        pygame.draw.rect(screen, GREEN, (self.x, self.y, OBSTACLE_WIDTH, OBSTACLE_HEIGHT))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, OBSTACLE_WIDTH, OBSTACLE_HEIGHT)

    def off_screen(self):
        return self.x + OBSTACLE_WIDTH < 0

def draw_ground():
    pygame.draw.line(screen, GRAY, (0, GROUND_Y), (SCREEN_WIDTH, GROUND_Y), 2)

def draw_score(score):
    text = FONT.render(f"Score: {score}", True, BLACK)
    screen.blit(text, (10, 10))

def game_over_screen(score):
    screen.fill(BLUE)
    text = FONT.render("Game Over!", True, RED)
    screen.blit(text, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 - 50))
    score_text = FONT.render(f"Score: {score}", True, BLACK)
    screen.blit(score_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2))
    restart_text = FONT.render("Press SPACE to restart", True, BLACK)
    screen.blit(restart_text, (SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 50))
    pygame.display.flip()

def main():
    car = Car()
    obstacles = []
    score = 0
    running = True
    game_over = False
    last_obstacle = 0

    while running:
        screen.fill(WHITE)
        draw_ground()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and not game_over:
                if event.key == pygame.K_SPACE:
                    car.jump()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and game_over:
                    car = Car()
                    obstacles = []
                    score = 0
                    game_over = False
                    last_obstacle = 0

        if not game_over:
            car.update()

            if time.time() - last_obstacle > random.uniform(2, 4):
                obstacles.append(Obstacle(SCREEN_WIDTH))
                last_obstacle = time.time()

            for obs in obstacles[:]:
                obs.update()
                if obs.off_screen():
                    obstacles.remove(obs)
                    score += 1

            car_rect = car.get_rect()
            for obs in obstacles:
                if car_rect.colliderect(obs.get_rect()):
                    game_over = True

            car.draw()
            for obs in obstacles:
                obs.draw()
            draw_score(score)
        else:
            game_over_screen(score)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()