"""
Camera and coordinate conversion utilities for Dota2 view.
"""
import pygame
from typing import Tuple


class Camera:
    """Camera system for world-to-screen coordinate conversion"""
    
    def __init__(self, screen, config, map_width: int, map_height: int):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.map_width = map_width
        self.map_height = map_height
        
        # Camera position
        self.camera_x = 200
        self.camera_y = 200
        
        # Drag state
        self.camera_dragging = False
        self.drag_start_pos = None
        self.drag_start_camera = None
    
    def handle_mouse_drag(self, event) -> bool:
        """Handle camera dragging with middle mouse button. Returns True if handled."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2:
            self.camera_dragging = True
            self.drag_start_pos = event.pos
            self.drag_start_camera = (self.camera_x, self.camera_y)
            return True
        
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 2:
            self.camera_dragging = False
            return True
        
        elif event.type == pygame.MOUSEMOTION and self.camera_dragging:
            dx = self.drag_start_pos[0] - event.pos[0]
            dy = self.drag_start_pos[1] - event.pos[1]
            
            self.camera_x = self.drag_start_camera[0] + dx
            self.camera_y = self.drag_start_camera[1] + dy
            
            # Clamp camera
            self.camera_x = max(0, min(self.map_width - self.width, self.camera_x))
            self.camera_y = max(0, min(self.map_height - self.height, self.camera_y))
            return True
        
        return False
    
    def world_to_screen(self, world_x: float, world_y: float) -> Tuple[int, int]:
        """Convert world coordinates to screen coordinates"""
        screen_x = int(world_x - self.camera_x)
        screen_y = int(world_y - self.camera_y)
        return (screen_x, screen_y)
    
    def screen_to_world(self, screen_x: int, screen_y: int) -> Tuple[float, float]:
        """Convert screen coordinates to world coordinates"""
        world_x = screen_x + self.camera_x
        world_y = screen_y + self.camera_y
        return (world_x, world_y)
    
    def is_on_screen(self, world_x: float, world_y: float, margin: int = 100) -> bool:
        """Check if a world position is visible on screen"""
        screen_x, screen_y = self.world_to_screen(world_x, world_y)
        return (-margin <= screen_x <= self.width + margin and
                -margin <= screen_y <= self.height + margin)

    def update_edge_panning(self, mouse_x: int, mouse_y: int, dt: float, pan_speed: float = 1000.0, edge_threshold: int = 0):
        """Update camera position based on mouse near screen edges"""
        pan_x = 0
        pan_y = 0

        if mouse_x <= edge_threshold:
            pan_x = -pan_speed * dt
        elif mouse_x >= self.width - 1 - edge_threshold:
            pan_x = pan_speed * dt

        if mouse_y <= edge_threshold:
            pan_y = -pan_speed * dt
        elif mouse_y >= self.height - 1 - edge_threshold:
            pan_y = pan_speed * dt

        if pan_x != 0 or pan_y != 0:
            self.camera_x += pan_x
            self.camera_y += pan_y

            # Clamp camera
            self.camera_x = max(0, min(self.map_width - self.width, self.camera_x))
            self.camera_y = max(0, min(self.map_height - self.height, self.camera_y))


class Minimap:
    """Minimap coordinate conversion and utilities"""
    
    def __init__(self, screen, map_width: int, map_height: int, size: int = 180):
        self.screen = screen
        self.minimap_size = size
        self.minimap_x = screen.get_width() - size - 10
        self.minimap_y = screen.get_height() - size - 10
        self.minimap_scale = size / max(map_width, map_height)
    
    def world_to_minimap(self, world_x: float, world_y: float) -> Tuple[int, int]:
        """Convert world coordinates to minimap coordinates"""
        mini_x = int(self.minimap_x + world_x * self.minimap_scale)
        mini_y = int(self.minimap_y + world_y * self.minimap_scale)
        return (mini_x, mini_y)
    
    def minimap_to_world(self, mini_x: int, mini_y: int) -> Tuple[float, float]:
        """Convert minimap coordinates to world coordinates"""
        world_x = (mini_x - self.minimap_x) / self.minimap_scale
        world_y = (mini_y - self.minimap_y) / self.minimap_scale
        return (world_x, world_y)
    
    def is_in_minimap(self, x: int, y: int) -> bool:
        """Check if point is inside minimap"""
        return (self.minimap_x <= x <= self.minimap_x + self.minimap_size and
                self.minimap_y <= y <= self.minimap_y + self.minimap_size)
    
    def get_viewport_rect(self, camera_x: float, camera_y: float, screen_width: int, screen_height: int):
        """Get minimap viewport rectangle"""
        viewport_mini_x = int(self.minimap_x + camera_x * self.minimap_scale)
        viewport_mini_y = int(self.minimap_y + camera_y * self.minimap_scale)
        viewport_mini_w = int(screen_width * self.minimap_scale)
        viewport_mini_h = int(screen_height * self.minimap_scale)
        return (viewport_mini_x, viewport_mini_y, viewport_mini_w, viewport_mini_h)
