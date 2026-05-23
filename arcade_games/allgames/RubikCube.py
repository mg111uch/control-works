import pygame
import copy

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
ORANGE = (255, 165, 0)

CELL_SIZE = 30
FACE_SIZE = 3

# Colors for faces
FACE_COLORS = [WHITE, YELLOW, GREEN, BLUE, RED, ORANGE]

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Rubik's Cube")

clock = pygame.time.Clock()

def init_cube():
    cube = []
    for i in range(6):
        face = [[FACE_COLORS[i]] * FACE_SIZE for _ in range(FACE_SIZE)]
        cube.append(face)
    return cube

def rotate_face(cube, face_idx, clockwise=True):
    # Rotate the face itself
    face = cube[face_idx]
    if clockwise:
        face[:] = [list(reversed(col)) for col in zip(*face)]
    else:
        face[:] = [list(col) for col in zip(*face[::-1])]

    # Update adjacent faces - simplified for front face only
    if face_idx == 0:  # Front
        if clockwise:
            temp = [cube[1][i][0] for i in range(FACE_SIZE)]
            for i in range(FACE_SIZE):
                cube[1][i][0] = cube[4][FACE_SIZE-1-i][FACE_SIZE-1]
            for i in range(FACE_SIZE):
                cube[4][FACE_SIZE-1-i][FACE_SIZE-1] = cube[3][FACE_SIZE-1-i][0]
            for i in range(FACE_SIZE):
                cube[3][FACE_SIZE-1-i][0] = cube[5][i][0]
            for i in range(FACE_SIZE):
                cube[5][i][0] = temp[i]
        else:
            temp = [cube[1][i][0] for i in range(FACE_SIZE)]
            for i in range(FACE_SIZE):
                cube[1][i][0] = cube[5][i][0]
            for i in range(FACE_SIZE):
                cube[5][i][0] = cube[3][FACE_SIZE-1-i][0]
            for i in range(FACE_SIZE):
                cube[3][FACE_SIZE-1-i][0] = cube[4][FACE_SIZE-1-i][FACE_SIZE-1]
            for i in range(FACE_SIZE):
                cube[4][FACE_SIZE-1-i][FACE_SIZE-1] = temp[i]

def draw_cube(cube):
    # Draw net: front, right, left, top, bottom
    positions = [
        (300, 200),  # front
        (450, 200),  # right
        (150, 200),  # left
        (300, 50),   # top
        (300, 350),  # bottom
    ]
    for idx, pos in enumerate(positions):
        for i in range(FACE_SIZE):
            for j in range(FACE_SIZE):
                x = pos[0] + j * CELL_SIZE
                y = pos[1] + i * CELL_SIZE
                pygame.draw.rect(screen, cube[idx][i][j], (x, y, CELL_SIZE, CELL_SIZE))
                pygame.draw.rect(screen, BLACK, (x, y, CELL_SIZE, CELL_SIZE), 1)

def is_solved(cube):
    for face in cube:
        color = face[0][0]
        if not all(cell == color for row in face for cell in row):
            return False
    return True

def main():
    cube = init_cube()
    running = True

    while running:
        screen.fill(WHITE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    rotate_face(cube, 0, True)  # Rotate front clockwise
                elif event.key == pygame.K_e:
                    rotate_face(cube, 0, False)  # Rotate front counter-clockwise

        draw_cube(cube)

        if is_solved(cube):
            font = pygame.font.SysFont(None, 48)
            text = font.render("Solved!", True, GREEN)
            screen.blit(text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()