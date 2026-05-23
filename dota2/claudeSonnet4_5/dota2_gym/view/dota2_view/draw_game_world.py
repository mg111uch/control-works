import pygame
import os

# Colors based on your UI specification
COLOR_LOW_GROUND = (12, 25, 30)    # Dark Areas
COLOR_HIGH_GROUND = (25, 65, 75)   # Light Areas (Polygons)
COLOR_RIVER = (35, 85, 120)       # River
COLOR_VIEWPORT = (255, 255, 0)    # Yellow Viewport
COLOR_STAIRS = (60, 80, 90)       # Greyish blue for stairs

polygon_file = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'map_polygons.txt')

def draw_staircase(world_surface, p1, p2):
    """Draws a staircase with increasing thickness perpendicular to the line from p1 to p2."""
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = (dx**2 + dy**2)**0.5
    if length == 0:
        return
    ux = dx / length
    uy = dy / length
    px = -uy
    py = ux
    t1 = 150  # thickness at p1
    t2 = 150  # thickness at p2
    p1_left = (p1[0] + (t1 / 2) * px, p1[1] + (t1 / 2) * py)
    p1_right = (p1[0] - (t1 / 2) * px, p1[1] - (t1 / 2) * py)
    p2_left = (p2[0] + (t2 / 2) * px, p2[1] + (t2 / 2) * py)
    p2_right = (p2[0] - (t2 / 2) * px, p2[1] - (t2 / 2) * py)
    points = [p1_left, p1_right, p2_right, p2_left]
    pygame.draw.polygon(world_surface, COLOR_STAIRS, points)

def generate_world_map(world_surface):
    """Generate the detailed world map from polygons"""
    # 1. Background (Low Ground)
    world_surface.fill(COLOR_LOW_GROUND)

    # 2. Read and draw polygons from file, scaled 10x
    font = pygame.font.SysFont(None, 36)
    try:
        with open(polygon_file, 'r') as f:
            lines = f.readlines()
            i = 0
            while i < len(lines):
                name = lines[i].strip()
                i += 1
                if name == "Stairs":
                    # parse stairs
                    while i < len(lines):
                        points_str = lines[i].strip()
                        i += 1
                        if not points_str:
                            continue
                        parts = points_str.split()
                        if len(parts) == 3:
                            name = parts[0]
                            p1_str = parts[1]
                            p2_str = parts[2]
                            p1 = tuple(map(float, p1_str.split(',')))
                            p2 = tuple(map(float, p2_str.split(',')))
                            p1_scaled = (p1[0]*10, p1[1]*10)
                            p2_scaled = (p2[0]*10, p2[1]*10)
                            draw_staircase(world_surface, p1_scaled, p2_scaled)
                            # Draw name on stair
                            cx = (p1_scaled[0] + p2_scaled[0]) / 2
                            cy = (p1_scaled[1] + p2_scaled[1]) / 2
                            text = font.render(name, True, (255, 255, 255))
                            world_surface.blit(text, (cx - text.get_width() // 2, cy - text.get_height() // 2))
                    break
                else:
                    # draw polygon
                    if i < len(lines):
                        points = []
                        for pair in lines[i].strip().split():
                            if pair:
                                x, y = map(float, pair.split(','))
                                scaled_x, scaled_y = x * 10, y * 10
                                points.append((scaled_x, scaled_y))
                        if len(points) >= 3:
                            if "River" in name:
                                draw_color = COLOR_RIVER
                            elif "high_ground" in name:
                                draw_color = COLOR_HIGH_GROUND
                            else:
                                draw_color = COLOR_HIGH_GROUND
                            pygame.draw.polygon(world_surface, draw_color, points)
                            pygame.draw.polygon(world_surface, (255, 255, 255), points, 2)
                            cx = sum(x for x, y in points) / len(points)
                            cy = sum(y for x, y in points) / len(points) + 50
                            text = font.render(name, True, (255, 255, 255))
                            world_surface.blit(text, (cx - text.get_width() // 2, cy - text.get_height() // 2))
                    i += 1
    except FileNotFoundError:
        print(f"Error: File not found at {polygon_file}")
    except Exception as e:
        print(f"Error processing polygons: {e}")

