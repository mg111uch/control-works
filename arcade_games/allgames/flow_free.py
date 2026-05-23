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

DOT_RADIUS = 10
LINE_WIDTH = 5

FONT = pygame.font.SysFont(None, 36)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Flow Free")

clock = pygame.time.Clock()

class Dot:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color

    def draw(self):
        pygame.draw.circle(screen, self.color, (self.x, self.y), DOT_RADIUS)

def init_dots():
    dots = [
        Dot(100, 100, RED),
        Dot(500, 100, RED),
        Dot(100, 300, BLUE),
        Dot(500, 300, BLUE),
    ]
    return dots

def draw_lines(lines):
    for line in lines:
        if len(line) > 1:
            pygame.draw.lines(screen, line[0], False, line[1:], LINE_WIDTH)

def lines_intersect(line1, line2):
    def ccw(A, B, C):
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])
    def intersect(A, B, C, D):
        return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)
    for i in range(len(line1) - 1):
        for j in range(len(line2) - 1):
            if intersect(line1[i], line1[i+1], line2[j], line2[j+1]):
                return True
    return False

def check_win(dots, lines):
    if len(lines) != 2:
        return False
    # Check connections
    connected = [False] * len(dots)
    for line in lines:
        if len(line) < 2:
            return False
        start_color = line[0]
        end_color = line[-1]
        if start_color != end_color:
            return False
        # Find dots
        start_dot = None
        end_dot = None
        for dot in dots:
            if (dot.x, dot.y) == line[1]:
                start_dot = dot
            if (dot.x, dot.y) == line[-1]:
                end_dot = dot
        if not start_dot or not end_dot or start_dot.color != end_dot.color:
            return False
        connected[dots.index(start_dot)] = True
        connected[dots.index(end_dot)] = True
    # Check no intersections
    for i in range(len(lines)):
        for j in range(i+1, len(lines)):
            if lines_intersect(lines[i][1:], lines[j][1:]):
                return False
    return all(connected)

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
    dots = init_dots()
    lines = []
    current_line = None
    running = True
    game_over = False
    won = False

    while running:
        screen.fill(WHITE)

        for dot in dots:
            dot.draw()

        draw_lines(lines)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                if event.button == 1:  # Left click
                    pos = pygame.mouse.get_pos()
                    for dot in dots:
                        if (pos[0] - dot.x)**2 + (pos[1] - dot.y)**2 < DOT_RADIUS**2:
                            current_line = [dot.color, (dot.x, dot.y)]
                            break
            if event.type == pygame.MOUSEMOTION and current_line and not game_over:
                if current_line:
                    pos = pygame.mouse.get_pos()
                    current_line.append(pos)
            if event.type == pygame.MOUSEBUTTONUP and current_line and not game_over:
                if event.button == 1:
                    pos = pygame.mouse.get_pos()
                    for dot in dots:
                        if (pos[0] - dot.x)**2 + (pos[1] - dot.y)**2 < DOT_RADIUS**2 and dot.color == current_line[0]:
                            current_line.append((dot.x, dot.y))
                            lines.append(current_line)
                            if check_win(dots, lines):
                                won = True
                                game_over = True
                            break
                    current_line = None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and game_over:
                    dots = init_dots()
                    lines = []
                    game_over = False
                    won = False

        if current_line:
            pygame.draw.lines(screen, current_line[0], False, current_line[1:], LINE_WIDTH)

        if game_over:
            game_over_screen(won)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()