"""
Enemy System
ECS System for enemy entities
"""

import math
from ecs.base import System, EntityManager
from ecs.components import PositionComponent, EnemyComponent, VelocityComponent, HealthComponent


class EnemySystem(System):
    """System for managing enemy entities"""
    
    def __init__(self, screen_width):
        super().__init__()
        self.screen_width = screen_width
        self.entity_manager = None
    
    def set_entity_manager(self, entity_manager):
        """Set the entity manager for cross-system communication"""
        self.entity_manager = entity_manager
    
    def update(self, dt):
        """Update all enemies"""
        for entity in self.entities[:]:
            pos = entity.get_component(PositionComponent)
            enemy = entity.get_component(EnemyComponent)
            vel = entity.get_component(VelocityComponent)
            
            if pos and enemy:
                # Move enemy
                pos.x += enemy.speed
                
                # Check if off screen
                if pos.x > self.screen_width:
                    entity.destroy()
    
    def render(self, screen, pygame):
        """Render all enemies"""
        import constants
        for entity in self.entities:
            # Skip dead entities
            if not entity.alive:
                continue
            
            pos = entity.get_component(PositionComponent)
            enemy = entity.get_component(EnemyComponent)
            health = entity.get_component(HealthComponent)
            
            if pos and enemy:
                # Draw enemy body
                pygame.draw.circle(screen, constants.RED, (int(pos.x), int(pos.y)), enemy.radius)
                
                # Draw health bar
                if health:
                    bar_width = 20
                    bar_height = 4
                    bar_x = int(pos.x) - bar_width // 2
                    bar_y = int(pos.y) - 18
                    
                    # Background
                    pygame.draw.rect(screen, constants.BLACK, (bar_x, bar_y, bar_width, bar_height))
                    
                    # Health fill
                    health_pct = health.get_health_percentage()
                    health_width = int(bar_width * health_pct)
                    if health_width > 0:
                        health_color = constants.GREEN if health_pct > 0.5 else constants.YELLOW if health_pct > 0.25 else constants.RED
                        pygame.draw.rect(screen, health_color, (bar_x, bar_y, health_width, bar_height))
    
    def get_enemy_at_position(self, x, y, radius=15):
        """Get enemy at given position"""
        for entity in self.entities:
            pos = entity.get_component(PositionComponent)
            enemy = entity.get_component(EnemyComponent)
            if pos and enemy:
                dist = math.sqrt((pos.x - x)**2 + (pos.y - y)**2)
                if dist <= radius + enemy.radius:
                    return entity
        return None
    
    def get_all_enemy_entities(self):
        """Get all alive enemy entities"""
        return [e for e in self.entities if e.alive]
