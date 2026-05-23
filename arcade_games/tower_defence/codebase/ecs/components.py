"""
ECS Components
"""

import math
from ecs.base import Component


class PositionComponent(Component):
    """Position component for all entities"""
    
    def __init__(self, x, y):
        super().__init__()
        self.x = x
        self.y = y


class EnemyComponent(Component):
    """Enemy component with health, speed, and wave info"""
    
    def __init__(self, wave_num=1):
        super().__init__()
        # Health scales with wave number
        self.max_health = 20 + (wave_num * 10)
        self.health = self.max_health
        # Speed increases slightly with waves
        self.speed = 2 + (wave_num * 0.2)
        self.wave = wave_num
        self.radius = 10


class TowerComponent(Component):
    """Tower component with type, range, and cooldown"""
    
    def __init__(self, tower_type, config):
        super().__init__()
        self.tower_type = tower_type
        self.config = config
        self.range = config['range']
        self.color = config['color']
        self.cooldown = config['cooldown']
        self.damage = config['damage']
        self.last_shot = 0
        self.selected = False
        self.radius = 15


class BulletComponent(Component):
    """Bullet component with target, speed, and damage"""
    
    def __init__(self, target_entity, config):
        super().__init__()
        self.target_entity = target_entity
        self.config = config
        self.color = config['bullet_color']
        self.size = config['bullet_size']
        self.damage = config['damage']
        self.speed = 5
        self.vx = 0
        self.vy = 0


class VelocityComponent(Component):
    """Velocity component for moving entities"""
    
    def __init__(self, vx=0, vy=0):
        super().__init__()
        self.vx = vx
        self.vy = vy


class HealthComponent(Component):
    """Health component for entities that can take damage"""
    
    def __init__(self, max_health):
        super().__init__()
        self.max_health = max_health
        self.health = max_health
    
    def take_damage(self, damage):
        """Apply damage and return True if dead"""
        self.health -= damage
        return self.health <= 0
    
    def get_health_percentage(self):
        """Get health as percentage"""
        return self.health / self.max_health if self.max_health > 0 else 0
