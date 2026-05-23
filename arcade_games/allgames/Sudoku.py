import pygame
import copy

pygame.init()

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (135, 206, 235)
YELLOW = (255, 255, 0)
GREEN = (0, 128, 0)
GRAY = (128, 128, 128)
RED = (255, 0, 0)

CELL_SIZE = 50
GRID_SIZE = 9

FONT = pygame.font.SysFont(None, 36)
SMALL_FONT = pygame.font.SysFont(None, 24)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Sudoku")

clock = pygame.time.Clock()

# Fixed puzzle
PUZZLE = [
    [5,3,0,0,7,0,0,0,0],
    [6,0,0,1,9,5,0,0,0],
    [0,9,8,0,0,0,0,6,0],
    [8,0,0,0,6,0,0,0,3],
    [4,0,0,8,0,3,0,0,1],
    [7,0,0,0,2,0,0,0,6],
    [0,6,0,0,0,0,2,8,0],
    [0,0,0,4,1,9,0,0,5],
    [0,0,0,0,8,0,0,7,9]
]

def init_board():
    return copy.deepcopy(PUZZLE)

def draw_board(board, selected):
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            x = j * CELL_SIZE + 50
            y = i * CELL_SIZE + 50
            color = YELLOW if selected == (i, j) else WHITE
            pygame.draw.rect(screen, color, (x, y, CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(screen, BLACK, (x, y, CELL_SIZE, CELL_SIZE), 1)
            if board[i][j] != 0:
                text = FONT.render(str(board[i][j]), True, BLACK)
                screen.blit(text, (x + 15, y + 10))

    # Draw thick lines
    for i in range(0, GRID_SIZE + 1, 3):
        pygame.draw.line(screen, BLACK, (50, 50 + i * CELL_SIZE), (50 + GRID_SIZE * CELL_SIZE, 50 + i * CELL_SIZE), 3)
        pygame.draw.line(screen, BLACK, (50 + i * CELL_SIZE, 50), (50 + i * CELL_SIZE, 50 + GRID_SIZE * CELL_SIZE), 3)

def get_cell(pos):
    x, y = pos
    j = (x - 50) // CELL_SIZE
    i = (y - 50) // CELL_SIZE
    if 0 <= i < GRID_SIZE and 0 <= j < GRID_SIZE:
        return i, j
    return None

def is_valid(board, row, col, num):
    # Check row
    if num in board[row]:
        return False
    # Check column
    for i in range(GRID_SIZE):
        if board[i][col] == num:
            return False
    # Check box
    box_row = (row // 3) * 3
    box_col = (col // 3) * 3
    for i in range(3):
        for j in range(3):
            if board[box_row + i][box_col + j] == num:
                return False
    return True

def is_solved(board):
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if board[i][j] == 0 or not is_valid(board, i, j, board[i][j]):
                return False
    return True

def main():
    board = init_board()
    selected = None
    running = True

    while running:
        screen.fill(WHITE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                selected = get_cell(event.pos)
            if event.type == pygame.KEYDOWN and selected:
                i, j = selected
                if PUZZLE[i][j] == 0:  # Only allow editing empty cells
                    if event.key == pygame.K_BACKSPACE:
                        board[i][j] = 0
                    elif event.key in range(pygame.K_1, pygame.K_9 + 1):
                        num = event.key - pygame.K_0
                        if is_valid(board, i, j, num):
                            board[i][j] = num
                        else:
                            pass  # Invalid move, do nothing

        draw_board(board, selected)

        if is_solved(board):
            text = FONT.render("Solved!", True, GREEN)
            screen.blit(text, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()