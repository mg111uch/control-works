import pygame
import sys
import copy

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

N = 8
CELL_SIZE = 40
OFFSET_X = (SCREEN_WIDTH - N * CELL_SIZE) // 2
OFFSET_Y = (SCREEN_HEIGHT - N * CELL_SIZE) // 2

FONT = pygame.font.SysFont(None, 36)
SMALL_FONT = pygame.font.SysFont(None, 24)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("8 Queens")

clock = pygame.time.Clock()

def init_grid():
    return [[0] * N for _ in range(N)]

def possible(grid, y, x):
    l = len(grid)
    for i in range(l):
        if grid[y][i] == 1:
            return False
    for i in range(l):
        if grid[i][x] == 1:
            return False
    for i in range(l):
        for j in range(l):
            if grid[i][j] == 1:
                if abs(i - y) == abs(j - x):
                    return False
    return True

def solve(grid):
    l = len(grid)
    for y in range(l):
        for x in range(l):
            if grid[y][x] == 0:
                if possible(grid, y, x):
                    grid[y][x] = 1
                    solve(grid)
                    if sum(sum(a) for a in grid) == l:
                        return grid
                    grid[y][x] = 0
    return grid

def draw_grid(grid):
    for i in range(N):
        for j in range(N):
            x = OFFSET_X + j * CELL_SIZE
            y = OFFSET_Y + i * CELL_SIZE
            color = WHITE if (i + j) % 2 == 0 else GRAY
            pygame.draw.rect(screen, color, (x, y, CELL_SIZE, CELL_SIZE))
            if grid[i][j] == 1:
                pygame.draw.circle(screen, GREEN, (x + CELL_SIZE // 2, y + CELL_SIZE // 2), CELL_SIZE // 3)

def draw_buttons():
    manual_rect = pygame.Rect(50, 50, 80, 40)
    auto_rect = pygame.Rect(150, 50, 80, 40)
    pygame.draw.rect(screen, GRAY, manual_rect)
    pygame.draw.rect(screen, GRAY, auto_rect)
    manual_text = SMALL_FONT.render("Manual", True, BLACK)
    auto_text = SMALL_FONT.render("Auto", True, BLACK)
    screen.blit(manual_text, (manual_rect.x + 10, manual_rect.y + 10))
    screen.blit(auto_text, (auto_rect.x + 10, auto_rect.y + 10))
    return manual_rect, auto_rect

def get_cell(pos):
    x, y = pos
    j = (x - OFFSET_X) // CELL_SIZE
    i = (y - OFFSET_Y) // CELL_SIZE
    if 0 <= i < N and 0 <= j < N:
        return i, j
    return None

def check_win(grid):
    queens = sum(sum(row) for row in grid)
    if queens == N:
        # Check if valid
        for i in range(N):
            for j in range(N):
                if grid[i][j] == 1:
                    if not possible(grid, i, j):
                        return False
        return True
    return False

def draw_win_screen():
    screen.fill(BLUE)
    text = FONT.render("Solved!", True, GREEN)
    screen.blit(text, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 - 50))
    home_rect = pygame.Rect(SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2, 100, 40)
    pygame.draw.rect(screen, GRAY, home_rect)
    home_text = SMALL_FONT.render("Home", True, BLACK)
    screen.blit(home_text, (home_rect.x + 25, home_rect.y + 10))
    pygame.display.flip()
    return home_rect

def main():
    mode = None
    grid = init_grid()
    running = True
    game_over = False

    while running:
        screen.fill(WHITE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if game_over:
                    home_rect = draw_win_screen()
                    if home_rect.collidepoint(pos):
                        mode = None
                        grid = init_grid()
                        game_over = False
                elif mode is None:
                    manual_rect, auto_rect = draw_buttons()
                    if manual_rect.collidepoint(pos):
                        mode = 'manual'
                    elif auto_rect.collidepoint(pos):
                        mode = 'auto'
                        solved_grid = solve(copy.deepcopy(grid))
                        grid = solved_grid
                        if check_win(grid):
                            game_over = True
                elif mode == 'manual':
                    cell = get_cell(pos)
                    if cell:
                        i, j = cell
                        if grid[i][j] == 0 and possible(grid, i, j):
                            grid[i][j] = 1
                        elif grid[i][j] == 1:
                            grid[i][j] = 0
                        if check_win(grid):
                            game_over = True

        if game_over:
            draw_win_screen()
        elif mode is None:
            draw_buttons()
        else:
            draw_grid(grid)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()