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

GRAVITY = 0.05
THRUST = 0.1
ROT_SPEED = 3
LANDER_SIZE = 20
PLATFORM_Y = SCREEN_HEIGHT - 50
PLATFORM_X1 = 200
PLATFORM_X2 = 400
FUEL = 1000

FONT = pygame.font.SysFont(None, 36)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Lunar Lander")

clock = pygame.time.Clock()

class Lander:
    def __init__(self):
        self.x = SCREEN_WIDTH // 2
        self.y = 50
        self.vx = 0
        self.vy = 0
        self.angle = 0
        self.fuel = FUEL

    def update(self, thrust, rot_left, rot_right):
        self.vy += GRAVITY
        if thrust and self.fuel > 0:
            self.vx += THRUST * math.sin(math.radians(self.angle))
            self.vy -= THRUST * math.cos(math.radians(self.angle))
            self.fuel -= 1
        if rot_left:
            self.angle -= ROT_SPEED
        if rot_right:
            self.angle += ROT_SPEED
        self.x += self.vx
        self.y += self.vy

    def draw(self):
        # Draw as triangle
        points = [
            (self.x + LANDER_SIZE * math.sin(math.radians(self.angle)), self.y - LANDER_SIZE * math.cos(math.radians(self.angle))),
            (self.x - LANDER_SIZE * math.sin(math.radians(self.angle + 120)), self.y + LANDER_SIZE * math.cos(math.radians(self.angle + 120))),
            (self.x - LANDER_SIZE * math.sin(math.radians(self.angle - 120)), self.y + LANDER_SIZE * math.cos(math.radians(self.angle - 120))),
        ]
        pygame.draw.polygon(screen, GREEN, points)
        # Thrust flame
        if self.fuel > 0 and pygame.key.get_pressed()[pygame.K_UP]:
            flame_points = [
                (self.x + LANDER_SIZE * math.sin(math.radians(self.angle)), self.y - LANDER_SIZE * math.cos(math.radians(self.angle))),
                (self.x + (LANDER_SIZE + 10) * math.sin(math.radians(self.angle + 10)), self.y - (LANDER_SIZE + 10) * math.cos(math.radians(self.angle + 10))),
                (self.x + (LANDER_SIZE + 10) * math.sin(math.radians(self.angle - 10)), self.y - (LANDER_SIZE + 10) * math.cos(math.radians(self.angle - 10))),
            ]
            pygame.draw.polygon(screen, YELLOW, flame_points)

def draw_platform():
    pygame.draw.line(screen, GRAY, (PLATFORM_X1, PLATFORM_Y), (PLATFORM_X2, PLATFORM_Y), 5)

def check_landing(lander):
    if PLATFORM_Y - 5 <= lander.y <= PLATFORM_Y + 5 and PLATFORM_X1 <= lander.x <= PLATFORM_X2:
        speed = math.sqrt(lander.vx**2 + lander.vy**2)
        angle_ok = -10 <= lander.angle % 360 <= 10 or 350 <= lander.angle % 360 <= 370
        if speed < 1 and angle_ok:
            return True
    return False

def check_crash(lander):
    if lander.y > SCREEN_HEIGHT or lander.x < 0 or lander.x > SCREEN_WIDTH:
        return True
    if lander.y >= PLATFORM_Y and not (PLATFORM_X1 <= lander.x <= PLATFORM_X2):
        return True
    return False

def draw_hud(lander):
    fuel_text = FONT.render(f"Fuel: {lander.fuel}", True, BLACK)
    screen.blit(fuel_text, (10, 10))
    speed = math.sqrt(lander.vx**2 + lander.vy**2)
    speed_text = FONT.render(f"Speed: {speed:.2f}", True, BLACK)
    screen.blit(speed_text, (10, 40))

def game_over_screen(score, won):
    screen.fill(BLUE)
    if won:
        text = FONT.render("Successful Landing!", True, GREEN)
    else:
        text = FONT.render("Crashed!", True, RED)
    screen.blit(text, (SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 - 50))
    score_text = FONT.render(f"Fuel left: {score}", True, BLACK)
    screen.blit(score_text, (SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT // 2))
    restart_text = FONT.render("Press SPACE to restart", True, BLACK)
    screen.blit(restart_text, (SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 50))
    pygame.display.flip()

def main():
    lander = Lander()
    running = True
    game_over = False
    won = False

    while running:
        screen.fill(BLACK)
        draw_platform()

        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and game_over:
                    lander = Lander()
                    game_over = False
                    won = False

        if not game_over:
            thrust = keys[pygame.K_UP]
            rot_left = keys[pygame.K_LEFT]
            rot_right = keys[pygame.K_RIGHT]
            lander.update(thrust, rot_left, rot_right)
            lander.draw()
            draw_hud(lander)
            if check_landing(lander):
                won = True
                game_over = True
            elif check_crash(lander) or lander.fuel <= 0:
                game_over = True
        else:
            game_over_screen(lander.fuel, won)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()