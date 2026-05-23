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

COLUMNS = 4
TILE_WIDTH = SCREEN_WIDTH // COLUMNS
TILE_HEIGHT = 50
SPEED = 3
BOTTOM_Y = SCREEN_HEIGHT - TILE_HEIGHT

FONT = pygame.font.SysFont(None, 36)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Piano Tiles")

clock = pygame.time.Clock()

class Tile:
    def __init__(self, col):
        self.col = col
        self.y = -TILE_HEIGHT
        self.color = BLACK if random.random() < 0.3 else WHITE

    def update(self):
        self.y += SPEED

    def draw(self):
        x = self.col * TILE_WIDTH
        pygame.draw.rect(screen, self.color, (x, self.y, TILE_WIDTH, TILE_HEIGHT))
        pygame.draw.rect(screen, GRAY, (x, self.y, TILE_WIDTH, TILE_HEIGHT), 2)

    def is_black(self):
        return self.color == BLACK

    def at_bottom(self):
        return self.y >= BOTTOM_Y

def draw_columns():
    for i in range(COLUMNS):
        x = i * TILE_WIDTH
        pygame.draw.rect(screen, GRAY, (x, 0, TILE_WIDTH, SCREEN_HEIGHT), 1)

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
    tiles = []
    score = 0
    running = True
    game_over = False
    last_tile = 0

    while running:
        screen.fill(WHITE)
        draw_columns()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                if event.button == 1:
                    pos = pygame.mouse.get_pos()
                    col = pos[0] // TILE_WIDTH
                    for tile in tiles[:]:
                        if tile.col == col and tile.at_bottom():
                            if tile.is_black():
                                tiles.remove(tile)
                                score += 1
                            else:
                                game_over = True
                            break
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and game_over:
                    tiles = []
                    score = 0
                    game_over = False
                    last_tile = 0

        if not game_over:
            if time.time() - last_tile > 0.5:
                tiles.append(Tile(random.randint(0, COLUMNS - 1)))
                last_tile = time.time()

            for tile in tiles[:]:
                tile.update()
                if tile.at_bottom() and tile.is_black():
                    game_over = True
                elif tile.y > SCREEN_HEIGHT:
                    tiles.remove(tile)

            for tile in tiles:
                tile.draw()
            draw_score(score)

        else:
            game_over_screen(score)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()