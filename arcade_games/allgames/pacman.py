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
    [1,2,2,2,2,2,2,2,2,2,2,2,2,2,1],
    [1,2,1,1,1,2,1,1,1,2,1,1,1,2,1],
    [1,2,2,2,2,2,2,2,2,2,2,2,2,2,1],
    [1,2,1,1,1,2,1,2,1,2,1,1,1,2,1],
    [1,2,2,2,2,2,1,2,1,2,2,2,2,2,1],
    [1,1,1,1,1,2,1,1,1,2,1,1,1,1,1],
    [2,2,2,2,1,2,2,2,2,2,1,2,2,2,2],
    [1,1,1,1,1,2,1,1,1,2,1,1,1,1,1],
    [1,2,2,2,2,2,1,2,1,2,2,2,2,2,1],
    [1,2,1,1,1,2,1,2,1,2,1,1,1,2,1],
    [1,2,2,2,2,2,2,2,2,2,2,2,2,2,1],
    [1,2,1,1,1,2,1,1,1,2,1,1,1,2,1],
    [1,2,2,2,2,2,2,2,2,2,2,2,2,2,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
]

CELL_SIZE = 20
OFFSET_X = (SCREEN_WIDTH - len(MAZE[0]) * CELL_SIZE) // 2
OFFSET_Y = (SCREEN_HEIGHT - len(MAZE) * CELL_SIZE) // 2

PACMAN_START = (1, 1)
GHOST_STARTS = [(7, 7), (7, 8), (8, 7), (8, 8)]

FONT = pygame.font.SysFont(None, 36)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pacman")

clock = pygame.time.Clock()

class Pacman:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.dir = (0, 0)

    def move(self, maze):
        nx, ny = self.x + self.dir[0], self.y + self.dir[1]
        if 0 <= nx < len(maze[0]) and 0 <= ny < len(maze) and maze[ny][nx] != 1:
            self.x, self.y = nx, ny
            if maze[ny][nx] == 2:
                maze[ny][nx] = 0

    def draw(self):
        px = OFFSET_X + self.x * CELL_SIZE + CELL_SIZE // 2
        py = OFFSET_Y + self.y * CELL_SIZE + CELL_SIZE // 2
        pygame.draw.circle(screen, YELLOW, (px, py), CELL_SIZE // 2 - 2)

class Ghost:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.dir = random.choice([(0,1), (0,-1), (1,0), (-1,0)])

    def move(self, maze):
        dirs = [(0,1), (0,-1), (1,0), (-1,0)]
        random.shuffle(dirs)
        for dx, dy in dirs:
            nx, ny = self.x + dx, self.y + dy
            if 0 <= nx < len(maze[0]) and 0 <= ny < len(maze) and maze[ny][nx] != 1:
                self.x, self.y = nx, ny
                self.dir = (dx, dy)
                break

    def draw(self):
        px = OFFSET_X + self.x * CELL_SIZE + CELL_SIZE // 2
        py = OFFSET_Y + self.y * CELL_SIZE + CELL_SIZE // 2
        pygame.draw.circle(screen, self.color, (px, py), CELL_SIZE // 2 - 2)

def draw_maze(maze):
    for y in range(len(maze)):
        for x in range(len(maze[0])):
            px = OFFSET_X + x * CELL_SIZE
            py = OFFSET_Y + y * CELL_SIZE
            if maze[y][x] == 1:
                pygame.draw.rect(screen, BLUE, (px, py, CELL_SIZE, CELL_SIZE))
            elif maze[y][x] == 2:
                pygame.draw.circle(screen, WHITE, (px + CELL_SIZE // 2, py + CELL_SIZE // 2), 3)

def count_dots(maze):
    return sum(row.count(2) for row in maze)

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
    maze = [row[:] for row in MAZE]
    pacman = Pacman(*PACMAN_START)
    ghosts = [Ghost(*start, RED) for start in GHOST_STARTS]
    score = 0
    running = True
    game_over = False
    won = False
    move_timer = 0

    while running:
        screen.fill(BLACK)
        draw_maze(maze)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and not game_over:
                if event.key == pygame.K_LEFT:
                    pacman.dir = (-1, 0)
                elif event.key == pygame.K_RIGHT:
                    pacman.dir = (1, 0)
                elif event.key == pygame.K_UP:
                    pacman.dir = (0, -1)
                elif event.key == pygame.K_DOWN:
                    pacman.dir = (0, 1)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and game_over:
                    maze = [row[:] for row in MAZE]
                    pacman = Pacman(*PACMAN_START)
                    ghosts = [Ghost(*start, RED) for start in GHOST_STARTS]
                    score = 0
                    game_over = False
                    won = False

        if not game_over:
            move_timer += clock.get_rawtime()
            if move_timer >= 100:
                pacman.move(maze)
                for ghost in ghosts:
                    ghost.move(maze)
                move_timer = 0

            for ghost in ghosts:
                if pacman.x == ghost.x and pacman.y == ghost.y:
                    game_over = True

            if count_dots(maze) == 0:
                won = True
                game_over = True

            pacman.draw()
            for ghost in ghosts:
                ghost.draw()
            draw_score(score)
        else:
            game_over_screen(score, won)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()