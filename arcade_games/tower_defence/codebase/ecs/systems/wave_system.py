"""
Wave System
ECS System for managing enemy waves
"""

import time
from ecs.base import System
from ecs.components import PositionComponent, EnemyComponent, HealthComponent


class WaveSystem(System):
    """System for managing waves of enemies"""
    
    def __init__(self, path_y):
        super().__init__()
        self.path_y = path_y
        self.wave = 1
        self.enemies_per_wave = 5
        self.enemies_spawned = 0
        self.enemies_killed = 0
        self.wave_cooldown = 0
        self.last_spawn = 0
        self.spawn_delay = 1.5
        self.entity_manager = None
        self.enemy_system = None
    
    def set_entity_manager(self, entity_manager):
        """Set the entity manager"""
        self.entity_manager = entity_manager
    
    def set_enemy_system(self, enemy_system):
        """Set the enemy system"""
        self.enemy_system = enemy_system
    
    def reset(self):
        """Reset wave system"""
        self.wave = 1
        self.enemies_per_wave = 5
        self.enemies_spawned = 0
        self.enemies_killed = 0
        self.wave_cooldown = 0
        self.last_spawn = 0
    
    def update(self, dt):
        """Update wave system"""
        current_time = time.time()
        
        # Handle wave cooldown
        if self.wave_cooldown > 0:
            self.wave_cooldown -= dt
            return
        
        # Spawn enemies
        if self.enemies_spawned < self.enemies_per_wave:
            if current_time - self.last_spawn >= self.spawn_delay:
                self.spawn_enemy()
                self.last_spawn = current_time
    
    def spawn_enemy(self):
        """Spawn an enemy"""
        if not self.entity_manager or not self.enemy_system:
            return
        
        # Create enemy entity
        enemy_entity = self.entity_manager.create_entity()
        
        # Add position component
        enemy_entity.add_component(PositionComponent(0, self.path_y))
        
        # Add enemy component
        enemy_entity.add_component(EnemyComponent(self.wave))
        
        # Add health component
        enemy_component = enemy_entity.get_component(EnemyComponent)
        enemy_entity.add_component(HealthComponent(enemy_component.max_health))
        
        # Add velocity component
        from ecs.components import VelocityComponent
        enemy_entity.add_component(VelocityComponent(0, 0))
        
        # Add to enemy system
        self.enemy_system.add_entity(enemy_entity)
        
        self.enemies_spawned += 1
    
    def enemy_killed(self):
        """Called when an enemy is killed"""
        self.enemies_killed += 1
    
    def check_wave_complete(self):
        """Check if wave is complete and prepare next wave"""
        # Use get_all_enemy_entities to get only alive enemies
        alive_enemies = self.enemy_system.get_all_enemy_entities() if self.enemy_system else []
        if (self.enemies_spawned >= self.enemies_per_wave and 
            len(alive_enemies) == 0 and 
            self.wave_cooldown <= 0):
            # Wave complete!
            self.wave += 1
            self.enemies_spawned = 0
            self.enemies_killed = 0
            self.enemies_per_wave = 5 + self.wave * 2
            self.wave_cooldown = 3
            return True
        return False
    
    def get_enemies_remaining(self):
        """Get number of enemies remaining in current wave"""
        return self.enemies_spawned - self.enemies_killed
    
    def get_wave_info(self):
        """Get current wave info"""
        return {
            'wave': self.wave,
            'enemies_per_wave': self.enemies_per_wave,
            'enemies_spawned': self.enemies_spawned,
            'enemies_killed': self.enemies_killed,
            'enemies_remaining': self.get_enemies_remaining()
        }
