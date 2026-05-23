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

MAZE = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,1,0,1,0,0,0,1,0,0,0,1],
    [1,0,1,0,1,0,1,0,1,0,1,0,1,0,1],
    [1,0,1,0,0,0,0,0,1,0,0,0,1,0,1],
    [1,0,1,1,1,0,1,1,1,0,1,1,1,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,1,1,1,0,1,0,1,1,1,0,1,1,1],
    [1,0,1,0,0,0,1,0,0,0,1,0,0,0,1],
    [1,0,1,0,1,1,1,1,1,0,1,0,1,0,1],
    [1,0,0,0,1,0,0,0,1,0,0,0,1,0,1],
    [1,1,1,1,1,0,1,1,1,0,1,1,1,0,1],
    [1,0,0,0,0,0,1,0,0,0,0,0,0,0,1],
    [1,0,1,1,1,1,1,0,1,1,1,1,1,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
]

CELL_SIZE = 20
OFFSET_X = (SCREEN_WIDTH - len(MAZE[0]) * CELL_SIZE) // 2
OFFSET_Y = (SCREEN_HEIGHT - len(MAZE) * CELL_SIZE) // 2

PLAYER_START = (1, 1)
EXIT = (13, 13)

FONT = pygame.font.SysFont(None, 36)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Maze 2D")

clock = pygame.time.Clock()

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def move(self, dx, dy, maze):
        nx, ny = self.x + dx, self.y + dy
        if 0 <= nx < len(maze[0]) and 0 <= ny < len(maze) and maze[ny][nx] == 0:
            self.x, self.y = nx, ny

    def draw(self):
        px = OFFSET_X + self.x * CELL_SIZE + CELL_SIZE // 2
        py = OFFSET_Y + self.y * CELL_SIZE + CELL_SIZE // 2
        pygame.draw.circle(screen, GREEN, (px, py), CELL_SIZE // 2 - 2)

def draw_maze(maze):
    for y in range(len(maze)):
        for x in range(len(maze[0])):
            px = OFFSET_X + x * CELL_SIZE
            py = OFFSET_Y + y * CELL_SIZE
            if maze[y][x] == 1:
                pygame.draw.rect(screen, BLACK, (px, py, CELL_SIZE, CELL_SIZE))
            else:
                pygame.draw.rect(screen, WHITE, (px, py, CELL_SIZE, CELL_SIZE), 1)

def draw_exit():
    ex, ey = EXIT
    px = OFFSET_X + ex * CELL_SIZE
    py = OFFSET_Y + ey * CELL_SIZE
    pygame.draw.rect(screen, YELLOW, (px, py, CELL_SIZE, CELL_SIZE))

def draw_score(score):
    text = FONT.render(f"Time: {score:.1f}s", True, BLACK)
    screen.blit(text, (10, 10))

def game_over_screen(score, won):
    screen.fill(BLUE)
    if won:
        text = FONT.render("You Win!", True, GREEN)
    else:
        text = FONT.render("Game Over!", True, RED)
    screen.blit(text, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 - 50))
    score_text = FONT.render(f"Time: {score:.1f}s", True, BLACK)
    screen.blit(score_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2))
    restart_text = FONT.render("Press SPACE to restart", True, BLACK)
    screen.blit(restart_text, (SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 50))
    pygame.display.flip()

def main():
    player = Player(*PLAYER_START)
    start_time = time.time()
    running = True
    game_over = False
    won = False

    while running:
        screen.fill(WHITE)
        draw_maze(MAZE)
        draw_exit()

        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and game_over:
                    player = Player(*PLAYER_START)
                    start_time = time.time()
                    game_over = False
                    won = False

        if not game_over:
            if keys[pygame.K_LEFT]:
                player.move(-1, 0, MAZE)
            if keys[pygame.K_RIGHT]:
                player.move(1, 0, MAZE)
            if keys[pygame.K_UP]:
                player.move(0, -1, MAZE)
            if keys[pygame.K_DOWN]:
                player.move(0, 1, MAZE)

            if (player.x, player.y) == EXIT:
                won = True
                game_over = True

            player.draw()
            draw_score(time.time() - start_time)
        else:
            game_over_screen(time.time() - start_time, won)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()