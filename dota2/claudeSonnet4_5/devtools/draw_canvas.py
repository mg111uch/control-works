import pygame
from pygame.locals import *
import os

# Initialize Pygame
os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"
pygame.init()
pygame.font.init()
font = pygame.font.SysFont(None, 24)
tools = ["Line", "Polygon", "Color", "Erase", "Circle", "Toggle Image", "Select", "Save"]
current_tool = "Polygon"

# Set up the display
WIDTH, HEIGHT = 1300, 800
SIDEBAR_WIDTH = 300
CANVAS_WIDTH = WIDTH - SIDEBAR_WIDTH
CANVAS_SIZE = 720
CANVAS_X = SIDEBAR_WIDTH + (CANVAS_WIDTH - CANVAS_SIZE) // 2
CANVAS_Y = (HEIGHT - CANVAS_SIZE) // 2
CANVAS_RECT = pygame.Rect(CANVAS_X, CANVAS_Y, CANVAS_SIZE, CANVAS_SIZE)
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Draw Irregular Shapes by Clicking")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)  # For optional filled shape
colors = [WHITE, (255,0,0), (0,255,0), (0,0,255), (255,255,0)]
current_color = WHITE
color_index = 0
selected_color = BLACK
r_text = str(current_color[0])
g_text = str(current_color[1])
b_text = str(current_color[2])
active_input = None
save_path = "polygons.txt"

# List to hold shapes
shapes = []
current_shape = []
drag_point = None
selection_start = None
selection_end = None
selected_shapes = set()
# List to hold line points
points = []
loaded_image = None
show_image = True
image_path = "/home/manigupt/Hello/python/dota2/claudeSonnet4_5/dota2_gym/assets/minimap.png"  # Path to the image to load

def load_image(path):
    global loaded_image
    loaded_image = pygame.image.load(path)
    loaded_image = pygame.transform.scale(loaded_image, (CANVAS_SIZE, CANVAS_SIZE))

load_image(image_path)

