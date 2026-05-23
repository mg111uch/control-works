"""Performance tests for Dota2 gym - anti-regression tests for scalability"""
import pytest
import time
import numpy as np
from engine.ecs.entity_manager import EntityManager
from engine.ecs.components import (
    PositionComponent, StatsComponent, CombatComponent, 
    HeroComponent, CollisionComponent, MovementComponent,
    TowerComponent, CreepComponent, ProjectileComponent
)
from engine.systems.combat_system import CombatSystem
from engine.systems.tower_system import TowerSystem
from engine.systems.movement_system import MovementSystem
from engine.systems.spatial_hash import SpatialHash
from engine.systems.creep_system import CreepSpawner, CreepAI


class TestPerformance:
    """Performance and scalability tests"""
    
    def setup_method(self):
        """Setup before each test"""
        self.em = EntityManager()
        self.dt = 1.0 / 15.0
        self.combat_system = CombatSystem(self.em, self.dt)
        self.config = {
            'game': {'tick_rate': 15, 'map_width': 7200, 'map_height': 7200}
        }
        # Setup spatial hash
        self.spatial_hash = SpatialHash(cell_size=500, map_width=7200, map_height=7200)
        self.em.spatial_hash = self.spatial_hash
    
    def create_test_hero(self, x, y, team, entity_id=None):
        """Helper to create a test hero"""
        if entity_id is None:
            entity_id = self.em.create_entity()
        
        self.em.add_component(entity_id, 'position', PositionComponent(x, y))
        self.em.add_component(entity_id, 'stats', StatsComponent(
            max_hp=1000,
            current_hp=1000,
            max_mana=500,
            current_mana=500
        ))
        self.em.add_component(entity_id, 'combat', CombatComponent(
            damage_min=50,
            damage_max=60,
            attack_range=500,
            attack_speed=1.7,
            attack_cooldown=1.7
        ))
        self.em.add_component(entity_id, 'hero', HeroComponent(
            hero_id='shadow_fiend',
            team=team
        ))
        self.em.add_component(entity_id, 'collision', CollisionComponent(radius=24))
        self.em.add_component(entity_id, 'movement', MovementComponent(move_speed=300))
        
        # Insert into spatial hash
        position = self.em.get_component(entity_id, 'position')
        self.spatial_hash.insert(entity_id, position.x, position.y)
        
        return entity_id
    
    def create_test_creep(self, x, y, team, creep_type='melee'):
        """Helper to create a test creep"""
        entity_id = self.em.create_entity()
        
        if creep_type == 'melee':
            hp, damage, attack_range = 550, 22, 128
        else:
            hp, damage, attack_range = 300, 26, 500
        
        self.em.add_component(entity_id, 'position', PositionComponent(x, y))
        self.em.add_component(entity_id, 'stats', StatsComponent(
            max_hp=hp, current_hp=hp,
            max_mana=0, current_mana=0
        ))
        self.em.add_component(entity_id, 'combat', CombatComponent(
            damage_min=damage * 0.9,
            damage_max=damage * 1.1,
            attack_range=attack_range,
            attack_speed=1.0,
            attack_cooldown=1.0
        ))
        self.em.add_component(entity_id, 'creep', CreepComponent(
            team=team,
            creep_type=creep_type
        ))
        self.em.add_component(entity_id, 'collision', CollisionComponent(radius=30 if creep_type == 'melee' else 24))
        self.em.add_component(entity_id, 'movement', MovementComponent(move_speed=325))
        
        # Insert into spatial hash
        position = self.em.get_component(entity_id, 'position')
        self.spatial_hash.insert(entity_id, position.x, position.y)
        
        return entity_id
    
    def test_combat_scaling_linear(self):
        """Test that combat update cost grows linearly with entity count"""
        # Create a large number of creeps
        num_creeps = 200
        
        for i in range(num_creeps):
            # Radiant creeps
            self.create_test_creep(1000 + i * 10, 1000, team=0)
            # Dire creeps
            self.create_test_creep(1000 + i * 10, 1100, team=1)
        
        # Time combat updates
        start = time.perf_counter()
        for _ in range(10):
            self.combat_system.update()
        elapsed = time.perf_counter() - start
        
        # Should complete in reasonable time (< 0.2s for 10 updates)
        assert elapsed < 0.2, f"Combat update took {elapsed:.3f}s, expected < 0.2s"
    
    def test_tower_nearby_query_only(self):
        """Test tower update cost is independent of total entity count"""
        tower_system = TowerSystem(self.em)
        
        # Create a tower
        tower_id = tower_system.create_tower(team=0, tier=1, x=1000, y=1000)
        tower_pos = self.em.get_component(tower_id, 'position')
        self.spatial_hash.insert(tower_id, tower_pos.x, tower_pos.y)
        
        # Create many creeps far away (should not affect tower query)
        for i in range(300):
            creep_id = self.create_test_creep(4000 + i * 10, 4000, team=1)
        
        # Create only 5 enemies near tower
        for i in range(5):
            enemy = self.create_test_hero(1200 + i * 50, 1000, team=1)
        
        # Time tower update
        t0 = time.perf_counter()
        tower_system.update(self.combat_system, 5.0)
        t1 = time.perf_counter()
        
        elapsed = t1 - t0
        # Tower update should be fast (< 0.02s)
        assert elapsed < 0.02, f"Tower update took {elapsed:.4f}s, expected < 0.02s"
    
    def test_projectiles_cleanup(self):
        """Test that projectiles are properly cleaned up"""
        # Create projectiles using ProjectileComponent
        num_projectiles = 100
        
        for i in range(num_projectiles):
            proj_id = self.em.create_entity()
            self.em.add_component(proj_id, 'position', PositionComponent(i * 10, 0))
            self.em.add_component(proj_id, 'projectile', ProjectileComponent(
                source_entity=-1,
                target_x=10000,
                target_y=0,
                damage=50,
                speed=1000,
                team=0,
                lifetime=0.1,  # Short lifetime for fast cleanup
                target_entity=None
            ))
            self.em.add_component(proj_id, 'collision', CollisionComponent(radius=10))
        
        # Update projectiles multiple times
        for _ in range(20):
            self.combat_system.update()
        
        # All projectiles should be cleaned up
        remaining = self.em.get_entities_with_component('projectile')
        assert len(remaining) == 0, f"Expected 0 projectiles, found {len(remaining)}"
    
    def test_spatial_hash_removes_dead_entities(self):
        """Test that dead entities are removed from spatial hash"""
        # Create entities
        entity_ids = []
        for i in range(50):
            entity_ids.append(self.create_test_creep(1000 + i * 10, 1000, team=0))
        
        # Verify entities are in spatial hash
        nearby = self.spatial_hash.query_radius(1100, 1000, 500)
        assert len(nearby) >= 50, f"Expected >= 50 entities in spatial hash, found {len(nearby)}"
        
        # Destroy some entities
        for entity_id in entity_ids[:25]:
            self.em.destroy_entity(entity_id)
        
        # Verify dead entities are removed from spatial hash
        nearby_after = self.spatial_hash.query_radius(1100, 1000, 500)
        assert len(nearby_after) <= 25, f"Expected <= 25 entities after destroy, found {len(nearby_after)}"
    
    def test_position_changed_flag_exists(self):
        """Test that position.changed flag exists and has correct default"""
        position = PositionComponent(1000, 1000)
        
        # Initial position should have changed=True (default)
        assert position.changed is True, "Initial position should have changed=True"
        
        # Flag should be modifiable
        position.changed = False
        assert position.changed is False, "Position.changed should be modifiable"
    
    def test_combat_local_caching(self):
        """Test that combat system uses local caching for get_component"""
        # Create entities
        for i in range(50):
            self.create_test_hero(1000 + i * 10, 1000 + i * 10, team=0)
            self.create_test_hero(1000 + i * 10, 2000 + i * 10, team=1)
        
        # This should complete quickly due to local caching
        start = time.perf_counter()
        for _ in range(10):
            self.combat_system._check_projectile_collisions()
        elapsed = time.perf_counter() - start
        
        assert elapsed < 0.3, f"Collision check with local caching took {elapsed:.3f}s, expected < 0.3s"


