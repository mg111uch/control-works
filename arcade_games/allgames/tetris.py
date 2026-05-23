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

BOARD_WIDTH = 10
BOARD_HEIGHT = 20
CELL_SIZE = 20
OFFSET_X = (SCREEN_WIDTH - BOARD_WIDTH * CELL_SIZE) // 2
OFFSET_Y = (SCREEN_HEIGHT - BOARD_HEIGHT * CELL_SIZE) // 2

SHAPES = [
    [[(0,0), (1,0), (2,0), (3,0)], RED],  # I
    [[(0,0), (0,1), (1,0), (1,1)], YELLOW],  # O
    [[(0,1), (1,0), (1,1), (2,1)], GREEN],  # S
    [[(0,0), (1,0), (1,1), (2,1)], BLUE],  # Z
    [[(0,1), (1,1), (2,0), (2,1)], (255, 165, 0)],  # L
    [[(0,0), (1,0), (2,0), (2,1)], (128, 0, 128)],  # J
    [[(0,1), (1,0), (1,1), (2,1)], (0, 255, 255)],  # T
]

FONT = pygame.font.SysFont(None, 36)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Tetris")

clock = pygame.time.Clock()

def rotate_shape(shape):
    return [(y, -x) for x, y in shape]

def valid_position(board, shape, x, y):
    for dx, dy in shape:
        nx, ny = x + dx, y + dy
        if nx < 0 or nx >= BOARD_WIDTH or ny >= BOARD_HEIGHT or (ny >= 0 and board[ny][nx]):
            return False
    return True

def place_shape(board, shape, x, y, color):
    for dx, dy in shape:
        nx, ny = x + dx, y + dy
        if ny >= 0:
            board[ny][nx] = color

def clear_lines(board):
    lines = 0
    for i in range(BOARD_HEIGHT):
        if all(board[i]):
            del board[i]
            board.insert(0, [0] * BOARD_WIDTH)
            lines += 1
    return lines

def draw_board(board):
    for y in range(BOARD_HEIGHT):
        for x in range(BOARD_WIDTH):
            if board[y][x]:
                pygame.draw.rect(screen, board[y][x], (OFFSET_X + x * CELL_SIZE, OFFSET_Y + y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
                pygame.draw.rect(screen, BLACK, (OFFSET_X + x * CELL_SIZE, OFFSET_Y + y * CELL_SIZE, CELL_SIZE, CELL_SIZE), 1)

def draw_shape(shape, x, y, color):
    for dx, dy in shape:
        nx, ny = x + dx, y + dy
        if ny >= 0:
            pygame.draw.rect(screen, color, (OFFSET_X + nx * CELL_SIZE, OFFSET_Y + ny * CELL_SIZE, CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(screen, BLACK, (OFFSET_X + nx * CELL_SIZE, OFFSET_Y + ny * CELL_SIZE, CELL_SIZE, CELL_SIZE), 1)

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
    board = [[0] * BOARD_WIDTH for _ in range(BOARD_HEIGHT)]
    current_shape, current_color = random.choice(SHAPES)
    current_x = BOARD_WIDTH // 2 - 2
    current_y = 0
    score = 0
    fall_time = 0
    fall_speed = 500
    running = True
    game_over = False

    while running:
        screen.fill(WHITE)
        draw_board(board)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and not game_over:
                if event.key == pygame.K_LEFT:
                    if valid_position(board, current_shape, current_x - 1, current_y):
                        current_x -= 1
                elif event.key == pygame.K_RIGHT:
                    if valid_position(board, current_shape, current_x + 1, current_y):
                        current_x += 1
                elif event.key == pygame.K_DOWN:
                    if valid_position(board, current_shape, current_x, current_y + 1):
                        current_y += 1
                elif event.key == pygame.K_UP:
                    rotated = rotate_shape(current_shape)
                    if valid_position(board, rotated, current_x, current_y):
                        current_shape = rotated
                elif event.key == pygame.K_SPACE:
                    game_over = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and game_over:
                    board = [[0] * BOARD_WIDTH for _ in range(BOARD_HEIGHT)]
                    current_shape, current_color = random.choice(SHAPES)
                    current_x = BOARD_WIDTH // 2 - 2
                    current_y = 0
                    score = 0
                    game_over = False

        if not game_over:
            fall_time += clock.get_rawtime()
            if fall_time >= fall_speed:
                if valid_position(board, current_shape, current_x, current_y + 1):
                    current_y += 1
                else:
                    place_shape(board, current_shape, current_x, current_y, current_color)
                    lines = clear_lines(board)
                    score += lines * 100
                    current_shape, current_color = random.choice(SHAPES)
                    current_x = BOARD_WIDTH // 2 - 2
                    current_y = 0
                    if not valid_position(board, current_shape, current_x, current_y):
                        game_over = True
                fall_time = 0

            draw_shape(current_shape, current_x, current_y, current_color)
            draw_score(score)
        else:
            game_over_screen(score)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()