def save_polygons():
    with open(save_path, 'w') as f:
        for shape in shapes:
            f.write(' '.join(f"{p[0] - CANVAS_X},{p[1] - CANVAS_Y}" for p in shape) + '\n')

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        elif event.type == MOUSEMOTION:
            if drag_point:
                shapes[drag_point[0]][drag_point[1]] = event.pos
            elif selection_start and current_tool == "Select":
                selection_end = event.pos
        elif event.type == MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                if event.pos[0] < SIDEBAR_WIDTH:
                    # Sidebar click
                    button_width = 80
                    button_height = 40
                    margin = 10
                    cols = 3
                    rows = 3
                    col = (event.pos[0] - margin) // (button_width + margin)
                    row = (event.pos[1] - margin) // (button_height + margin)
                    if 0 <= col < cols and 0 <= row < rows:
                        index = row * cols + col
                        if index < len(tools):
                            if tools[index] == "Toggle Image":
                                show_image = not show_image
                            elif tools[index] == "Save":
                                save_polygons()
                            else:
                                current_tool = tools[index]
                        elif index == 2:  # R
                            active_input = "r"
                        elif index == 5:  # G
                            active_input = "g"
                        elif index == 8:  # B
                            active_input = "b"
                        else:
                            active_input = None
                    # Check color selection boxes
                    color_box_y = 10 + 3 * (40 + 10)
                    color_box_width = 80
                    color_box_height = 40
                    if 10 <= event.pos[0] <= 10 + color_box_width and color_box_y <= event.pos[1] <= color_box_y + color_box_height:
                        selected_color = BLACK
                    elif 10 + color_box_width + 10 <= event.pos[0] <= 10 + 2*color_box_width + 10 and color_box_y <= event.pos[1] <= color_box_y + color_box_height:
                        selected_color = WHITE
                else:
                    # Canvas click
                    if CANVAS_RECT.collidepoint(event.pos):
                        if current_tool == "Select":
                            if not selection_start:
                                selection_start = event.pos
                            else:
                                selection_end = event.pos
                                rect = pygame.Rect(min(selection_start[0], selection_end[0]), min(selection_start[1], selection_end[1]), abs(selection_end[0] - selection_start[0]), abs(selection_end[1] - selection_start[1]))
                                selected_shapes = {i for i, shape in enumerate(shapes) if all(rect.collidepoint(p) for p in shape)}
                                selection_start = None
                                selection_end = None
                        else:
                            # Check for vertex drag
                            drag_point = None
                            for i, shape in enumerate(shapes):
                                for j, p in enumerate(shape):
                                    if (event.pos[0] - p[0])**2 + (event.pos[1] - p[1])**2 < 100:
                                        drag_point = (i, j)
                                        break
                                if drag_point:
                                    break
                            if not drag_point:
                                if current_tool == "Polygon":
                                    current_shape.append(event.pos)
                                elif current_tool == "Line":
                                    if len(points) < 2:
                                        points.append(event.pos)
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                running = False
            elif event.key == K_c:  # Press 'c' to clear points
                points = []
            elif event.key == K_f:  # Press 'f' to finish/close and start new (optional)
                if current_shape:
                    shapes.append(current_shape[:])
                    current_shape = []
                points = []
            # Handle RGB input
            if active_input:
                if event.key == K_BACKSPACE:
                    if active_input == "r":
                        r_text = r_text[:-1]
                    elif active_input == "g":
                        g_text = g_text[:-1]
                    elif active_input == "b":
                        b_text = b_text[:-1]
                elif event.key == K_RETURN:
                    active_input = None
                else:
                    char = event.unicode
                    if char.isdigit():
                        if active_input == "r":
                            r_text += char
                        elif active_input == "g":
                            g_text += char
                        elif active_input == "b":
                            b_text += char
                # Update color
                try:
                    r = int(r_text) if r_text else 0
                    g = int(g_text) if g_text else 0
                    b = int(b_text) if b_text else 0
                    current_color = (r, g, b)
                except ValueError:
                    pass

    # Clear screen
    screen.fill(BLACK)

    # Draw sidebar
    pygame.draw.rect(screen, (50, 50, 50), (0, 0, SIDEBAR_WIDTH, HEIGHT))

    # Draw canvas
    pygame.draw.rect(screen, WHITE, CANVAS_RECT)

    # Draw loaded image
    if show_image and loaded_image:
        screen.blit(loaded_image, (CANVAS_X, CANVAS_Y))

    # Draw buttons
    button_width = 80
    button_height = 40
    margin = 10
    cols = 3
    rows = 3
    for i in range(rows):
        for j in range(cols):
            index = i * cols + j
            x = margin + j * (button_width + margin)
            y = margin + i * (button_height + margin)
            if index < len(tools):
                color = (100, 100, 100)
                if tools[index] == current_tool or (tools[index] == "Toggle Image" and show_image):
                    color = (150, 150, 150)
                pygame.draw.rect(screen, color, (x, y, button_width, button_height))
                tool_name = tools[index]
                if tool_name == "Color":
                    pygame.draw.rect(screen, current_color, (x + button_width - 20, y + button_height - 20, 15, 15))
                text = font.render(tool_name, True, WHITE)
                screen.blit(text, (x + 5, y + 10))
            elif index == 2:  # R
                color = (100, 100, 100)
                if active_input == "r":
                    color = (150, 150, 150)
                pygame.draw.rect(screen, color, (x, y, button_width, button_height))
                text = font.render("R: " + r_text, True, WHITE)
                screen.blit(text, (x + 5, y + 10))
            elif index == 5:  # G
                color = (100, 100, 100)
                if active_input == "g":
                    color = (150, 150, 150)
                pygame.draw.rect(screen, color, (x, y, button_width, button_height))
                text = font.render("G: " + g_text, True, WHITE)
                screen.blit(text, (x + 5, y + 10))
            elif index == 8:  # B
                color = (100, 100, 100)
                if active_input == "b":
                    color = (150, 150, 150)
                pygame.draw.rect(screen, color, (x, y, button_width, button_height))
                text = font.render("B: " + b_text, True, WHITE)
                screen.blit(text, (x + 5, y + 10))

    # Draw color selection boxes
    color_box_y = 10 + 3 * (40 + 10)
    color_box_width = 80
    color_box_height = 40
    # Black
    pygame.draw.rect(screen, BLACK, (10, color_box_y, color_box_width, color_box_height))
    if selected_color == BLACK:
        pygame.draw.rect(screen, (150, 150, 150), (10, color_box_y, color_box_width, color_box_height), 3)
    # White
    pygame.draw.rect(screen, WHITE, (10 + color_box_width + 10, color_box_y, color_box_width, color_box_height))
    if selected_color == WHITE:
        pygame.draw.rect(screen, (150, 150, 150), (10 + color_box_width + 10, color_box_y, color_box_width, color_box_height), 3)

    # Draw selection box
    if selection_start and selection_end:
        rect = pygame.Rect(min(selection_start[0], selection_end[0]), min(selection_start[1], selection_end[1]), abs(selection_end[0] - selection_start[0]), abs(selection_end[1] - selection_start[1]))
        pygame.draw.rect(screen, GREEN, rect, 1)

    # Draw on canvas
    # Draw completed shapes
    for i, shape in enumerate(shapes):
        color = selected_color
        if i in selected_shapes:
            color = GREEN
        if len(shape) > 1:
            pygame.draw.lines(screen, color, False, shape, 2)
            if len(shape) >= 3:
                pygame.draw.polygon(screen, color, shape, 2)
        # Draw vertex circles
        for p in shape:
            pygame.draw.circle(screen, (255, 0, 0), p, 5)
    # Draw current shape
    if len(current_shape) > 1:
        pygame.draw.lines(screen, selected_color, False, current_shape, 2)
        if len(current_shape) >= 3:
            pygame.draw.polygon(screen, selected_color, current_shape, 2)
    # Draw vertex circles for current
    for p in current_shape:
        pygame.draw.circle(screen, (255, 0, 0), p, 5)
    # Draw line
    if current_tool == "Line" and len(points) == 2:
        pygame.draw.line(screen, selected_color, points[0], points[1], 2)

    # Update display
    pygame.display.flip()

# Quit Pygame
pygame.quit()