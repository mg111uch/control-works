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

BOARD_SIZE = 7
CELL_SIZE = 40
OFFSET_X = (SCREEN_WIDTH - BOARD_SIZE * CELL_SIZE) // 2
OFFSET_Y = (SCREEN_HEIGHT - BOARD_SIZE * CELL_SIZE) // 2
PEG_RADIUS = 15

FONT = pygame.font.SysFont(None, 36)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Peg Solitaire")

clock = pygame.time.Clock()

def init_board():
    board = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if (2 <= i <= 4 or 2 <= j <= 4) and not (i == 3 and j == 3):
                board[i][j] = 1  # peg
    board[3][3] = 0  # center empty
    return board

def is_valid_pos(i, j):
    return 0 <= i < BOARD_SIZE and 0 <= j < BOARD_SIZE and (2 <= i <= 4 or 2 <= j <= 4)

def draw_board(board, selected):
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if is_valid_pos(i, j):
                x = OFFSET_X + j * CELL_SIZE + CELL_SIZE // 2
                y = OFFSET_Y + i * CELL_SIZE + CELL_SIZE // 2
                pygame.draw.circle(screen, GRAY, (x, y), PEG_RADIUS + 5)
                if board[i][j] == 1:
                    color = RED if selected and selected == (i, j) else GREEN
                    pygame.draw.circle(screen, color, (x, y), PEG_RADIUS)
                elif board[i][j] == 0:
                    pygame.draw.circle(screen, WHITE, (x, y), PEG_RADIUS)

def get_cell(pos):
    x, y = pos
    j = (x - OFFSET_X) // CELL_SIZE
    i = (y - OFFSET_Y) // CELL_SIZE
    if is_valid_pos(i, j):
        return i, j
    return None

def can_jump(board, si, sj, ei, ej):
    di = ei - si
    dj = ej - sj
    if abs(di) + abs(dj) != 2:
        return False
    mi = si + di // 2
    mj = sj + dj // 2
    return board[mi][mj] == 1 and board[ei][ej] == 0

def make_jump(board, si, sj, ei, ej):
    di = ei - si
    dj = ej - sj
    mi = si + di // 2
    mj = sj + dj // 2
    board[si][sj] = 0
    board[mi][mj] = 0
    board[ei][ej] = 1

def count_pegs(board):
    return sum(sum(row) for row in board)

def draw_score(pegs):
    text = FONT.render(f"Pegs: {pegs}", True, BLACK)
    screen.blit(text, (10, 10))

def game_over_screen(pegs, won):
    screen.fill(BLUE)
    if won:
        text = FONT.render("You Win!", True, GREEN)
    else:
        text = FONT.render("No More Moves!", True, RED)
    screen.blit(text, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 - 50))
    pegs_text = FONT.render(f"Pegs left: {pegs}", True, BLACK)
    screen.blit(pegs_text, (SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT // 2))
    restart_text = FONT.render("Press SPACE to restart", True, BLACK)
    screen.blit(restart_text, (SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 50))
    pygame.display.flip()

def main():
    board = init_board()
    selected = None
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
                        if selected is None:
                            if board[i][j] == 1:
                                selected = (i, j)
                        else:
                            si, sj = selected
                            if (i, j) == selected:
                                selected = None
                            elif can_jump(board, si, sj, i, j):
                                make_jump(board, si, sj, i, j)
                                selected = None
                                pegs = count_pegs(board)
                                if pegs == 1:
                                    won = True
                                    game_over = True
                                elif not any(can_jump(board, x, y, a, b) for x in range(BOARD_SIZE) for y in range(BOARD_SIZE) if board[x][y] == 1 for a in range(BOARD_SIZE) for b in range(BOARD_SIZE) if is_valid_pos(a, b) and can_jump(board, x, y, a, b)):
                                    game_over = True
                            else:
                                selected = None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and game_over:
                    board = init_board()
                    selected = None
                    game_over = False
                    won = False

        if not game_over:
            draw_board(board, selected)
            draw_score(count_pegs(board))
        else:
            game_over_screen(count_pegs(board), won)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()