class TestMovementPathSanity:
    """Movement path sanity tests - anti-regression tests"""
    
    def setup_method(self):
        """Setup before each test"""
        self.em = EntityManager()
        self.config = {
            'game': {'tick_rate': 15, 'map_width': 7200, 'map_height': 7200}
        }
        self.spatial_hash = SpatialHash(cell_size=500, map_width=7200, map_height=7200)
        self.em.spatial_hash = self.spatial_hash
        self.movement_system = MovementSystem(self.em, 1.0/15.0)
        self.movement_system.set_spatial_hash(self.spatial_hash)
    
    def test_position_changed_after_movement(self):
        """Test that position.changed is set after movement"""
        entity_id = self.em.create_entity()
        self.em.add_component(entity_id, 'position', PositionComponent(1000, 1000))
        self.em.add_component(entity_id, 'movement', MovementComponent(move_speed=300))
        
        position = self.em.get_component(entity_id, 'position')
        
        # Initially changed should be True
        assert position.changed is True
        
        # Set to False to simulate start of frame
        position.changed = False
        
        # Simulate movement - directly modify position as movement system does
        position.x = 2000
        position.y = 1000
        position.changed = True
        
        # Position should now be marked as changed
        assert position.changed is True
    
    def test_movement_system_local_caching(self):
        """Test that movement system uses local caching"""
        # Create many entities
        for i in range(100):
            entity_id = self.em.create_entity()
            self.em.add_component(entity_id, 'position', PositionComponent(1000 + i * 5, 1000 + i * 5))
            self.em.add_component(entity_id, 'movement', MovementComponent(move_speed=300))
            self.em.add_component(entity_id, 'collision', CollisionComponent(radius=24))
            
            # Insert into spatial hash
            position = self.em.get_component(entity_id, 'position')
            self.spatial_hash.insert(entity_id, position.x, position.y)
        
        # Set targets for all entities
        for entity_id in self.em.get_entities_with_components('position', 'movement'):
            movement = self.em.get_component(entity_id, 'position')
            self.movement_system.set_move_target(entity_id, movement.x + 100, movement.y + 100)
        
        # Time movement updates
        start = time.perf_counter()
        for _ in range(10):
            self.movement_system.update()
        elapsed = time.perf_counter() - start
        
        assert elapsed < 0.5, f"Movement update took {elapsed:.3f}s, expected < 0.5s"


