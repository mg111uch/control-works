import pygame
import re
import itertools
import sys

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (135, 206, 235)
YELLOW = (255, 255, 0)
GREEN = (0, 128, 0)
GRAY = (128, 128, 128)
RED = (255, 0, 0)

FONT = pygame.font.SysFont(None, 36)
SMALL_FONT = pygame.font.SysFont(None, 24)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Alphametics Solver")

clock = pygame.time.Clock()

def solve(puzzle):
    words = re.findall('[A-Z]+', puzzle.upper())
    unique_characters = set(''.join(words))
    if len(unique_characters) > 10:
        return None
    first_letters = {word[0] for word in words}
    n = len(first_letters)
    sorted_characters = ''.join(first_letters) + \
        ''.join(unique_characters - first_letters)
    characters = tuple(ord(c) for c in sorted_characters)
    digits = tuple(ord(c) for c in '0123456789')
    zero = digits[0]
    for guess in itertools.permutations(digits, len(characters)):
        if zero not in guess[:n]:
            equation = puzzle.translate(dict(zip(characters, guess)))
            try:
                if eval(equation):
                    return equation
            except:
                pass
    return None

class TextInput:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = ""
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = True
            else:
                self.active = False
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                self.active = False
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode

    def draw(self, screen):
        color = YELLOW if self.active else GRAY
        pygame.draw.rect(screen, color, self.rect, 2)
        txt_surface = FONT.render(self.text, True, BLACK)
        screen.blit(txt_surface, (self.rect.x + 5, self.rect.y + 5))

def main():
    input_box = TextInput(50, 50, 500, 40)
    solve_button = pygame.Rect(600, 50, 100, 40)
    result = ""
    running = True

    while running:
        screen.fill(WHITE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            input_box.handle_event(event)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if solve_button.collidepoint(event.pos):
                    puzzle = input_box.text
                    solution = solve(puzzle)
                    if solution:
                        result = solution
                    else:
                        result = "No solution found"

        input_box.draw(screen)
        pygame.draw.rect(screen, GRAY, solve_button)
        solve_text = SMALL_FONT.render("Solve", True, BLACK)
        screen.blit(solve_text, (solve_button.x + 20, solve_button.y + 10))

        if result:
            result_surface = FONT.render(result, True, GREEN)
            screen.blit(result_surface, (50, 120))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()