"""
Car renderer for Drift King 2D.
Renders car and drift trail to pygame surface.
"""

import math
import pygame
from models.car import Car


class CarRenderer:
    """Renders car to pygame surface."""
    
    def __init__(self):
        """Initialize car renderer."""
        pass
    
    def render(self, car: Car, screen: pygame.Surface) -> None:
        """
        Render car, drift trail, and ray casting visualization.
        
        Args:
            car: Car to render
            screen: Pygame surface to draw on
        """
        self._render_rays(car, screen)  # Draw rays first (behind car)
        self._render_trail(car, screen)
        self._render_car_body(car, screen)
    
    def _render_rays(self, car: Car, screen: pygame.Surface) -> None:
        """
        Render ray casting visualization.
        Green rays = hitting track (safe)
        Red rays = hitting boundary (obstacle)
        """
        if car._track is None:
            return
        # Cast and draw rays
        car.ray_caster.cast_rays(car.x, car.y, car.angle, car._track)
        car.ray_caster.draw_rays(screen, car.x, car.y, 
                                  color_safe=(0, 255, 0),  # Green
                                  color_boundary=(255, 0, 0),  # Red
                                  line_width=1)
    
    def _render_trail(self, car: Car, screen: pygame.Surface) -> None:
        """
        Render drift trail with glow effect.
        
        Args:
            car: Car to render trail for
            screen: Pygame surface to draw on
        """
        from utils.constants import GLOW_COLORS
        
        for i, (tx, ty, t_angle) in enumerate(car.drift_trail):
            # Fade effect: brighter at car, dimmer further back
            alpha = (i + 1) / len(car.drift_trail)
            glow_color = GLOW_COLORS[min(i // 3, len(GLOW_COLORS) - 1)]
            trail_size = int(3 + alpha * 4)
            # Draw small rotated trail segment
            trail_end_x = tx + 3 * math.sin(math.radians(t_angle))
            trail_end_y = ty - 3 * math.cos(math.radians(t_angle))
            pygame.draw.line(
                screen, 
                glow_color, 
                (tx, ty), 
                (trail_end_x, trail_end_y), 
                trail_size
            )
    
    def _render_car_body(self, car: Car, screen: pygame.Surface) -> None:
        """
        Render car body as rotated rectangle.
        
        Args:
            car: Car to render
            screen: Pygame surface to draw on
        """
        from utils.constants import CAR_WIDTH, CAR_HEIGHT, RED, WHITE
        
        angle_rad = math.radians(car.angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        # Car center
        cx, cy = car.x, car.y
        
        # Calculate corner points for a rectangle
        half_w = CAR_WIDTH // 2
        half_h = CAR_HEIGHT // 2
        
        # Corners relative to center, then rotate
        corners = [
            (cx + half_w * sin_a - half_h * cos_a, cy - half_w * cos_a - half_h * sin_a),  # Front-right
            (cx + half_w * sin_a + half_h * cos_a, cy - half_w * cos_a + half_h * sin_a),  # Front-left
            (cx - half_w * sin_a + half_h * cos_a, cy + half_w * cos_a + half_h * sin_a),  # Back-left
            (cx - half_w * sin_a - half_h * cos_a, cy + half_w * cos_a - half_h * sin_a),  # Back-right
        ]
        
        # Draw car body
        pygame.draw.polygon(screen, RED, corners)
        # Add car outline
        pygame.draw.polygon(screen, WHITE, corners, 2)