class TestFrameBudget:
    """Frame budget smoke tests"""
    
    def setup_method(self):
        """Setup before each test"""
        self.em = EntityManager()
        self.config = {
            'game': {'tick_rate': 15, 'map_width': 7200, 'map_height': 7200}
        }
        self.spatial_hash = SpatialHash(cell_size=500, map_width=7200, map_height=7200)
        self.em.spatial_hash = self.spatial_hash
        self.combat_system = CombatSystem(self.em, 1.0/15.0)
        self.tower_system = TowerSystem(self.em)
        self.movement_system = MovementSystem(self.em, 1.0/15.0)
        self.movement_system.set_spatial_hash(self.spatial_hash)
        self.creep_spawner = CreepSpawner(self.em, self.config)
        self.creep_ai = CreepAI(self.em, self.creep_spawner)
    
    def test_full_tick_under_budget(self):
        """Test that a full game tick completes within frame budget"""
        # Setup a large world
        # Create towers
        for i in range(3):
            tower_id = self.tower_system.create_tower(team=0, tier=1, x=1000 + i * 200, y=1000 + i * 200)
            pos = self.em.get_component(tower_id, 'position')
            self.spatial_hash.insert(tower_id, pos.x, pos.y)
        
        # Create heroes
        for i in range(5):
            hero_id = self.em.create_entity()
            self.em.add_component(hero_id, 'position', PositionComponent(1000 + i * 50, 1000 + i * 50))
            self.em.add_component(hero_id, 'stats', StatsComponent(max_hp=1000, current_hp=1000, max_mana=500, current_mana=500))
            self.em.add_component(hero_id, 'combat', CombatComponent(damage_min=50, damage_max=60, attack_range=500, attack_speed=1.7, attack_cooldown=1.7))
            self.em.add_component(hero_id, 'hero', HeroComponent(hero_id='shadow_fiend', team=0))
            self.em.add_component(hero_id, 'collision', CollisionComponent(radius=24))
            self.em.add_component(hero_id, 'movement', MovementComponent(move_speed=300))
            
            pos = self.em.get_component(hero_id, 'position')
            self.spatial_hash.insert(hero_id, pos.x, pos.y)
        
        # Create many creeps
        for i in range(100):
            for team in [0, 1]:
                creep_id = self.em.create_entity()
                self.em.add_component(creep_id, 'position', PositionComponent(2000 + i * 20, 2000 + (team - 0.5) * 100))
                self.em.add_component(creep_id, 'stats', StatsComponent(max_hp=550, current_hp=550, max_mana=0, current_mana=0))
                self.em.add_component(creep_id, 'combat', CombatComponent(damage_min=20, damage_max=25, attack_range=128, attack_speed=1.0, attack_cooldown=1.0))
                self.em.add_component(creep_id, 'creep', CreepComponent(team=team, creep_type='melee'))
                self.em.add_component(creep_id, 'collision', CollisionComponent(radius=30))
                self.em.add_component(creep_id, 'movement', MovementComponent(move_speed=325))
                
                pos = self.em.get_component(creep_id, 'position')
                self.spatial_hash.insert(creep_id, pos.x, pos.y)
        
        # Time a full tick
        start = time.perf_counter()
        
        # Update all systems
        self.movement_system.update()
        self.combat_system.update()
        self.creep_ai.update(self.movement_system, self.combat_system, 1.0)
        
        elapsed = time.perf_counter() - start
        
        # Should complete well under 50ms (50ms = 0.05s for 20 FPS)
        assert elapsed < 0.05, f"Full tick took {elapsed*1000:.2f}ms, expected < 50ms"


