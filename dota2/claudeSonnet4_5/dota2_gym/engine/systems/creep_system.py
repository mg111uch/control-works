"""
Complete Creep System
Spawns from bases, moves to mid lane
Optimized with spatial hashing for better performance
"""
import numpy as np
import random
from typing import Optional, List, Tuple
from dataclasses import dataclass
from engine.ecs.entity_manager import EntityManager
from engine.ecs.components import *

MAX_TARGETS_PER_CREEP = 5

class CreepSpawner:
    """Manages creep wave spawning from bases"""
    
    def __init__(self, entity_manager: EntityManager, config: dict):
        self.em = entity_manager
        self.config = config
        self.spawn_interval = 30.0  # 30 seconds
        self.last_spawn_time = -30.0  # Spawn immediately
        
        # Spawn positions (inside bases)
        self.radiant_spawn = (450, 6750)  # Top-left base
        self.dire_spawn = (6750, 450)  # Bottom-right base

        # Mid lane waypoints along anti-diagonal
        self.radiant_mid_waypoints = [
            (450, 6750),   # Radiant base
            (1200, 6000),  # Early lane
            (2400, 4800),  # Radiant T1 area
            (3600, 3600),  # Mid river
            (4800, 2400),  # Dire T1 area
            (6000, 1200),  # Dire high ground
            (6750, 450)    # Dire base
        ]

        # Top lane waypoints
        self.radiant_top_waypoints = [
            (450, 6750),   # Radiant base
            (1800, 6750),  # Along top
            (3600, 6750),  # Radiant top T1
            (5400, 6750),  # Mid top
            (6750, 5400),  # Dire top T1
            (6750, 3600),  # Dire top high ground
            (6750, 1800),  # Dire top base area
            (6750, 450)    # Dire base
        ]

        # Bottom lane waypoints
        self.radiant_bottom_waypoints = [
            (450, 6750),   # Radiant base
            (450, 5400),   # Along bottom
            (450, 3600),   # Radiant bottom T1
            (450, 1800),   # Mid bottom
            (1800, 450),   # Dire bottom T1
            (3600, 450),   # Dire bottom high ground
            (5400, 450),   # Dire bottom base area
            (6750, 450)    # Dire base
        ]

        self.dire_mid_waypoints = list(reversed(self.radiant_mid_waypoints))
        self.dire_top_waypoints = list(reversed(self.radiant_top_waypoints))
        self.dire_bottom_waypoints = list(reversed(self.radiant_bottom_waypoints))
        
        # Store waypoints for each creep
        self.creep_waypoints = {}
    
    def update(self, game_time: float):
        """Check if it's time to spawn a new wave"""
        if game_time - self.last_spawn_time >= self.spawn_interval:
            for lane in ['top', 'mid', 'bottom']:
                self.spawn_wave(0, lane)  # Radiant
                self.spawn_wave(1, lane)  # Dire
            self.last_spawn_time = game_time
            print(f"[Creeps] New waves spawned in all lanes at {game_time:.1f}s")
    
    def spawn_wave(self, team: int, lane: str):
        """Spawn a wave of creeps for a team in a specific lane"""
        spawn_pos = self.radiant_spawn if team == 0 else self.dire_spawn

        if lane == 'mid':
            waypoints = self.radiant_mid_waypoints if team == 0 else self.dire_mid_waypoints
        elif lane == 'top':
            waypoints = self.radiant_top_waypoints if team == 0 else self.dire_top_waypoints
        elif lane == 'bottom':
            waypoints = self.radiant_bottom_waypoints if team == 0 else self.dire_bottom_waypoints
        else:
            raise ValueError(f"Invalid lane: {lane}")
        
        # 3 melee creeps
        for i in range(3):
            offset_x = (i - 1) * 50
            offset_y = (i - 1) * 30
            self.create_creep(team, 'melee', 
                            spawn_pos[0] + offset_x, 
                            spawn_pos[1] + offset_y, 
                            waypoints)
        
        # 1 ranged creep
        self.create_creep(team, 'ranged', 
                         spawn_pos[0], 
                         spawn_pos[1] - 60, 
                         waypoints)
    
    def create_creep(self, team: int, creep_type: str, x: float, y: float, 
                     waypoints: List[Tuple]):
        """Create a single creep"""
        entity_id = self.em.create_entity()
        
        # Stats based on type
        if creep_type == 'melee':
            hp, damage, attack_range, speed = 550, 22, 128, 325
            gold, xp = 40, 62
            radius = 30  # Increased by 50% from 20
        elif creep_type == 'ranged':
            hp, damage, attack_range, speed = 300, 26, 500, 325
            gold, xp = 45, 62
            radius = 24  # Increased by 50% from 16
        else:  # siege
            hp, damage, attack_range, speed = 825, 42, 685, 325
            gold, xp = 74, 88
            radius = 24
        
        # Add components
        self.em.add_component(entity_id, 'position', 
                             PositionComponent(x, y))
        
        self.em.add_component(entity_id, 'velocity', 
                             VelocityComponent(0, 0))
        
        self.em.add_component(entity_id, 'movement', 
                             MovementComponent(move_speed=speed))
        
        self.em.add_component(entity_id, 'stats', StatsComponent(
            max_hp=hp, current_hp=hp,
            max_mana=0, current_mana=0,
            armor=2.0
        ))
        
        self.em.add_component(entity_id, 'combat', CombatComponent(
            damage_min=damage * 0.9,
            damage_max=damage * 1.1,
            attack_range=attack_range,
            attack_speed=1.0,
            attack_cooldown=1.0,
            last_attack_time=-10.0
        ))
        
        self.em.add_component(entity_id, 'creep', CreepComponent(
            team=team,
            creep_type=creep_type,
            gold_value=gold,
            xp_value=xp
        ))
        
        self.em.add_component(entity_id, 'ai', AIComponent(
            state='move_to_lane',
            aggro_range=500.0
        ))
        
        self.em.add_component(entity_id, 'collision', 
                             CollisionComponent(radius=radius))
        
        # Store waypoints and initialize waypoint index in movement component
        movement = self.em.get_component(entity_id, 'movement')
        if movement:
            movement.current_waypoint_index = 0
        self.creep_waypoints[entity_id] = waypoints  # store reference once
        
        return entity_id


