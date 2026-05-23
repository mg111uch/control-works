"""
Bullet System
ECS System for bullet entities
"""

import math
from ecs.base import System
from ecs.components import PositionComponent, BulletComponent, VelocityComponent, EnemyComponent


class BulletSystem(System):
    """System for managing bullet entities"""
    
    def __init__(self, screen_width, screen_height):
        super().__init__()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.enemy_system = None
    
    def set_enemy_system(self, enemy_system):
        """Set the enemy system for collision detection"""
        self.enemy_system = enemy_system
    
    def create_bullet(self, tower_entity, target_entity, entity_manager):
        """Create a bullet from tower to target"""
        from ecs.components import PositionComponent, TowerComponent
        
        tower_pos = tower_entity.get_component(PositionComponent)
        tower = tower_entity.get_component(TowerComponent)
        
        if not tower_pos or not tower:
            return None
        
        # Create bullet entity
        bullet_entity = entity_manager.create_entity()
        
        # Add position component
        bullet_entity.add_component(PositionComponent(tower_pos.x, tower_pos.y))
        
        # Add bullet component
        bullet_component = BulletComponent(target_entity, tower.config)
        bullet_entity.add_component(bullet_component)
        
        # Add velocity component (will be updated in update())
        bullet_entity.add_component(VelocityComponent(0, 0))
        
        # Add to system
        self.add_entity(bullet_entity)
        
        return bullet_entity
    
    def update(self, dt):
        """Update all bullets"""
        # Create a copy of entities list to avoid modification during iteration
        for bullet_entity in self.entities[:]:
            # Skip dead bullets
            if not bullet_entity.alive:
                continue
            
            pos = bullet_entity.get_component(PositionComponent)
            bullet = bullet_entity.get_component(BulletComponent)
            vel = bullet_entity.get_component(VelocityComponent)
            
            if not pos or not bullet or not vel:
                continue
            
            # Get target enemy
            target_entity = bullet.target_entity
            
            # Check if target is still alive
            if not target_entity or not target_entity.alive:
                bullet_entity.destroy()
                continue
            
            target_pos = target_entity.get_component(PositionComponent)
            if not target_pos:
                bullet_entity.destroy()
                continue
            
            # Update velocity to track target
            dx = target_pos.x - pos.x
            dy = target_pos.y - pos.y
            dist = math.sqrt(dx**2 + dy**2)
            
            if dist > 0:
                vel.vx = bullet.speed * dx / dist
                vel.vy = bullet.speed * dy / dist
            
            # Move bullet (use velocity directly for now, dt is 1/60)
            pos.x += vel.vx
            pos.y += vel.vy
            
            # Check collision with target - use enemy_component directly
            enemy_component = target_entity.get_component(EnemyComponent)
            if enemy_component:
                radius = enemy_component.radius
                dist = math.sqrt((pos.x - target_pos.x)**2 + (pos.y - target_pos.y)**2)
                
                if dist < (radius + bullet.size):
                    # Hit! Apply damage
                    from ecs.components import HealthComponent
                    health = target_entity.get_component(HealthComponent)
                    if health and health.take_damage(bullet.damage):
                        target_entity.destroy()
                    
                    bullet_entity.destroy()
                    continue
            
            # Check if off screen
            if (pos.x < 0 or pos.x > self.screen_width or 
                pos.y < 0 or pos.y > self.screen_height):
                bullet_entity.destroy()
    
    def render(self, screen, pygame):
        """Render all bullets"""
        for entity in self.entities:
            # Skip dead entities
            if not entity.alive:
                continue
            
            pos = entity.get_component(PositionComponent)
            bullet = entity.get_component(BulletComponent)
            
            if pos and bullet:
                pygame.draw.circle(screen, bullet.color, (int(pos.x), int(pos.y)), bullet.size)
