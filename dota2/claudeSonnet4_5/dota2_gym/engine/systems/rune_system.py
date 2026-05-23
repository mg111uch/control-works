import numpy as np
from dataclasses import dataclass

@dataclass
class RuneComponent:
    """Power rune component"""
    rune_type: str  # 'haste', 'double_damage', 'regen', 'invis', 'illusion'
    spawn_time: float
    duration: float = 45.0  # Rune lasts 45 seconds on ground

class RuneSystem:
    """Power rune spawning and pickup"""
    
    def __init__(self, entity_manager):
        self.em = entity_manager
        self.spawn_interval = 120.0  # 2 minutes
        self.last_spawn_time = -120.0
        
        # Rune spawn positions (simplified - river spots)
        self.spawn_positions = [
            (3600, 2000),  # Top rune
            (3600, 5400)   # Bottom rune
        ]
        
        self.rune_types = ['haste', 'double_damage', 'regen', 'invis', 'illusion']
    
    def update(self, game_time: float):
        """Check if it's time to spawn runes"""
        if game_time - self.last_spawn_time >= self.spawn_interval:
            for pos in self.spawn_positions:
                self.spawn_rune(pos[0], pos[1], game_time)
            self.last_spawn_time = game_time
    
    def spawn_rune(self, x: float, y: float, game_time: float):
        """Spawn a random rune"""
        from engine.ecs.components import PositionComponent, CollisionComponent
        
        rune_type = np.random.choice(self.rune_types)
        
        entity_id = self.em.create_entity()
        self.em.add_component(entity_id, 'position', PositionComponent(x, y))
        self.em.add_component(entity_id, 'rune', RuneComponent(
            rune_type=rune_type,
            spawn_time=game_time
        ))
        self.em.add_component(entity_id, 'collision', CollisionComponent(radius=32))
        
        print(f"[Runes] Spawned {rune_type} rune at ({x:.0f}, {y:.0f})")
        return entity_id
    
    def check_pickups(self):
        """Check for rune pickups"""
        from engine.ecs.components import PositionComponent
        
        runes = self.em.get_entities_with_component('rune')
        heroes = self.em.get_entities_with_component('hero')
        
        for rune_id in list(runes):
            rune_pos = self.em.get_component(rune_id, 'position')
            rune = self.em.get_component(rune_id, 'rune')
            
            for hero_id in heroes:
                hero_pos = self.em.get_component(hero_id, 'position')
                
                distance = rune_pos.distance_to(hero_pos)
                
                if distance < 64:  # Pickup range
                    self._apply_rune_buff(hero_id, rune.rune_type)
                    self.em.destroy_entity(rune_id)
                    print(f"[Runes] Hero {hero_id} picked up {rune.rune_type} rune")
                    break
    
    def _apply_rune_buff(self, hero_id: int, rune_type: str):
        """Apply rune buff to hero"""
        # Simplified - just print message
        # Full implementation would add buff components
        print(f"  Applied {rune_type} buff to hero {hero_id}")