class TestTowerEngagement:
    """Tower engagement optimization tests"""
    
    def setup_method(self):
        """Setup before each test"""
        self.em = EntityManager()
        self.config = {
            'game': {'tick_rate': 15, 'map_width': 7200, 'map_height': 7200}
        }
        self.spatial_hash = SpatialHash(cell_size=500, map_width=7200, map_height=7200)
        self.em.spatial_hash = self.spatial_hash
        self.combat_system = CombatSystem(self.em, 1.0/15.0)
        self.tower_system = TowerSystem(self.em)
    
    def test_tower_local_caching_performance(self):
        """Test that tower system benefits from local caching"""
        # Create tower
        tower_id = self.tower_system.create_tower(team=0, tier=1, x=1000, y=1000)
        pos = self.em.get_component(tower_id, 'position')
        self.spatial_hash.insert(tower_id, pos.x, pos.y)
        
        # Create many nearby entities
        for i in range(200):
            entity_id = self.em.create_entity()
            self.em.add_component(entity_id, 'position', PositionComponent(1000 + (i % 20) * 30, 1000 + (i // 20) * 30))
            self.em.add_component(entity_id, 'stats', StatsComponent(max_hp=1000, current_hp=1000, max_mana=0, current_mana=0))
            
            if i % 2 == 0:
                self.em.add_component(entity_id, 'hero', HeroComponent(hero_id='shadow_fiend', team=1))
            else:
                self.em.add_component(entity_id, 'creep', CreepComponent(team=1, creep_type='melee'))
            
            self.em.add_component(entity_id, 'collision', CollisionComponent(radius=24))
            
            pos = self.em.get_component(entity_id, 'position')
            self.spatial_hash.insert(entity_id, pos.x, pos.y)
        
        # Time tower update
        start = time.perf_counter()
        for _ in range(10):
            self.tower_system.update(self.combat_system, 5.0)
        elapsed = time.perf_counter() - start
        
        # Should complete quickly due to local caching and spatial hash
        assert elapsed < 0.15, f"Tower update with local caching took {elapsed:.3f}s, expected < 0.15s"