class CreepAI:
    """Optimized rule-based AI for creeps using spatial hashing"""
    
    def __init__(self, entity_manager: EntityManager, spawner: CreepSpawner):
        self.em = entity_manager
        self.spawner = spawner
    
    def update(self, movement_system, combat_system, current_time: float):
        """Update all creep AI with staggering"""
        creeps = self.em.get_entities_with_component('creep')
        
        # Only update 1/3 of creeps per frame (Fix 10)
        frame_offset = int(current_time * 15) % 3  # Rotate which third each frame
        
        for i, creep_id in enumerate(creeps):
            if i % 3 != frame_offset:
                continue  # Skip this creep this frame
            
            self._update_creep_ai(creep_id, movement_system, combat_system, current_time)
    
    def _update_creep_ai(self, creep_id: int, movement_system, combat_system,
                        current_time: float):
        """Update single creep AI - attack all enemies in range"""
        get = self.em.get_component  # Local caching for performance
        
        ai = get(creep_id, 'ai')
        creep = get(creep_id, 'creep')
        position = get(creep_id, 'position')
        combat = get(creep_id, 'combat')
        stats = get(creep_id, 'stats')

        if not all([ai, creep, position, combat, stats]) or not stats.is_alive():
            return
        
        # Stop movement updates while attacking
        if combat and combat.attack_target is not None:
            return

        # Find all enemies within aggro range (optimized with spatial hash)
        enemies_in_aggro = self._find_all_enemies_optimized(creep_id, creep.team, position, ai.aggro_range)

        if not enemies_in_aggro:
            # No enemies - follow lane
            ai.state = 'move_to_lane'
            ai.target_entity = None
            self._follow_lane(creep_id, movement_system)
            return

        # Check which enemies are within attack range using squared distance
        attack_range_sq = combat.attack_range * combat.attack_range
        enemies_in_attack_range = []
        for enemy_id in enemies_in_aggro:
            enemy_pos = get(enemy_id, 'position')
            if enemy_pos:
                dx = enemy_pos.x - position.x
                dy = enemy_pos.y - position.y
                if dx*dx + dy*dy <= attack_range_sq:
                    enemies_in_attack_range.append(enemy_id)

        if enemies_in_attack_range:
            # Found enemies in attack range - prioritize attacking creeps over heroes
            ai.state = 'attack'

            # Check if there are creeps in attack range
            creeps_in_range = [eid for eid in enemies_in_attack_range if get(eid, 'creep')]
            if creeps_in_range:
                # Prioritize creeps — sort closest first
                creeps_in_range.sort(key=lambda eid: (
                    position.distance_to(get(eid, 'position'))
                ))
                targets = creeps_in_range[:MAX_TARGETS_PER_CREEP]
            else:
                # No enemy creeps → fall back to any enemy (heroes, towers, etc.)
                enemies_in_attack_range.sort(key=lambda eid: (
                    position.distance_to(get(eid, 'position'))
                ))
                targets = enemies_in_attack_range[:MAX_TARGETS_PER_CREEP]

            ai.target_entity = targets[0]  # Primary target
            movement_system.stop_movement(creep_id)

            if combat.can_attack(current_time):
                # Set cooldown before attacking prioritized enemies
                combat.last_attack_time = current_time
                for target_id in targets:
                    target_pos = get(target_id, 'position')
                    if target_pos:
                        if creep.creep_type == 'ranged':
                            # Ranged creeps throw projectiles
                            combat_system.create_attack_projectile(
                                creep_id, target_pos.x, target_pos.y, target_id,
                                check_cooldown=False
                            )
                        else:
                            # Melee creeps apply damage directly
                            self._apply_melee_damage(creep_id, target_id)
        else:
            # No enemies in attack range but some in aggro range - move toward nearest
            ai.state = 'attack'
            ai.target_entity = enemies_in_aggro[0]
            nearest_enemy_pos = get(enemies_in_aggro[0], 'position')
            if nearest_enemy_pos:
                movement_system.set_move_target(creep_id, nearest_enemy_pos.x, nearest_enemy_pos.y)

    def _find_all_enemies_optimized(self, creep_id: int, team: int,
                                   position: PositionComponent, range: float) -> list:
        """
        Optimized enemy finding using spatial hash.
        Returns enemies within range, prioritized: creeps first, then heroes, then towers
        """
        creeps = []
        heroes = []
        towers = []
        
        # Get spatial hash from entity manager
        spatial_hash = getattr(self.em, 'spatial_hash', None)
        nearby_ids = None
        
        if spatial_hash and spatial_hash.cells:
            # Use spatial hash for O(1) nearby entity lookup
            nearby_ids = spatial_hash.query_radius(position.x, position.y, range)
        else:
            # Fallback: get all potential enemy entities
            nearby_ids = set()
            nearby_ids.update(self.em.get_entities_with_component('creep'))
            nearby_ids.update(self.em.get_entities_with_component('hero'))
            nearby_ids.update(self.em.get_entities_with_component('tower'))
        
        # Process nearby entities by type
        for entity_id in nearby_ids:
            if entity_id == creep_id:
                continue
            
            entity_pos = self.em.get_component(entity_id, 'position')
            if not entity_pos:
                continue
            
            # Calculate squared distance to avoid sqrt
            dx = position.x - entity_pos.x
            dy = position.y - entity_pos.y
            dist_sq = dx*dx + dy*dy
            
            if dist_sq > range * range:
                continue
            
            # Check entity type
            entity_creep = self.em.get_component(entity_id, 'creep')
            if entity_creep:
                if entity_creep.team != team:
                    entity_stats = self.em.get_component(entity_id, 'stats')
                    if entity_stats and entity_stats.is_alive():
                        creeps.append(entity_id)
                continue
            
            entity_hero = self.em.get_component(entity_id, 'hero')
            if entity_hero:
                if entity_hero.team != team:
                    entity_stats = self.em.get_component(entity_id, 'stats')
                    if entity_stats and entity_stats.is_alive():
                        heroes.append(entity_id)
                continue
            
            entity_tower = self.em.get_component(entity_id, 'tower')
            if entity_tower:
                if entity_tower.team != team:
                    entity_stats = self.em.get_component(entity_id, 'stats')
                    if entity_stats and entity_stats.is_alive():
                        towers.append(entity_id)
                continue
        
        # Return prioritized list: creeps > heroes > towers
        return creeps + heroes + towers
    
    def _find_all_enemies(self, creep_id: int, team: int,
                          position: PositionComponent, range: float) -> list:
        """Legacy method - use _find_all_enemies_optimized instead"""
        return self._find_all_enemies_optimized(creep_id, team, position, range)
    
    def _find_nearest_enemy(self, creep_id: int, team: int, 
                           position: PositionComponent, range: float) -> Optional[int]:
        """Find nearest enemy entity within range using spatial hash"""
        nearest_enemy = None
        nearest_distance = range
        
        # Use spatial hash if available
        spatial_hash = getattr(self.em, 'spatial_hash', None)
        nearby_ids = None
        
        if spatial_hash and spatial_hash.cells:
            nearby_ids = spatial_hash.query_radius(position.x, position.y, range)
        else:
            nearby_ids = set()
            nearby_ids.update(self.em.get_entities_with_component('hero'))
            nearby_ids.update(self.em.get_entities_with_component('creep'))
            nearby_ids.update(self.em.get_entities_with_component('tower'))
        
        for entity_id in nearby_ids:
            if entity_id == creep_id:
                continue
            
            entity_pos = self.em.get_component(entity_id, 'position')
            if not entity_pos:
                continue
            
            # Calculate squared distance to avoid sqrt
            dx = position.x - entity_pos.x
            dy = position.y - entity_pos.y
            dist_sq = dx*dx + dy*dy
            
            if dist_sq >= nearest_distance * nearest_distance:
                continue
            
            # Check if enemy and alive
            entity_team = None
            entity_hero = self.em.get_component(entity_id, 'hero')
            entity_creep = self.em.get_component(entity_id, 'creep')
            entity_tower = self.em.get_component(entity_id, 'tower')
            
            if entity_hero:
                entity_team = entity_hero.team
            elif entity_creep:
                entity_team = entity_creep.team
            elif entity_tower:
                entity_team = entity_tower.team
            
            if entity_team is None or entity_team == team:
                continue
            
            entity_stats = self.em.get_component(entity_id, 'stats')
            if not entity_stats or not entity_stats.is_alive():
                continue
            
            nearest_enemy = entity_id
            nearest_distance = distance
        
        return nearest_enemy

    def _apply_melee_damage(self, attacker_id: int, target_id: int):
        """Apply melee damage directly to target"""
        combat = self.em.get_component(attacker_id, 'combat')
        stats = self.em.get_component(attacker_id, 'stats')
        target_stats = self.em.get_component(target_id, 'stats')
        target_creep = self.em.get_component(target_id, 'creep')
        target_hero = self.em.get_component(target_id, 'hero')
        target_tower = self.em.get_component(target_id, 'tower')

        if not combat or not stats or not target_stats:
            return

        damage = combat.get_random_damage()
        actual_damage = target_stats.take_damage(damage)

        if not target_stats.is_alive():
            if target_creep:
                self._award_kill_rewards(attacker_id, target_id, target_creep)
            elif target_hero:
                self._on_hero_killed(attacker_id, target_id)
            elif target_tower:
                pass

    def _award_kill_rewards(self, killer_id: int, victim_id: int, victim_creep):
        """Award gold/xp for creep kill"""
        killer_hero = self.em.get_component(killer_id, 'hero')
        if not killer_hero:
            return

        killer_hero.last_hits += 1

        from engine.systems.item_system import InventoryComponent
        inventory = self.em.get_component(killer_id, 'inventory')
        if inventory:
            inventory.gold += victim_creep.gold_value

        if killer_hero.hero_id == 'shadow_fiend':
            soul_value = 1
            old_souls = killer_hero.souls
            killer_hero.souls = min(killer_hero.souls + soul_value, 100)

    def _on_hero_killed(self, killer_id: int, victim_id: int):
        """Handle hero death - collect souls"""
        killer_hero = self.em.get_component(killer_id, 'hero')

        if killer_hero and killer_hero.hero_id == 'shadow_fiend':
            old_souls = killer_hero.souls
            killer_hero.souls = min(killer_hero.souls + 1, 36)

    def _follow_lane(self, creep_id: int, movement_system):
        """Follow lane waypoints"""
        if creep_id not in self.spawner.creep_waypoints:
            return
        
        position = self.em.get_component(creep_id, 'position')
        movement = self.em.get_component(creep_id, 'movement')
        if not position or not movement:
            return
        
        waypoints = self.spawner.creep_waypoints[creep_id]
        current_idx = movement.current_waypoint_index
        
        if current_idx >= len(waypoints):
            return  # Reached end
        
        target_waypoint = waypoints[current_idx]
        distance_to_waypoint = np.sqrt(
            (position.x - target_waypoint[0])**2 + 
            (position.y - target_waypoint[1])**2
        )
        
        if distance_to_waypoint < 100:
            # Reached waypoint - move to next
            if current_idx + 1 < len(waypoints):
                movement.current_waypoint_index += 1
                movement.is_moving = False  # allow next waypoint to be issued
                next_waypoint = waypoints[movement.current_waypoint_index]
                # Only issue movement if not already moving - use movement_system.set_move_target()
                if not movement.is_moving:
                    movement_system.set_move_target(creep_id, next_waypoint[0], next_waypoint[1])
        else:
            # Only issue movement if not already moving toward this waypoint - use movement_system.set_move_target()
            if not movement.is_moving:
                movement_system.set_move_target(creep_id, target_waypoint[0], target_waypoint[1])
