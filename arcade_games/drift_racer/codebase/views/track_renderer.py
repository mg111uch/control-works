"""
Track renderer for Drift King 2D.
Renders track elements to pygame surface.
"""

import pygame
from typing import Optional
from models.track import Track, TrackElement


class TrackRenderer:
    """Renders track to pygame surface."""
    
    def __init__(self, screen: pygame.Surface):
        """
        Initialize track renderer.
        
        Args:
            screen: Pygame surface to render to
        """
        self.screen = screen
    
    def render(self, track: Track) -> None:
        """
        Render entire track.
        
        Args:
            track: Track to render
        """
        # Fill background
        self.screen.fill(track.background_color)
        
        # Render all track elements FIRST (start line goes on top)
        for element in track.elements:
            self._render_element(element)
        
        # Render start/finish line AFTER track elements (so it's visible on top)
        if hasattr(track, 'start_finish_line'):
            self._render_start_finish_line(track.start_finish_line)
    
    def _render_element(self, element: TrackElement) -> None:
        """
        Render single track element.
        
        Args:
            element: Track element to render
        """
        if element.type == 'ellipse':
            pygame.draw.ellipse(
                self.screen, 
                element.color, 
                element.rect
            )
            # Draw border
            pygame.draw.ellipse(
                self.screen,
                (255, 255, 255),  # White border
                element.rect,
                element.border_width
            )
        elif element.type == 'rectangle':
            # Calculate rect from center and dimensions
            rect = pygame.Rect(
                element.center_x - element.width // 2,
                element.center_y - element.height // 2,
                element.width,
                element.height
            )
            pygame.draw.rect(
                self.screen,
                element.color,
                rect
            )
            pygame.draw.rect(
                self.screen,
                (255, 255, 255),
                rect,
                element.border_width
            )
    
    def _render_start_finish_line(self, line) -> None:
        """
        Render start/finish line.
        
        Args:
            line: StartFinishLine to render
        """
        import math
        # The line angle is perpendicular to the car direction
        # Endpoints should be calculated along the line angle
        angle_rad = math.radians(line.angle)
        half_width = line.width / 2
        
        # Calculate endpoints along the line direction
        end_x1 = line.x + math.cos(angle_rad) * half_width
        end_y1 = line.y + math.sin(angle_rad) * half_width
        end_x2 = line.x - math.cos(angle_rad) * half_width
        end_y2 = line.y - math.sin(angle_rad) * half_width
        
        # Draw checkered line (white with black dashes) - thickness reduced to 2
        pygame.draw.line(
            self.screen,
            (255, 255, 255),
            (end_x1, end_y1),
            (end_x2, end_y2),
            2
        )
        
        # Draw center dot
        pygame.draw.circle(
            self.screen,
            (255, 0, 0),
            (int(line.x), int(line.y)),
            5
        )
    
    def draw_start_line(self, x: float, y: float, width: float = 100) -> None:
        """
        Draw start/finish line.
        
        Args:
            x: X position of line
            y: Y position of line
            width: Width of line
        """
        pygame.draw.line(
            self.screen,
            (255, 255, 255),
            (x, y),
            (x + width, y),
            2
        )
