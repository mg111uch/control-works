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

RUNWAYS = 3
RUNWAY_WIDTH = SCREEN_WIDTH // RUNWAYS
PLANE_SIZE = 20
PLANE_SPEED = 2

FONT = pygame.font.SysFont(None, 36)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Air Traffic Landing Control")

clock = pygame.time.Clock()

class Plane:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH - PLANE_SIZE)
        self.y = 0
        self.runway = None
        self.target_x = None

    def update(self):
        if self.runway is not None:
            if self.target_x is None:
                self.target_x = self.runway * RUNWAY_WIDTH + RUNWAY_WIDTH // 2 - PLANE_SIZE // 2
            if self.x < self.target_x:
                self.x += min(PLANE_SPEED, self.target_x - self.x)
            elif self.x > self.target_x:
                self.x -= min(PLANE_SPEED, self.x - self.target_x)
            self.y += PLANE_SPEED
        else:
            self.y += PLANE_SPEED

    def draw(self):
        pygame.draw.rect(screen, GREEN, (self.x, self.y, PLANE_SIZE, PLANE_SIZE))

    def landed(self):
        return self.y >= SCREEN_HEIGHT - PLANE_SIZE

    def crashed(self):
        return self.y >= SCREEN_HEIGHT

def draw_runways():
    for i in range(RUNWAYS):
        x = i * RUNWAY_WIDTH
        pygame.draw.rect(screen, GRAY, (x, SCREEN_HEIGHT - 50, RUNWAY_WIDTH, 50))

def check_collisions(planes):
    landed = {}
    for plane in planes:
        if plane.runway is not None and plane.landed():
            if plane.runway in landed:
                return True  # collision
            landed[plane.runway] = True
    return False

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
    planes = []
    score = 0
    running = True
    game_over = False
    last_plane = 0

    while running:
        screen.fill(WHITE)
        draw_runways()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                if event.button == 1:
                    pos = pygame.mouse.get_pos()
                    runway = pos[0] // RUNWAY_WIDTH
                    for plane in planes:
                        if plane.runway is None and plane.x <= pos[0] <= plane.x + PLANE_SIZE and plane.y <= pos[1] <= plane.y + PLANE_SIZE:
                            plane.runway = runway
                            break
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and game_over:
                    planes = []
                    score = 0
                    game_over = False
                    last_plane = 0

        if not game_over:
            if time.time() - last_plane > random.uniform(1, 3):
                planes.append(Plane())
                last_plane = time.time()

            for plane in planes[:]:
                plane.update()
                if plane.crashed():
                    game_over = True
                elif plane.landed():
                    planes.remove(plane)
                    score += 10

            if check_collisions(planes):
                game_over = True

            for plane in planes:
                plane.draw()
            draw_score(score)
        else:
            game_over_screen(score)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()