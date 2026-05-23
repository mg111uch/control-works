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
TILE_SIZE = 80
MARGIN = 10
GRID_OFFSET_X = (SCREEN_WIDTH - (GRID_SIZE * TILE_SIZE + (GRID_SIZE - 1) * MARGIN)) // 2
GRID_OFFSET_Y = (SCREEN_HEIGHT - (GRID_SIZE * TILE_SIZE + (GRID_SIZE - 1) * MARGIN)) // 2

TILE_COLORS = {
    0: GRAY,
    2: (238, 228, 218),
    4: (237, 224, 200),
    8: (242, 177, 121),
    16: (245, 149, 99),
    32: (246, 124, 95),
    64: (246, 94, 59),
    128: (237, 207, 114),
    256: (237, 204, 97),
    512: (237, 200, 80),
    1024: (237, 197, 63),
    2048: (237, 194, 46),
}

FONT = pygame.font.SysFont(None, 36)
SMALL_FONT = pygame.font.SysFont(None, 24)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Puzzle 2048")

clock = pygame.time.Clock()

def init_grid():
    grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
    add_random_tile(grid)
    add_random_tile(grid)
    return grid

def add_random_tile(grid):
    empty = [(i, j) for i in range(GRID_SIZE) for j in range(GRID_SIZE) if grid[i][j] == 0]
    if empty:
        i, j = random.choice(empty)
        grid[i][j] = 2 if random.random() < 0.9 else 4

def draw_grid(grid):
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            x = GRID_OFFSET_X + j * (TILE_SIZE + MARGIN)
            y = GRID_OFFSET_Y + i * (TILE_SIZE + MARGIN)
            pygame.draw.rect(screen, TILE_COLORS.get(grid[i][j], RED), (x, y, TILE_SIZE, TILE_SIZE))
            if grid[i][j] != 0:
                text = SMALL_FONT.render(str(grid[i][j]), True, BLACK)
                text_rect = text.get_rect(center=(x + TILE_SIZE // 2, y + TILE_SIZE // 2))
                screen.blit(text, text_rect)

def move_left(grid):
    moved = False
    for i in range(GRID_SIZE):
        row = [x for x in grid[i] if x != 0]
        for j in range(len(row) - 1):
            if row[j] == row[j + 1]:
                row[j] *= 2
                row[j + 1] = 0
        row = [x for x in row if x != 0]
        row += [0] * (GRID_SIZE - len(row))
        if grid[i] != row:
            moved = True
        grid[i] = row
    return moved

def move_right(grid):
    moved = False
    for i in range(GRID_SIZE):
        row = [x for x in grid[i] if x != 0]
        for j in range(len(row) - 1, 0, -1):
            if row[j] == row[j - 1]:
                row[j] *= 2
                row[j - 1] = 0
        row = [0] * (GRID_SIZE - len(row)) + [x for x in row if x != 0]
        if grid[i] != row:
            moved = True
        grid[i] = row
    return moved

def move_up(grid):
    moved = False
    for j in range(GRID_SIZE):
        col = [grid[i][j] for i in range(GRID_SIZE) if grid[i][j] != 0]
        for i in range(len(col) - 1):
            if col[i] == col[i + 1]:
                col[i] *= 2
                col[i + 1] = 0
        col = [x for x in col if x != 0]
        col += [0] * (GRID_SIZE - len(col))
        for i in range(GRID_SIZE):
            if grid[i][j] != col[i]:
                moved = True
            grid[i][j] = col[i]
    return moved

def move_down(grid):
    moved = False
    for j in range(GRID_SIZE):
        col = [grid[i][j] for i in range(GRID_SIZE) if grid[i][j] != 0]
        for i in range(len(col) - 1, 0, -1):
            if col[i] == col[i - 1]:
                col[i] *= 2
                col[i - 1] = 0
        col = [0] * (GRID_SIZE - len(col)) + [x for x in col if x != 0]
        for i in range(GRID_SIZE):
            if grid[i][j] != col[i]:
                moved = True
            grid[i][j] = col[i]
    return moved

def can_move(grid):
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if grid[i][j] == 0:
                return True
            if i < GRID_SIZE - 1 and grid[i][j] == grid[i + 1][j]:
                return True
            if j < GRID_SIZE - 1 and grid[i][j] == grid[i][j + 1]:
                return True
    return False

def check_win(grid):
    for row in grid:
        if 2048 in row:
            return True
    return False

def draw_score(score):
    text = FONT.render(f"Score: {score}", True, BLACK)
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
    grid = init_grid()
    score = 0
    running = True
    game_over = False
    won = False

    while running:
        screen.fill(BLUE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and game_over:
                    grid = init_grid()
                    score = 0
                    game_over = False
                    won = False
                elif not game_over:
                    moved = False
                    if event.key == pygame.K_LEFT:
                        moved = move_left(grid)
                    elif event.key == pygame.K_RIGHT:
                        moved = move_right(grid)
                    elif event.key == pygame.K_UP:
                        moved = move_up(grid)
                    elif event.key == pygame.K_DOWN:
                        moved = move_down(grid)
                    if moved:
                        add_random_tile(grid)
                        if check_win(grid):
                            won = True
                            game_over = True
                        elif not can_move(grid):
                            game_over = True

        if not game_over:
            draw_grid(grid)
            draw_score(score)
        else:
            game_over_screen(score, won)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()