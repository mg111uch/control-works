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

GRID_SIZE = 6
CELL_SIZE = 50
OFFSET_X = (SCREEN_WIDTH - GRID_SIZE * CELL_SIZE) // 2
OFFSET_Y = (SCREEN_HEIGHT - GRID_SIZE * CELL_SIZE) // 2

FONT = pygame.font.SysFont(None, 36)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Unblock Me")

clock = pygame.time.Clock()

class Block:
    def __init__(self, x, y, w, h, color, is_red=False):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = color
        self.is_red = is_red

    def draw(self):
        px = OFFSET_X + self.x * CELL_SIZE
        py = OFFSET_Y + self.y * CELL_SIZE
        pygame.draw.rect(screen, self.color, (px, py, self.w * CELL_SIZE, self.h * CELL_SIZE))
        pygame.draw.rect(screen, BLACK, (px, py, self.w * CELL_SIZE, self.h * CELL_SIZE), 2)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)

def init_blocks():
    blocks = [
        Block(0, 0, 2, 1, GREEN),
        Block(2, 0, 1, 2, BLUE),
        Block(3, 0, 2, 1, YELLOW),
        Block(5, 0, 1, 3, BLUE),
        Block(0, 1, 1, 2, BLUE),
        Block(1, 2, 2, 1, RED, True),  # red block
        Block(3, 2, 1, 2, BLUE),
        Block(4, 2, 1, 2, BLUE),
        Block(0, 3, 2, 1, GREEN),
        Block(2, 3, 1, 2, BLUE),
        Block(3, 4, 2, 1, GREEN),
        Block(0, 4, 1, 2, BLUE),
        Block(1, 5, 2, 1, GREEN),
    ]
    return blocks

def draw_grid():
    for i in range(GRID_SIZE + 1):
        pygame.draw.line(screen, GRAY, (OFFSET_X, OFFSET_Y + i * CELL_SIZE), (OFFSET_X + GRID_SIZE * CELL_SIZE, OFFSET_Y + i * CELL_SIZE))
        pygame.draw.line(screen, GRAY, (OFFSET_X + i * CELL_SIZE, OFFSET_Y), (OFFSET_X + i * CELL_SIZE, OFFSET_Y + GRID_SIZE * CELL_SIZE))

def draw_exit():
    pygame.draw.rect(screen, GREEN, (OFFSET_X + GRID_SIZE * CELL_SIZE, OFFSET_Y + 2 * CELL_SIZE, 20, CELL_SIZE))

def collides(block, blocks, dx=0, dy=0):
    new_rect = pygame.Rect(block.x + dx, block.y + dy, block.w, block.h)
    if new_rect.left < 0 or new_rect.right > GRID_SIZE or new_rect.top < 0 or new_rect.bottom > GRID_SIZE:
        return True
    for b in blocks:
        if b != block and new_rect.colliderect(b.get_rect()):
            return True
    return False

def move_block(block, dx, dy, blocks):
    if not collides(block, blocks, dx, dy):
        block.x += dx
        block.y += dy
        return True
    return False

def check_win(blocks):
    for block in blocks:
        if block.is_red and block.x + block.w == GRID_SIZE:
            return True
    return False

def game_over_screen(won):
    screen.fill(BLUE)
    if won:
        text = FONT.render("You Win!", True, GREEN)
    else:
        text = FONT.render("Game Over!", True, RED)
    screen.blit(text, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 - 50))
    restart_text = FONT.render("Press SPACE to restart", True, BLACK)
    screen.blit(restart_text, (SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 50))
    pygame.display.flip()

def main():
    blocks = init_blocks()
    selected = None
    running = True
    game_over = False
    won = False

    while running:
        screen.fill(WHITE)
        draw_grid()
        draw_exit()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                if event.button == 1:
                    pos = pygame.mouse.get_pos()
                    gx = (pos[0] - OFFSET_X) // CELL_SIZE
                    gy = (pos[1] - OFFSET_Y) // CELL_SIZE
                    for block in blocks:
                        if block.x <= gx < block.x + block.w and block.y <= gy < block.y + block.h:
                            selected = block
                            break
            if event.type == pygame.KEYDOWN and selected and not game_over:
                moved = False
                if event.key == pygame.K_LEFT and selected.w > selected.h:
                    moved = move_block(selected, -1, 0, blocks)
                elif event.key == pygame.K_RIGHT and selected.w > selected.h:
                    moved = move_block(selected, 1, 0, blocks)
                elif event.key == pygame.K_UP and selected.h > selected.w:
                    moved = move_block(selected, 0, -1, blocks)
                elif event.key == pygame.K_DOWN and selected.h > selected.w:
                    moved = move_block(selected, 0, 1, blocks)
                if moved and check_win(blocks):
                    won = True
                    game_over = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and game_over:
                    blocks = init_blocks()
                    selected = None
                    game_over = False
                    won = False

        if not game_over:
            for block in blocks:
                block.draw()
            if selected:
                pygame.draw.rect(screen, YELLOW, (OFFSET_X + selected.x * CELL_SIZE - 2, OFFSET_Y + selected.y * CELL_SIZE - 2, selected.w * CELL_SIZE + 4, selected.h * CELL_SIZE + 4), 3)
        else:
            game_over_screen(won)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()