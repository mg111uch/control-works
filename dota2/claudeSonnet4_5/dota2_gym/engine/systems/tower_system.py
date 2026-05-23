from engine.ecs.entity_manager import EntityManager
from engine.ecs.components import *

class TowerSystem:
    """Tower attack system - optimized with spatial hashing"""
    
    def __init__(self, entity_manager: EntityManager):
        self.em = entity_manager
    
    def create_tower(self, team: int, tier: int, x: float, y: float) -> int:
        """Create a tower"""
        entity_id = self.em.create_entity()
        
        # Tower stats based on tier
        hp_by_tier = {1: 1800, 2: 2500, 3: 2500}
        damage_by_tier = {1: 100, 2: 142, 3: 142}
        
        hp = hp_by_tier.get(tier, 1800)
        damage = damage_by_tier.get(tier, 100)
        
        self.em.add_component(entity_id, 'position', PositionComponent(x, y))
        
        self.em.add_component(entity_id, 'stats', StatsComponent(
            max_hp=hp, current_hp=hp,
            max_mana=0, current_mana=0,
            armor=20.0
        ))
        
        self.em.add_component(entity_id, 'tower', TowerComponent(
            team=team,
            tier=tier,
            attack_damage=damage,
            attack_range=700.0,
            attack_cooldown=1.0,
            last_attack_time=-10.0
        ))
        
        self.em.add_component(entity_id, 'combat', CombatComponent(
            damage_min=damage,
            damage_max=damage,
            attack_range=700.0,
            attack_speed=1.0,
            attack_cooldown=1.0,
            last_attack_time=-10.0
        ))
        
        self.em.add_component(entity_id, 'collision', CollisionComponent(radius=64))
        
        return entity_id
    
    def update(self, combat_system, current_time: float):
        """Update all towers"""
        towers = self.em.get_entities_with_component('tower')
        
        for tower_id in towers:
            self._update_tower(tower_id, combat_system, current_time)
    
    def _update_tower(self, tower_id: int, combat_system, current_time: float):
        """Update single tower - attack all enemies in range"""
        get = self.em.get_component  # Local caching for performance
        
        tower = get(tower_id, 'tower')
        combat = get(tower_id, 'combat')
        position = get(tower_id, 'position')
        stats = get(tower_id, 'stats')

        if not all([tower, combat, position, stats]) or not stats.is_alive():
            return

        if not combat.can_attack(current_time):
            return
        
        # Lock attack target - keep current target if valid
        if tower.attack_target is not None:
            target_stats = get(tower.attack_target, 'stats')
            target_pos = get(tower.attack_target, 'position')
            
            if target_stats and target_stats.is_alive() and target_pos:
                # Check if target is still in range using squared distance
                dx = target_pos.x - position.x
                dy = target_pos.y - position.y
                dist_sq = dx*dx + dy*dy
                if dist_sq <= tower.attack_range * tower.attack_range:
                    # Target still valid, fire at it
                    combat_system.create_attack_projectile(
                        tower_id,
                        target_pos.x,
                        target_pos.y,
                        tower.attack_target,
                        check_cooldown=False
                    )
                    combat.last_attack_time = current_time
                    return
            
            # Target invalid, clear it
            tower.attack_target = None

        # Find all enemies in range using spatial hash
        enemies = self._find_all_enemies_optimized(tower_id, tower.team, position, tower.attack_range)

        if not enemies:
            return

        # Attack all enemies in range
        for enemy_id in enemies:
            target_pos = get(enemy_id, 'position')
            if target_pos:
                # Set as attack target for next frame
                tower.attack_target = enemy_id
                combat_system.create_attack_projectile(tower_id,
                                                target_pos.x,
                                                target_pos.y,
                                                enemy_id,
                                                check_cooldown=False)

        # Set cooldown after attacking all enemies
        combat.last_attack_time = current_time

    def _find_all_enemies_optimized(self, tower_id: int, team: int, position: PositionComponent,
                                   range: float) -> list:
        """
        Optimized enemy finding using spatial hash.
        Returns enemies within range.
        """
        enemies = []
        
        # Use spatial hash if available
        spatial_hash = getattr(self.em, 'spatial_hash', None)
        nearby_ids = None
        
        if spatial_hash and spatial_hash.cells:
            # Use spatial hash for O(1) nearby entity lookup
            nearby_ids = spatial_hash.query_radius(position.x, position.y, range)
        else:
            # Fallback: get all potential enemy entities
            nearby_ids = set()
            nearby_ids.update(self.em.get_entities_with_component('hero'))
            nearby_ids.update(self.em.get_entities_with_component('creep'))
        
        # Process nearby entities
        for entity_id in nearby_ids:
            if entity_id == tower_id:
                continue
            
            entity_pos = self.em.get_component(entity_id, 'position')
            if not entity_pos:
                continue
            
            # Calculate squared distance once to avoid sqrt
            dx = position.x - entity_pos.x
            dy = position.y - entity_pos.y
            dist_sq = dx*dx + dy*dy
            
            if dist_sq > range * range:
                continue
            
            # Check entity type
            entity_team = None
            entity_hero = self.em.get_component(entity_id, 'hero')
            entity_creep = self.em.get_component(entity_id, 'creep')
            
            if entity_hero:
                entity_team = entity_hero.team
            elif entity_creep:
                entity_team = entity_creep.team
            
            if entity_team is None or entity_team == team:
                continue
            
            entity_stats = self.em.get_component(entity_id, 'stats')
            if not entity_stats or not entity_stats.is_alive():
                continue
            
            enemies.append(entity_id)
        
        return enemies
    
    def _find_all_enemies(self, tower_id: int, team: int, position: PositionComponent,
                         range: float) -> list:
        """Legacy method - use _find_all_enemies_optimized instead"""
        return self._find_all_enemies_optimized(tower_id, team, position, range)
    
    def _find_target(self, tower_id: int, team: int, position: PositionComponent,
                    range: float) -> Optional[int]:
        """Find target to attack - prioritize heroes, then find nearest using spatial hash"""
        nearest_enemy = None
        nearest_distance_sq = range * range  # Use squared distance
        
        # Use spatial hash if available
        spatial_hash = getattr(self.em, 'spatial_hash', None)
        nearby_ids = None
        
        if spatial_hash and spatial_hash.cells:
            nearby_ids = spatial_hash.query_radius(position.x, position.y, range)
        else:
            nearby_ids = set()
            nearby_ids.update(self.em.get_entities_with_component('hero'))
            nearby_ids.update(self.em.get_entities_with_component('creep'))
        
        for entity_id in nearby_ids:
            if entity_id == tower_id:
                continue
            
            entity_pos = self.em.get_component(entity_id, 'position')
            if not entity_pos:
                continue
            
            # Calculate squared distance to avoid sqrt
            dx = position.x - entity_pos.x
            dy = position.y - entity_pos.y
            dist_sq = dx*dx + dy*dy
            
            if dist_sq >= nearest_distance_sq:
                continue
            
            # Check if enemy and alive
            entity_team = None
            entity_hero = self.em.get_component(entity_id, 'hero')
            entity_creep = self.em.get_component(entity_id, 'creep')
            
            if entity_hero:
                entity_team = entity_hero.team
            elif entity_creep:
                entity_team = entity_creep.team
            
            if entity_team is None or entity_team == team:
                continue
            
            entity_stats = self.em.get_component(entity_id, 'stats')
            if not entity_stats or not entity_stats.is_alive():
                continue
            
            nearest_enemy = entity_id
            nearest_distance_sq = dist_sq
        
        return nearest_enemy
