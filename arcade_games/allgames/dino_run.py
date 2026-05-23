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
DINO_WIDTH = 40
DINO_HEIGHT = 40
DINO_X = 50
DINO_Y = GROUND_Y - DINO_HEIGHT
JUMP_HEIGHT = 100
GRAVITY = 5
CACTUS_WIDTH = 20
CACTUS_HEIGHT = 40
CACTUS_SPEED = 5

FONT = pygame.font.SysFont(None, 36)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Chrome Dino Run")

clock = pygame.time.Clock()

class Dino:
    def __init__(self):
        self.x = DINO_X
        self.y = DINO_Y
        self.vel_y = 0
        self.jumping = False

    def jump(self):
        if not self.jumping:
            self.vel_y = -15
            self.jumping = True

    def update(self):
        self.y += self.vel_y
        self.vel_y += GRAVITY
        if self.y >= DINO_Y:
            self.y = DINO_Y
            self.vel_y = 0
            self.jumping = False

    def draw(self):
        pygame.draw.rect(screen, GREEN, (self.x, self.y, DINO_WIDTH, DINO_HEIGHT))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, DINO_WIDTH, DINO_HEIGHT)

class Cactus:
    def __init__(self):
        self.x = SCREEN_WIDTH
        self.y = GROUND_Y - CACTUS_HEIGHT

    def update(self):
        self.x -= CACTUS_SPEED

    def draw(self):
        pygame.draw.rect(screen, RED, (self.x, self.y, CACTUS_WIDTH, CACTUS_HEIGHT))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, CACTUS_WIDTH, CACTUS_HEIGHT)

    def off_screen(self):
        return self.x + CACTUS_WIDTH < 0

def draw_score(score):
    text = FONT.render(f"Score: {score}", True, BLACK)
    screen.blit(text, (10, 10))

def game_over_screen(score):
    screen.fill(BLUE)
    text = FONT.render("Game Over!", True, BLACK)
    screen.blit(text, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 - 50))
    score_text = FONT.render(f"Score: {score}", True, BLACK)
    screen.blit(score_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2))
    restart_text = FONT.render("Press SPACE to restart", True, BLACK)
    screen.blit(restart_text, (SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 50))
    pygame.display.flip()

def main():
    dino = Dino()
    cacti = []
    score = 0
    running = True
    game_over = False
    last_cactus = 0

    while running:
        screen.fill(BLUE)
        pygame.draw.line(screen, GRAY, (0, GROUND_Y), (SCREEN_WIDTH, GROUND_Y), 2)

        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if game_over:
                        # Restart
                        dino = Dino()
                        cacti = []
                        score = 0
                        game_over = False
                        last_cactus = 0
                    else:
                        dino.jump()

        if not game_over:
            dino.update()

            if time.time() - last_cactus > random.uniform(1, 3):
                cacti.append(Cactus())
                last_cactus = time.time()

            for cactus in cacti[:]:
                cactus.update()
                if cactus.off_screen():
                    cacti.remove(cactus)
                    score += 1

            dino_rect = dino.get_rect()
            for cactus in cacti:
                if dino_rect.colliderect(cactus.get_rect()):
                    game_over = True

            dino.draw()
            for cactus in cacti:
                cactus.draw()
            draw_score(score)

        else:
            game_over_screen(score)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()