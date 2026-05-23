import pytest
import numpy as np
from engine.ecs.entity_manager import EntityManager
from engine.ecs.components import *


class TestCreepSystem:
    """Test creep spawning and AI"""
    
    def setup_method(self):
        """Setup before each test"""
        self.em = EntityManager()
        self.config = {
            'game': {'tick_rate': 15, 'map_width': 7200, 'map_height': 7200}
        }
    
    def test_creep_spawning(self):
        """Test creep wave spawning"""
        # Note: Uncomment when CreepSpawner is in a separate file
        from engine.systems.creep_system import CreepSpawner
        
        spawner = CreepSpawner(self.em, self.config)
        
        # Spawn wave
        spawner.spawn_wave(team=0, lane='mid')
        
        # Should have 4 creeps (3 melee + 1 ranged)
        creeps = self.em.get_entities_with_component('creep')
        assert len(creeps) == 4
        
        # Check types
        melee_count = 0
        ranged_count = 0
        for creep_id in creeps:
            creep = self.em.get_component(creep_id, 'creep')
            if creep.creep_type == 'melee':
                melee_count += 1
            elif creep.creep_type == 'ranged':
                ranged_count += 1
        
        assert melee_count == 3
        assert ranged_count == 1
        pass
    
    def test_creep_stats(self):
        """Test creep have correct stats"""
        # Test melee creep stats
        entity_id = self.em.create_entity()
        self.em.add_component(entity_id, 'stats', StatsComponent(
            max_hp=550, current_hp=550, max_mana=0, current_mana=0
        ))
        self.em.add_component(entity_id, 'combat', CombatComponent(
            damage_min=19.8, damage_max=24.2, attack_range=128,
            attack_speed=1.0, attack_cooldown=1.0
        ))
        self.em.add_component(entity_id, 'creep', CreepComponent(
            team=0, creep_type='melee', gold_value=40, xp_value=62
        ))
        
        stats = self.em.get_component(entity_id, 'stats')
        combat = self.em.get_component(entity_id, 'combat')
        creep = self.em.get_component(entity_id, 'creep')
        
        assert stats.max_hp == 550
        assert combat.attack_range == 128
        assert creep.gold_value == 40

    def test_melee_creep_applies_direct_damage(self):
        """Test melee creeps apply damage directly without projectiles"""
        from engine.systems.creep_system import CreepSpawner, CreepAI
        from engine.systems.combat_system import CombatSystem
        from engine.systems.movement_system import MovementSystem

        spawner = CreepSpawner(self.em, self.config)
        movement_system = MovementSystem(self.em, 1.0/15.0)
        combat_system = CombatSystem(self.em, 1.0/15.0)

        creep_ai = CreepAI(self.em, spawner)

        # Create a melee creep
        creep_id = spawner.create_creep(team=0, creep_type='melee', x=0, y=0, waypoints=[])

        # Create enemy hero
        hero_id = self.em.create_entity()
        self.em.add_component(hero_id, 'position', PositionComponent(50, 0))
        self.em.add_component(hero_id, 'stats', StatsComponent(
            max_hp=1000, current_hp=1000, max_mana=0, current_mana=0
        ))
        self.em.add_component(hero_id, 'hero', HeroComponent(hero_id='shadow_fiend', team=1))
        self.em.add_component(hero_id, 'collision', CollisionComponent(radius=24))

        hero_stats = self.em.get_component(hero_id, 'stats')
        initial_hp = hero_stats.current_hp

        # Update creep AI - should attack with direct damage
        for _ in range(10):
            combat_system.current_time += 1.0
            creep_ai.update(movement_system, combat_system, combat_system.current_time)

        # Melee creep should NOT have created a projectile
        projectiles = self.em.get_entities_with_component('projectile')
        assert len(projectiles) == 0, "Melee creep should not create projectiles"

        # Hero should have taken some direct damage (multiple attacks)
        assert hero_stats.current_hp < initial_hp
        # Damage is 19.8-24.2 per attack, ~10 attacks total
        expected_damage = 10 * 22  # roughly
        assert initial_hp - hero_stats.current_hp >= expected_damage * 0.8

    def test_ranged_creep_throws_projectile(self):
        """Test ranged creeps throw projectiles instead of direct damage"""
        from engine.systems.creep_system import CreepSpawner, CreepAI
        from engine.systems.combat_system import CombatSystem
        from engine.systems.movement_system import MovementSystem

        spawner = CreepSpawner(self.em, self.config)
        movement_system = MovementSystem(self.em, 1.0/15.0)
        combat_system = CombatSystem(self.em, 1.0/15.0)

        creep_ai = CreepAI(self.em, spawner)

        # Create a ranged creep
        creep_id = spawner.create_creep(team=0, creep_type='ranged', x=0, y=0, waypoints=[])

        # Create enemy hero
        hero_id = self.em.create_entity()
        self.em.add_component(hero_id, 'position', PositionComponent(200, 0))
        self.em.add_component(hero_id, 'stats', StatsComponent(
            max_hp=1000, current_hp=1000, max_mana=0, current_mana=0
        ))
        self.em.add_component(hero_id, 'hero', HeroComponent(hero_id='shadow_fiend', team=1))
        self.em.add_component(hero_id, 'collision', CollisionComponent(radius=24))

        # Update creep AI
        for _ in range(10):
            combat_system.current_time += 1.0
            creep_ai.update(movement_system, combat_system, combat_system.current_time)

        # Ranged creep SHOULD have created a projectile
        projectiles = self.em.get_entities_with_component('projectile')
        assert len(projectiles) > 0, "Ranged creep should create projectiles"

    def test_creep_attacks_all_enemies_in_range(self):
        """Test creep attacks all enemies within attack range"""
        from engine.systems.creep_system import CreepSpawner, CreepAI
        from engine.systems.combat_system import CombatSystem
        from engine.systems.movement_system import MovementSystem

        spawner = CreepSpawner(self.em, self.config)
        movement_system = MovementSystem(self.em, 1.0/15.0)
        combat_system = CombatSystem(self.em, 1.0/15.0)

        creep_ai = CreepAI(self.em, spawner)

        # Create a ranged creep
        creep_id = spawner.create_creep(team=0, creep_type='ranged', x=0, y=0, waypoints=[])

        # Create multiple enemy heroes in attack range (ranged creep range is 500)
        hero1 = self.em.create_entity()
        self.em.add_component(hero1, 'position', PositionComponent(200, 0))
        self.em.add_component(hero1, 'stats', StatsComponent(
            max_hp=1000, current_hp=1000, max_mana=0, current_mana=0
        ))
        self.em.add_component(hero1, 'hero', HeroComponent(hero_id='shadow_fiend', team=1))
        self.em.add_component(hero1, 'collision', CollisionComponent(radius=24))

        hero2 = self.em.create_entity()
        self.em.add_component(hero2, 'position', PositionComponent(-200, 0))
        self.em.add_component(hero2, 'stats', StatsComponent(
            max_hp=1000, current_hp=1000, max_mana=0, current_mana=0
        ))
        self.em.add_component(hero2, 'hero', HeroComponent(hero_id='shadow_fiend', team=1))
        self.em.add_component(hero2, 'collision', CollisionComponent(radius=24))

        # Update creep AI
        combat_system.current_time = 5.0
        creep_ai.update(movement_system, combat_system, combat_system.current_time)

        # Should have created projectiles for both enemies
        projectiles = self.em.get_entities_with_component('projectile')
        assert len(projectiles) >= 2, f"Creep should attack all enemies in range, got {len(projectiles)}"

    def test_creep_only_attacks_enemies_in_range(self):
        """Test creep does not attack enemies outside attack range"""
        from engine.systems.creep_system import CreepSpawner, CreepAI
        from engine.systems.combat_system import CombatSystem
        from engine.systems.movement_system import MovementSystem

        spawner = CreepSpawner(self.em, self.config)
        movement_system = MovementSystem(self.em, 1.0/15.0)
        combat_system = CombatSystem(self.em, 1.0/15.0)

        creep_ai = CreepAI(self.em, spawner)

        # Create a ranged creep
        creep_id = spawner.create_creep(team=0, creep_type='ranged', x=0, y=0, waypoints=[])

        # Create enemy in attack range
        hero_in_range = self.em.create_entity()
        self.em.add_component(hero_in_range, 'position', PositionComponent(200, 0))
        self.em.add_component(hero_in_range, 'stats', StatsComponent(
            max_hp=1000, current_hp=1000, max_mana=0, current_mana=0
        ))
        self.em.add_component(hero_in_range, 'hero', HeroComponent(hero_id='shadow_fiend', team=1))
        self.em.add_component(hero_in_range, 'collision', CollisionComponent(radius=24))

        # Create enemy outside attack range
        hero_out_of_range = self.em.create_entity()
        self.em.add_component(hero_out_of_range, 'position', PositionComponent(800, 0))
        self.em.add_component(hero_out_of_range, 'stats', StatsComponent(
            max_hp=1000, current_hp=1000, max_mana=0, current_mana=0
        ))
        self.em.add_component(hero_out_of_range, 'hero', HeroComponent(hero_id='shadow_fiend', team=1))
        self.em.add_component(hero_out_of_range, 'collision', CollisionComponent(radius=24))

        # Update creep AI
        combat_system.current_time = 5.0
        creep_ai.update(movement_system, combat_system, combat_system.current_time)

        # Should have created projectile only for enemy in range
        projectiles = self.em.get_entities_with_component('projectile')
        assert len(projectiles) == 1, f"Creep should only attack enemy in range, got {len(projectiles)}"

        proj = self.em.get_component(projectiles[0], 'projectile')
        assert proj.target_x == 200, "Creep should target the enemy in range"

    def test_creep_prioritizes_creeps_over_heroes(self):
        """Test creep prioritizes attacking creeps over heroes when both in range"""
        from engine.systems.creep_system import CreepSpawner, CreepAI
        from engine.systems.combat_system import CombatSystem
        from engine.systems.movement_system import MovementSystem

        spawner = CreepSpawner(self.em, self.config)
        movement_system = MovementSystem(self.em, 1.0/15.0)
        combat_system = CombatSystem(self.em, 1.0/15.0)

        creep_ai = CreepAI(self.em, spawner)

        # Create a melee creep (attack range is 128)
        creep_id = spawner.create_creep(team=0, creep_type='melee', x=0, y=0, waypoints=[])

        # Create enemy creep in attack range
        enemy_creep_id = spawner.create_creep(team=1, creep_type='melee', x=50, y=0, waypoints=[])

        # Create enemy hero in attack range
        hero_id = self.em.create_entity()
        self.em.add_component(hero_id, 'position', PositionComponent(-50, 0))
        self.em.add_component(hero_id, 'stats', StatsComponent(
            max_hp=1000, current_hp=1000, max_mana=0, current_mana=0
        ))
        self.em.add_component(hero_id, 'hero', HeroComponent(hero_id='shadow_fiend', team=1))
        self.em.add_component(hero_id, 'collision', CollisionComponent(radius=24))

        enemy_creep_stats = self.em.get_component(enemy_creep_id, 'stats')
        hero_stats = self.em.get_component(hero_id, 'stats')
        initial_creep_hp = enemy_creep_stats.current_hp
        initial_hero_hp = hero_stats.current_hp

        # Update creep AI
        combat_system.current_time = 5.0
        creep_ai.update(movement_system, combat_system, combat_system.current_time)

        # Enemy creep should have taken damage, hero should not
        assert enemy_creep_stats.current_hp < initial_creep_hp, "Enemy creep should have taken damage"
        assert hero_stats.current_hp == initial_hero_hp, "Hero should not have taken damage when creeps are present"

    def test_melee_creep_attacks_all_enemies_in_range(self):
        """Test melee creep attacks all enemies within attack range with direct damage"""
        from engine.systems.creep_system import CreepSpawner, CreepAI
        from engine.systems.combat_system import CombatSystem
        from engine.systems.movement_system import MovementSystem

        spawner = CreepSpawner(self.em, self.config)
        movement_system = MovementSystem(self.em, 1.0/15.0)
        combat_system = CombatSystem(self.em, 1.0/15.0)

        creep_ai = CreepAI(self.em, spawner)

        # Create a melee creep (attack range is 128)
        creep_id = spawner.create_creep(team=0, creep_type='melee', x=0, y=0, waypoints=[])

        # Create multiple enemy heroes in attack range
        hero1 = self.em.create_entity()
        self.em.add_component(hero1, 'position', PositionComponent(50, 0))
        self.em.add_component(hero1, 'stats', StatsComponent(
            max_hp=1000, current_hp=1000, max_mana=0, current_mana=0
        ))
        self.em.add_component(hero1, 'hero', HeroComponent(hero_id='shadow_fiend', team=1))
        self.em.add_component(hero1, 'collision', CollisionComponent(radius=24))

        hero2 = self.em.create_entity()
        self.em.add_component(hero2, 'position', PositionComponent(-50, 0))
        self.em.add_component(hero2, 'stats', StatsComponent(
            max_hp=1000, current_hp=1000, max_mana=0, current_mana=0
        ))
        self.em.add_component(hero2, 'hero', HeroComponent(hero_id='shadow_fiend', team=1))
        self.em.add_component(hero2, 'collision', CollisionComponent(radius=24))

        hero1_stats = self.em.get_component(hero1, 'stats')
        hero2_stats = self.em.get_component(hero2, 'stats')
        initial_hp1 = hero1_stats.current_hp
        initial_hp2 = hero2_stats.current_hp

        # Update creep AI
        combat_system.current_time = 5.0
        creep_ai.update(movement_system, combat_system, combat_system.current_time)

        # Both heroes should have taken damage (melee creep attacks both)
        assert hero1_stats.current_hp < initial_hp1, "Hero1 should have taken damage"
        assert hero2_stats.current_hp < initial_hp2, "Hero2 should have taken damage"

        # Melee creep should NOT have created any projectiles
        projectiles = self.em.get_entities_with_component('projectile')
        assert len(projectiles) == 0, "Melee creep should not create projectiles"