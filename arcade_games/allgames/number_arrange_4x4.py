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

GRID_SIZE = 4
CELL_SIZE = 80
OFFSET_X = (SCREEN_WIDTH - GRID_SIZE * CELL_SIZE) // 2
OFFSET_Y = (SCREEN_HEIGHT - GRID_SIZE * CELL_SIZE) // 2

FONT = pygame.font.SysFont(None, 48)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Number Arrange 4x4")

clock = pygame.time.Clock()

def init_grid():
    grid = list(range(1, 16)) + [0]
    random.shuffle(grid)
    return [grid[i:i+4] for i in range(0, 16, 4)]

def draw_grid(grid):
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            x = OFFSET_X + j * CELL_SIZE
            y = OFFSET_Y + i * CELL_SIZE
            pygame.draw.rect(screen, GRAY, (x, y, CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(screen, BLACK, (x, y, CELL_SIZE, CELL_SIZE), 2)
            if grid[i][j] != 0:
                text = FONT.render(str(grid[i][j]), True, BLACK)
                text_rect = text.get_rect(center=(x + CELL_SIZE // 2, y + CELL_SIZE // 2))
                screen.blit(text, text_rect)

def find_empty(grid):
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if grid[i][j] == 0:
                return i, j

def move(grid, i, j):
    ei, ej = find_empty(grid)
    if abs(i - ei) + abs(j - ej) == 1:
        grid[ei][ej], grid[i][j] = grid[i][j], grid[ei][ej]
        return True
    return False

def is_solved(grid):
    flat = [grid[i][j] for i in range(GRID_SIZE) for j in range(GRID_SIZE)]
    return flat == list(range(1, 16)) + [0]

def get_cell(pos):
    x, y = pos
    j = (x - OFFSET_X) // CELL_SIZE
    i = (y - OFFSET_Y) // CELL_SIZE
    if 0 <= i < GRID_SIZE and 0 <= j < GRID_SIZE:
        return i, j
    return None

def draw_score(moves):
    text = FONT.render(f"Moves: {moves}", True, BLACK)
    screen.blit(text, (10, 10))

def game_over_screen(moves, won):
    screen.fill(BLUE)
    if won:
        text = FONT.render("You Win!", True, GREEN)
    else:
        text = FONT.render("Game Over!", True, RED)
    screen.blit(text, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 - 50))
    moves_text = FONT.render(f"Moves: {moves}", True, BLACK)
    screen.blit(moves_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2))
    restart_text = FONT.render("Press SPACE to restart", True, BLACK)
    screen.blit(restart_text, (SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 50))
    pygame.display.flip()

def main():
    grid = init_grid()
    moves = 0
    running = True
    game_over = False
    won = False

    while running:
        screen.fill(WHITE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                if event.button == 1:
                    cell = get_cell(event.pos)
                    if cell:
                        i, j = cell
                        if move(grid, i, j):
                            moves += 1
                            if is_solved(grid):
                                won = True
                                game_over = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and game_over:
                    grid = init_grid()
                    moves = 0
                    game_over = False
                    won = False

        if not game_over:
            draw_grid(grid)
            draw_score(moves)
        else:
            game_over_screen(moves, won)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()