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

PLAYER_WIDTH = 40
PLAYER_HEIGHT = 20
PLAYER_SPEED = 5
BULLET_SPEED = 7
ALIEN_WIDTH = 30
ALIEN_HEIGHT = 20
ALIEN_SPEED = 1
ALIEN_DROP = 20

FONT = pygame.font.SysFont(None, 36)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Invaders")

clock = pygame.time.Clock()

class Player:
    def __init__(self):
        self.x = SCREEN_WIDTH // 2 - PLAYER_WIDTH // 2
        self.y = SCREEN_HEIGHT - PLAYER_HEIGHT - 10

    def move_left(self):
        self.x -= PLAYER_SPEED
        if self.x < 0:
            self.x = 0

    def move_right(self):
        self.x += PLAYER_SPEED
        if self.x + PLAYER_WIDTH > SCREEN_WIDTH:
            self.x = SCREEN_WIDTH - PLAYER_WIDTH

    def draw(self):
        pygame.draw.rect(screen, GREEN, (self.x, self.y, PLAYER_WIDTH, PLAYER_HEIGHT))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, PLAYER_WIDTH, PLAYER_HEIGHT)

class Bullet:
    def __init__(self, x, y, vy):
        self.x = x
        self.y = y
        self.vy = vy

    def update(self):
        self.y += self.vy

    def draw(self):
        pygame.draw.rect(screen, YELLOW, (self.x, self.y, 5, 10))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, 5, 10)

    def off_screen(self):
        return self.y < 0 or self.y > SCREEN_HEIGHT

class Alien:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def draw(self):
        pygame.draw.rect(screen, RED, (self.x, self.y, ALIEN_WIDTH, ALIEN_HEIGHT))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, ALIEN_WIDTH, ALIEN_HEIGHT)

def create_aliens():
    aliens = []
    for i in range(5):
        for j in range(10):
            aliens.append(Alien(50 + j * 50, 50 + i * 40))
    return aliens

def move_aliens(aliens, direction):
    for alien in aliens:
        alien.x += direction * ALIEN_SPEED
    # Check if hit edge
    if aliens and (aliens[0].x <= 0 or aliens[-1].x + ALIEN_WIDTH >= SCREEN_WIDTH):
        for alien in aliens:
            alien.y += ALIEN_DROP
        return -direction
    return direction

def draw_score(score):
    text = FONT.render(f"Score: {score}", True, WHITE)
    screen.blit(text, (10, 10))

def game_over_screen(score, won):
    screen.fill(BLUE)
    if won:
        text = FONT.render("You Win!", True, GREEN)
    else:
        text = FONT.render("Game Over!", True, RED)
    screen.blit(text, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 - 50))
    score_text = FONT.render(f"Score: {score}", True, BLACK)
    screen.blit(score_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2))
    restart_text = FONT.render("Press SPACE to restart", True, BLACK)
    screen.blit(restart_text, (SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 50))
    pygame.display.flip()

def main():
    player = Player()
    bullets = []
    aliens = create_aliens()
    alien_direction = 1
    score = 0
    running = True
    game_over = False
    won = False
    last_shot = 0

    while running:
        screen.fill(BLACK)

        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and game_over:
                    player = Player()
                    bullets = []
                    aliens = create_aliens()
                    alien_direction = 1
                    score = 0
                    game_over = False
                    won = False
                    last_shot = 0

        if not game_over:
            if keys[pygame.K_LEFT]:
                player.move_left()
            if keys[pygame.K_RIGHT]:
                player.move_right()
            if keys[pygame.K_SPACE] and time.time() - last_shot > 0.2:
                bullets.append(Bullet(player.x + PLAYER_WIDTH // 2 - 2, player.y, -BULLET_SPEED))
                last_shot = time.time()

            alien_direction = move_aliens(aliens, alien_direction)

            for bullet in bullets[:]:
                bullet.update()
                if bullet.off_screen():
                    bullets.remove(bullet)
                else:
                    for alien in aliens[:]:
                        if bullet.get_rect().colliderect(alien.get_rect()):
                            bullets.remove(bullet)
                            aliens.remove(alien)
                            score += 10
                            break

            for alien in aliens:
                if alien.y + ALIEN_HEIGHT >= player.y:
                    game_over = True

            if not aliens:
                won = True
                game_over = True

            player.draw()
            for bullet in bullets:
                bullet.draw()
            for alien in aliens:
                alien.draw()
            draw_score(score)
        else:
            game_over_screen(score, won)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()