"""
Projectile and selection box rendering for Dota2 view.
"""
import pygame
from typing import Tuple


class ProjectileRenderer:
    """Renderer for projectiles"""
    
    def __init__(self, screen):
        self.screen = screen
        self.COLOR_PROJECTILE = (255, 200, 50)
    
    def render(self, em, world_to_screen, screen_width, screen_height):
        """Render all projectiles"""
        projectiles = em.get_entities_with_component('projectile')
        
        for proj_id in projectiles:
            position = em.get_component(proj_id, 'position')
            projectile = em.get_component(proj_id, 'projectile')
            
            if not position or not projectile:
                continue
            
            screen_x, screen_y = world_to_screen(position.x, position.y)
            
            if not (-50 < screen_x < screen_width + 50 and -50 < screen_y < screen_height + 50):
                continue
            
            pygame.draw.circle(self.screen, self.COLOR_PROJECTILE, (screen_x, screen_y), 6)
            pygame.draw.circle(self.screen, (255, 255, 255), (screen_x, screen_y), 6, 1)


class SelectionBox:
    """Box selection rendering and logic"""
    
    def __init__(self):
        self.box_selection_start = None
        self.box_selection_end = None
    
    def handle_selection(self, event, screen, is_ui_click_fn) -> Tuple:
        """Handle box selection with mouse"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not is_ui_click_fn(event.pos):
                self.box_selection_start = event.pos
        
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.box_selection_start:
                self.box_selection_end = event.pos
                result = (self.box_selection_start, self.box_selection_end)
                self.box_selection_start = None
                self.box_selection_end = None
                return result
        
        elif event.type == pygame.MOUSEMOTION:
            if self.box_selection_start:
                self.box_selection_end = event.pos
        
        return (None, None)
    
    def render(self, screen):
        """Render selection box if active"""
        if self.box_selection_start and self.box_selection_end:
            x1, y1 = self.box_selection_start
            x2, y2 = self.box_selection_end
            
            rect = pygame.Rect(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
            pygame.draw.rect(screen, (100, 255, 100), rect, 2)
    
    def select_units_in_box(self, em, box_start, box_end, screen_to_world_fn):
        """Select units within box selection"""
        if not box_start or not box_end:
            return
        
        # Clear previous selection
        for entity_id in em.get_all_entities():
            selection = em.get_component(entity_id, 'selection')
            if selection:
                selection.selected = False
        
        # Get box bounds in world coordinates
        x1, y1 = screen_to_world_fn(*box_start)
        x2, y2 = screen_to_world_fn(*box_end)
        
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        
        # Select units in box
        for entity_id in em.get_all_entities():
            position = em.get_component(entity_id, 'position')
            selection = em.get_component(entity_id, 'selection')
            
            if position and selection and selection.selectable:
                if min_x <= position.x <= max_x and min_y <= position.y <= max_y:
                    selection.selected = True
