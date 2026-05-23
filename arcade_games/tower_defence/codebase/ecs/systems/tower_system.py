"""
Tower System
ECS System for tower entities
"""

import math
import time
from ecs.base import System
from ecs.components import PositionComponent, TowerComponent


class TowerSystem(System):
    """System for managing tower entities"""
    
    def __init__(self):
        super().__init__()
        self.bullet_system = None
        self.entity_manager = None
    
    def set_entity_manager(self, entity_manager):
        """Set the entity manager"""
        self.entity_manager = entity_manager
    
    def set_bullet_system(self, bullet_system):
        """Set the bullet system for creating bullets"""
        self.bullet_system = bullet_system
    
    def update(self, dt, enemy_entities):
        """Update all towers - find targets and shoot"""
        current_time = time.time()
        
        for tower_entity in self.entities:
            tower = tower_entity.get_component(TowerComponent)
            pos = tower_entity.get_component(PositionComponent)
            
            if not tower or not pos:
                continue
            
            # Find enemies in range
            for enemy_entity in enemy_entities:
                enemy_pos = enemy_entity.get_component(PositionComponent)
                if not enemy_pos:
                    continue
                
                # Check if enemy is in range
                dist = math.sqrt((pos.x - enemy_pos.x)**2 + (pos.y - enemy_pos.y)**2)
                
                if dist <= tower.range:
                    # Check cooldown
                    if current_time - tower.last_shot >= tower.cooldown:
                        # Shoot!
                        if self.bullet_system:
                            self.bullet_system.create_bullet(tower_entity, enemy_entity, self.entity_manager)
                        tower.last_shot = current_time
                        break  # Only shoot one enemy per frame
    
    def render(self, screen, pygame):
        """Render all towers"""
        import constants
        for entity in self.entities:
            pos = entity.get_component(PositionComponent)
            tower = entity.get_component(TowerComponent)
            
            if pos and tower:
                # Draw tower body
                pygame.draw.circle(screen, tower.color, (int(pos.x), int(pos.y)), tower.radius)
                
                # Draw range circle if selected
                if tower.selected:
                    pygame.draw.circle(screen, constants.BLACK, (int(pos.x), int(pos.y)), tower.range, 1)
    
    def get_tower_at_position(self, x, y):
        """Get tower at given position"""
        for entity in self.entities:
            pos = entity.get_component(PositionComponent)
            tower = entity.get_component(TowerComponent)
            if pos and tower:
                dist = math.sqrt((pos.x - x)**2 + (pos.y - y)**2)
                if dist <= tower.radius:
                    return entity
        return None
    
    def deselect_all(self):
        """Deselect all towers"""
        for entity in self.entities:
            tower = entity.get_component(TowerComponent)
            if tower:
                tower.selected = False
    
    def select_tower(self, entity):
        """Select a tower"""
        tower = entity.get_component(TowerComponent)
        if tower:
            self.deselect_all()
            tower.selected = True
    
    def can_place_tower(self, x, y, existing_towers):
        """Check if a tower can be placed at position"""
        # Check distance to other towers
        for tower_entity in existing_towers:
            pos = tower_entity.get_component(PositionComponent)
            if pos:
                dist = math.sqrt((pos.x - x)**2 + (pos.y - y)**2)
                if dist < 30:  # Minimum distance between towers
                    return False
        return True
