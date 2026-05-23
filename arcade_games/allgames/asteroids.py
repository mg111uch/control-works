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

SHIP_SIZE = 20
BULLET_SPEED = 5
ASTEROID_SPEED = 1
THRUST = 0.1
ROT_SPEED = 3

FONT = pygame.font.SysFont(None, 36)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Asteroids")

clock = pygame.time.Clock()

class Ship:
    def __init__(self):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT // 2
        self.vx = 0
        self.vy = 0
        self.angle = 0

    def update(self, thrust, rot_left, rot_right):
        if rot_left:
            self.angle -= ROT_SPEED
        if rot_right:
            self.angle += ROT_SPEED
        if thrust:
            self.vx += THRUST * math.sin(math.radians(self.angle))
            self.vy -= THRUST * math.cos(math.radians(self.angle))
        self.x += self.vx
        self.y += self.vy
        self.x %= SCREEN_WIDTH
        self.y %= SCREEN_HEIGHT

    def draw(self):
        points = [
            (self.x + SHIP_SIZE * math.sin(math.radians(self.angle)), self.y - SHIP_SIZE * math.cos(math.radians(self.angle))),
            (self.x - SHIP_SIZE * math.sin(math.radians(self.angle + 120)), self.y + SHIP_SIZE * math.cos(math.radians(self.angle + 120))),
            (self.x - SHIP_SIZE * math.sin(math.radians(self.angle - 120)), self.y + SHIP_SIZE * math.cos(math.radians(self.angle - 120))),
        ]
        pygame.draw.polygon(screen, GREEN, points)

class Bullet:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.vx = BULLET_SPEED * math.sin(math.radians(angle))
        self.vy = -BULLET_SPEED * math.cos(math.radians(angle))

    def update(self):
        self.x += self.vx
        self.y += self.vy

    def draw(self):
        pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), 2)

    def off_screen(self):
        return self.x < 0 or self.x > SCREEN_WIDTH or self.y < 0 or self.y > SCREEN_HEIGHT

class Asteroid:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-ASTEROID_SPEED, ASTEROID_SPEED)
        self.vy = random.uniform(-ASTEROID_SPEED, ASTEROID_SPEED)
        self.size = 30

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.x %= SCREEN_WIDTH
        self.y %= SCREEN_HEIGHT

    def draw(self):
        pygame.draw.circle(screen, GRAY, (int(self.x), int(self.y)), self.size)

def collides(obj1, obj2):
    dx = obj1.x - obj2.x
    dy = obj1.y - obj2.y
    dist = math.sqrt(dx**2 + dy**2)
    return dist < obj1.size + obj2.size

def draw_score(score):
    text = FONT.render(f"Score: {score}", True, WHITE)
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
    ship = Ship()
    bullets = []
    asteroids = [Asteroid(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)) for _ in range(5)]
    score = 0
    running = True
    game_over = False
    last_shot = 0

    while running:
        screen.fill(BLACK)

        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and game_over:
                    ship = Ship()
                    bullets = []
                    asteroids = [Asteroid(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)) for _ in range(5)]
                    score = 0
                    game_over = False
                    last_shot = 0

        if not game_over:
            thrust = keys[pygame.K_UP]
            rot_left = keys[pygame.K_LEFT]
            rot_right = keys[pygame.K_RIGHT]
            ship.update(thrust, rot_left, rot_right)

            if keys[pygame.K_SPACE] and time.time() - last_shot > 0.2:
                bullets.append(Bullet(ship.x, ship.y, ship.angle))
                last_shot = time.time()

            for bullet in bullets[:]:
                bullet.update()
                if bullet.off_screen():
                    bullets.remove(bullet)
                else:
                    for asteroid in asteroids[:]:
                        if collides(bullet, asteroid):
                            bullets.remove(bullet)
                            asteroids.remove(asteroid)
                            score += 10
                            break

            for asteroid in asteroids:
                asteroid.update()
                if collides(ship, asteroid):
                    game_over = True

            ship.draw()
            for bullet in bullets:
                bullet.draw()
            for asteroid in asteroids:
                asteroid.draw()
            draw_score(score)
        else:
            game_over_screen(score)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()