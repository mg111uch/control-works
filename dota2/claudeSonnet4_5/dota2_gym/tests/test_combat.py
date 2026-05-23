"""Tests for combat system"""
import pytest
import numpy as np
from engine.ecs.entity_manager import EntityManager
from engine.ecs.components import (
    PositionComponent, StatsComponent, CombatComponent, 
    HeroComponent, CollisionComponent
)
from engine.systems.combat_system import CombatSystem


class TestCombatSystem:
    """Test combat system"""
    
    def setup_method(self):
        """Setup before each test"""
        self.em = EntityManager()
        self.dt = 1.0 / 15.0
        self.combat_system = CombatSystem(self.em, self.dt)
        self.config = {
            'game': {'tick_rate': 15, 'map_width': 7200, 'map_height': 7200}
        }
    
    def create_test_hero(self, x, y, team):
        """Helper to create a test hero"""
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
        
        return entity_id
    
    def test_projectile_creation(self):
        """Test creating attack projectiles"""
        attacker = self.create_test_hero(0, 0, 0)
        
        # Create projectile
        proj_id = self.combat_system.create_attack_projectile(attacker, 500, 0)
        
        assert proj_id >= 0
        assert self.em.has_component(proj_id, 'projectile')
        assert self.em.has_component(proj_id, 'position')
        
        # Check projectile data
        proj = self.em.get_component(proj_id, 'projectile')
        assert proj.source_entity == attacker
        assert proj.target_x == 500
        assert proj.target_y == 0
        assert proj.team == 0
        assert 50 <= proj.damage <= 60
    
    def test_attack_cooldown(self):
        """Test attack cooldown"""
        attacker = self.create_test_hero(0, 0, 0)
        
        # First attack should succeed
        proj1 = self.combat_system.create_attack_projectile(attacker, 500, 0)
        assert proj1 >= 0
        
        # Immediate second attack should fail (on cooldown)
        proj2 = self.combat_system.create_attack_projectile(attacker, 500, 0)
        assert proj2 == -1
        
        # Advance time past cooldown
        combat = self.em.get_component(attacker, 'combat')
        self.combat_system.current_time = combat.last_attack_time + combat.attack_cooldown + 0.1
        
        # Attack should work now
        proj3 = self.combat_system.create_attack_projectile(attacker, 500, 0)
        assert proj3 >= 0
    
    def test_projectile_movement(self):
        """Test projectile movement"""
        attacker = self.create_test_hero(0, 0, 0)
        
        # Create projectile
        proj_id = self.combat_system.create_attack_projectile(attacker, 1000, 0)
        
        proj_pos = self.em.get_component(proj_id, 'position')
        initial_x = proj_pos.x
        
        # Update combat system
        self.combat_system.update()
        
        # Projectile should have moved
        assert proj_pos.x > initial_x
        
        # Calculate expected movement
        projectile = self.em.get_component(proj_id, 'projectile')
        expected_distance = projectile.speed * self.dt
        actual_distance = proj_pos.x - initial_x
        
        assert actual_distance == pytest.approx(expected_distance, abs=0.1)
    
    def test_projectile_collision(self):
        """Test projectile hitting target"""
        attacker = self.create_test_hero(0, 0, 0)
        target = self.create_test_hero(100, 0, 1)  # Different team
        
        target_stats = self.em.get_component(target, 'stats')
        initial_hp = target_stats.current_hp
        
        # Create projectile aimed at target
        target_pos = self.em.get_component(target, 'position')
        proj_id = self.combat_system.create_attack_projectile(
            attacker, target_pos.x, target_pos.y
        )
        
        # Update until projectile hits or times out
        for _ in range(100):
            self.combat_system.update()
            
            # Check if projectile is destroyed (hit or timeout)
            if not self.em.has_component(proj_id, 'projectile'):
                break
        
        # Target should have taken damage
        assert target_stats.current_hp < initial_hp
        assert 50 <= (initial_hp - target_stats.current_hp) <= 60
    
    def test_projectile_team_check(self):
        """Test projectiles don't hit same team"""
        attacker = self.create_test_hero(0, 0, 0)
        ally = self.create_test_hero(100, 0, 0)  # Same team
        
        ally_stats = self.em.get_component(ally, 'stats')
        initial_hp = ally_stats.current_hp
        
        # Create projectile
        ally_pos = self.em.get_component(ally, 'position')
        proj_id = self.combat_system.create_attack_projectile(
            attacker, ally_pos.x, ally_pos.y
        )
        
        # Update many times
        for _ in range(100):
            self.combat_system.update()
        
        # Ally should not be damaged
        assert ally_stats.current_hp == initial_hp
    
    def test_soul_collection(self):
        """Test Necromastery soul collection on kill"""
        killer = self.create_test_hero(0, 0, 0)
        victim = self.create_test_hero(100, 0, 1)
        
        killer_hero = self.em.get_component(killer, 'hero')
        victim_stats = self.em.get_component(victim, 'stats')
        
        # Set victim to low HP
        victim_stats.current_hp = 10
        
        initial_souls = killer_hero.souls
        
        # Create projectile that will kill
        victim_pos = self.em.get_component(victim, 'position')
        proj_id = self.combat_system.create_attack_projectile(
            killer, victim_pos.x, victim_pos.y
        )
        
        # Update until hit
        for _ in range(100):
            self.combat_system.update()
            if victim_stats.current_hp <= 0:
                break
        
        # Killer should have gained a soul
        assert killer_hero.souls == initial_souls + 1
        assert victim_stats.current_hp <= 0
    
    def test_max_souls_cap(self):
        """Test soul cap at 36"""
        killer = self.create_test_hero(0, 0, 0)
        killer_hero = self.em.get_component(killer, 'hero')
        
        # Set to max souls
        killer_hero.souls = 36
        
        # Kill someone
        victim = self.create_test_hero(100, 0, 1)
        victim_stats = self.em.get_component(victim, 'stats')
        victim_stats.current_hp = 1
        
        # Trigger kill
        self.combat_system._on_hero_killed(victim, killer)
        
        # Should still be at max
        assert killer_hero.souls == 36
    
    def test_projectile_lifetime(self):
        """Test projectiles expire after lifetime"""
        attacker = self.create_test_hero(0, 0, 0)
        
        # Create projectile aimed far away
        proj_id = self.combat_system.create_attack_projectile(attacker, 10000, 0)
        
        projectile = self.em.get_component(proj_id, 'projectile')
        initial_lifetime = projectile.lifetime
        
        # Update once
        self.combat_system.update()
        
        # Lifetime should decrease
        assert projectile.lifetime < initial_lifetime
        
        # Update many times to expire
        for _ in range(200):
            self.combat_system.update()
            if not self.em.has_component(proj_id, 'projectile'):
                break
        
        # Projectile should be destroyed
        assert not self.em.has_component(proj_id, 'projectile')
    
    def test_damage_variation(self):
        """Test damage varies within range"""
        attacker = self.create_test_hero(0, 0, 0)
        combat = self.em.get_component(attacker, 'combat')
        
        damages = []
        for _ in range(20):
            damage = combat.get_random_damage()
            damages.append(damage)
            assert 50 <= damage <= 60
        
        # Should have some variation
        assert len(set(damages)) > 1
    
    def test_multiple_projectiles(self):
        """Test multiple projectiles in flight"""
        attacker1 = self.create_test_hero(0, 0, 0)
        attacker2 = self.create_test_hero(0, 100, 0)
        
        # Create multiple projectiles
        proj1 = self.combat_system.create_attack_projectile(attacker1, 1000, 0)
        
        # Advance time past cooldown for second attacker
        self.combat_system.current_time += 2.0
        proj2 = self.combat_system.create_attack_projectile(attacker2, 1000, 100)
        
        assert proj1 >= 0
        assert proj2 >= 0
        assert proj1 != proj2
        
        # Both should exist
        assert self.em.has_component(proj1, 'projectile')
        assert self.em.has_component(proj2, 'projectile')
        
        # Update - both should move
        self.combat_system.update()
        
        pos1 = self.em.get_component(proj1, 'position')
        pos2 = self.em.get_component(proj2, 'position')

        assert pos1.x > 0
        assert pos2.x > 0

    def test_tower_damage_from_projectile(self):
        """Test that projectiles can damage towers"""
        from engine.ecs.components import TowerComponent

        attacker = self.create_test_hero(0, 0, 0)

        # Create a tower
        tower_id = self.em.create_entity()
        self.em.add_component(tower_id, 'position', PositionComponent(100, 0))
        self.em.add_component(tower_id, 'stats', StatsComponent(
            max_hp=1800,
            current_hp=1800,
            max_mana=0,
            current_mana=0
        ))
        self.em.add_component(tower_id, 'collision', CollisionComponent(radius=64))
        self.em.add_component(tower_id, 'tower', TowerComponent(
            team=1,
            tier=1,
            attack_damage=100,
            attack_range=700.0,
            attack_cooldown=1.0
        ))

        tower_stats = self.em.get_component(tower_id, 'stats')
        initial_hp = tower_stats.current_hp

        # Create projectile aimed at tower
        tower_pos = self.em.get_component(tower_id, 'position')
        proj_id = self.combat_system.create_attack_projectile(
            attacker, tower_pos.x, tower_pos.y
        )

        # Update until projectile hits
        for _ in range(100):
            self.combat_system.update()
            if not self.em.has_component(proj_id, 'projectile'):
                break

        # Tower should have taken damage
        assert tower_stats.current_hp < initial_hp
        assert 50 <= (initial_hp - tower_stats.current_hp) <= 60

    def test_projectile_tracks_target_entity(self):
        """Test that projectiles track the target entity's position"""
        attacker = self.create_test_hero(0, 0, 0)
        target = self.create_test_hero(100, 0, 1)

        # Create projectile with target entity
        target_pos = self.em.get_component(target, 'position')
        proj_id = self.combat_system.create_attack_projectile(
            attacker, target_pos.x, target_pos.y, target
        )

        projectile = self.em.get_component(proj_id, 'projectile')
        assert projectile.target_entity == target

        # Move target to new position
        target_pos.x = 200
        target_pos.y = 100

        # Update projectile - it should update target position
        self.combat_system.update()

        # Target position in projectile should be updated
        assert projectile.target_x == 200
        assert projectile.target_y == 100

    def test_projectile_target_entity_destroyed(self):
        """Test projectile behavior when target entity is destroyed"""
        from engine.ecs.components import TowerComponent

        attacker = self.create_test_hero(0, 0, 0)

        # Create a tower as target
        tower_id = self.em.create_entity()
        self.em.add_component(tower_id, 'position', PositionComponent(100, 0))
        self.em.add_component(tower_id, 'stats', StatsComponent(
            max_hp=100,
            current_hp=100,
            max_mana=0,
            current_mana=0
        ))
        self.em.add_component(tower_id, 'collision', CollisionComponent(radius=64))
        self.em.add_component(tower_id, 'tower', TowerComponent(
            team=1,
            tier=1,
            attack_damage=100,
            attack_range=700.0,
            attack_cooldown=1.0
        ))

        # Create projectile with target entity
        tower_pos = self.em.get_component(tower_id, 'position')
        proj_id = self.combat_system.create_attack_projectile(
            attacker, tower_pos.x, tower_pos.y, tower_id
        )

        # Destroy target entity
        self.em.destroy_entity(tower_id)

        # Projectile should still exist and continue to last known position
        assert self.em.has_component(proj_id, 'projectile')

        # Update projectile until lifetime expires (10 seconds / (1/15) = 150 updates)
        for _ in range(200):
            self.combat_system.update()
            if not self.em.has_component(proj_id, 'projectile'):
                break

        # Projectile should eventually be destroyed (lifetime expires)
        assert not self.em.has_component(proj_id, 'projectile')

    def test_tower_attacks_hero(self):
        """Test tower can find and attack enemy hero within range"""
        from engine.ecs.components import TowerComponent
        from engine.systems.tower_system import TowerSystem

        # Create tower system
        tower_system = TowerSystem(self.em)

        # Create a tower
        tower_id = tower_system.create_tower(team=0, tier=1, x=1000, y=1000)

        # Create enemy hero in range (within 700 units)
        hero_id = self.em.create_entity()
        self.em.add_component(hero_id, 'position', PositionComponent(1500, 1000))
        self.em.add_component(hero_id, 'stats', StatsComponent(
            max_hp=1000, current_hp=1000, max_mana=500, current_mana=500
        ))
        self.em.add_component(hero_id, 'combat', CombatComponent(
            damage_min=50, damage_max=60, attack_range=500,
            attack_speed=1.7, attack_cooldown=1.7
        ))
        self.em.add_component(hero_id, 'hero', HeroComponent(
            hero_id='shadow_fiend', team=1
        ))
        self.em.add_component(hero_id, 'collision', CollisionComponent(radius=24))

        hero_stats = self.em.get_component(hero_id, 'stats')
        initial_hp = hero_stats.current_hp

        # Update tower - should attack hero
        tower_system.update(self.combat_system, 5.0)

        # Tower should have created a projectile
        projectiles = self.em.get_entities_with_component('projectile')
        assert len(projectiles) > 0, "Tower should create projectile when attacking"

        # Advance time and let projectile hit
        for _ in range(100):
            self.combat_system.update()
            if not self.em.has_component(projectiles[0], 'projectile'):
                break

        # Hero should have taken damage
        assert hero_stats.current_hp < initial_hp

    def test_tower_finds_nearest_enemy(self):
        """Test tower prioritizes nearest enemy within range"""
        from engine.ecs.components import TowerComponent
        from engine.systems.tower_system import TowerSystem

        # Create tower system
        tower_system = TowerSystem(self.em)

        # Create a tower at origin
        tower_id = tower_system.create_tower(team=0, tier=1, x=1000, y=1000)

        # Create two enemy heroes in range
        hero_near = self.em.create_entity()
        self.em.add_component(hero_near, 'position', PositionComponent(1200, 1000))  # 200 away
        self.em.add_component(hero_near, 'stats', StatsComponent(
            max_hp=1000, current_hp=1000, max_mana=500, current_mana=500
        ))
        self.em.add_component(hero_near, 'hero', HeroComponent(
            hero_id='shadow_fiend', team=1
        ))

        hero_far = self.em.create_entity()
        self.em.add_component(hero_far, 'position', PositionComponent(1600, 1000))  # 600 away
        self.em.add_component(hero_far, 'stats', StatsComponent(
            max_hp=1000, current_hp=1000, max_mana=500, current_mana=500
        ))
        self.em.add_component(hero_far, 'hero', HeroComponent(
            hero_id='shadow_fiend', team=1
        ))

        # Update tower
        tower_system.update(self.combat_system, 5.0)

        # Tower should have attacked the nearest enemy
        projectiles = self.em.get_entities_with_component('projectile')
        assert len(projectiles) > 0

        # Check projectile target - should be the nearer hero (200 away, not 600)
        proj = self.em.get_component(projectiles[0], 'projectile')
        assert proj.target_x == 1200, "Tower should target nearest enemy"

    def test_projectile_destroyed_when_source_dies(self):
        """Test projectile is destroyed when source entity dies"""
        from engine.systems.creep_system import CreepSpawner, CreepAI
        from engine.systems.movement_system import MovementSystem

        spawner = CreepSpawner(self.em, self.config)
        movement_system = MovementSystem(self.em, 1.0/15.0)

        creep_ai = CreepAI(self.em, spawner)

        # Create a ranged creep
        creep_id = spawner.create_creep(team=0, creep_type='ranged', x=0, y=0, waypoints=[])

        # Create enemy hero in range
        hero_id = self.em.create_entity()
        self.em.add_component(hero_id, 'position', PositionComponent(200, 0))
        self.em.add_component(hero_id, 'stats', StatsComponent(
            max_hp=1000, current_hp=1000, max_mana=0, current_mana=0
        ))
        self.em.add_component(hero_id, 'hero', HeroComponent(hero_id='shadow_fiend', team=1))
        self.em.add_component(hero_id, 'collision', CollisionComponent(radius=24))

        # Update creep AI to make it attack
        self.combat_system.current_time = 5.0
        creep_ai.update(movement_system, self.combat_system, self.combat_system.current_time)

        # Should have created a projectile
        projectiles = self.em.get_entities_with_component('projectile')
        assert len(projectiles) > 0, "Ranged creep should create projectile"
        proj_id = projectiles[0]

        # Kill the creep
        creep_stats = self.em.get_component(creep_id, 'stats')
        creep_stats.current_hp = 0

        # Update combat system - projectile should be destroyed
        self.combat_system.update()

        # Projectile should be destroyed when source dies
        assert not self.em.has_component(proj_id, 'projectile'), "Projectile should be destroyed when source dies"

    def test_projectile_stays_when_source_survives(self):
        """Test projectile persists when source entity is alive"""
        from engine.systems.creep_system import CreepSpawner, CreepAI
        from engine.systems.movement_system import MovementSystem

        spawner = CreepSpawner(self.em, self.config)
        movement_system = MovementSystem(self.em, 1.0/15.0)

        creep_ai = CreepAI(self.em, spawner)

        # Create a ranged creep
        creep_id = spawner.create_creep(team=0, creep_type='ranged', x=0, y=0, waypoints=[])

        # Create enemy hero in range (within aggro_range of 500)
        hero_id = self.em.create_entity()
        self.em.add_component(hero_id, 'position', PositionComponent(200, 0))
        self.em.add_component(hero_id, 'stats', StatsComponent(
            max_hp=1000, current_hp=1000, max_mana=0, current_mana=0
        ))
        self.em.add_component(hero_id, 'hero', HeroComponent(hero_id='shadow_fiend', team=1))
        self.em.add_component(hero_id, 'collision', CollisionComponent(radius=24))

        # Update creep AI to make it attack
        self.combat_system.current_time = 5.0
        creep_ai.update(movement_system, self.combat_system, self.combat_system.current_time)

        # Should have created a projectile
        projectiles = self.em.get_entities_with_component('projectile')
        assert len(projectiles) > 0, "Ranged creep should create projectile"
        proj_id = projectiles[0]

        # Verify creep is still alive
        creep_stats = self.em.get_component(creep_id, 'stats')
        assert creep_stats.is_alive(), "Creep should be alive"

        # Projectile should still exist since creep is alive (check immediately)
        assert self.em.has_component(proj_id, 'projectile'), "Projectile should persist while source is alive"

    def test_projectile_destroyed_when_target_dies(self):
        """Test projectile is destroyed when target entity dies"""
        from engine.ecs.components import TowerComponent
        from engine.systems.tower_system import TowerSystem

        # Create tower system
        tower_system = TowerSystem(self.em)

        # Create a tower
        tower_id = tower_system.create_tower(team=0, tier=1, x=1000, y=1000)

        # Create enemy hero in range
        hero_id = self.em.create_entity()
        self.em.add_component(hero_id, 'position', PositionComponent(1500, 1000))
        self.em.add_component(hero_id, 'stats', StatsComponent(
            max_hp=1000, current_hp=1000, max_mana=500, current_mana=500
        ))
        self.em.add_component(hero_id, 'combat', CombatComponent(
            damage_min=50, damage_max=60, attack_range=500,
            attack_speed=1.7, attack_cooldown=1.7
        ))
        self.em.add_component(hero_id, 'hero', HeroComponent(
            hero_id='shadow_fiend', team=1
        ))
        self.em.add_component(hero_id, 'collision', CollisionComponent(radius=24))

        # Update tower - should attack hero
        self.combat_system.current_time = 5.0
        tower_system.update(self.combat_system, self.combat_system.current_time)

        # Should have created a projectile
        projectiles = self.em.get_entities_with_component('projectile')
        assert len(projectiles) > 0, "Tower should create projectile when attacking"
        proj_id = projectiles[0]

        # Kill the target hero
        hero_stats = self.em.get_component(hero_id, 'stats')
        hero_stats.current_hp = 0

        # Update combat system - projectile should be destroyed
        self.combat_system.update()

        # Projectile should be destroyed when target dies
        assert not self.em.has_component(proj_id, 'projectile'), "Projectile should be destroyed when target dies"

    def test_tower_attacks_all_enemies_in_range(self):
        """Test tower attacks all enemies within range"""
        from engine.systems.tower_system import TowerSystem

        # Create tower system
        tower_system = TowerSystem(self.em)

        # Create a tower
        tower_id = tower_system.create_tower(team=0, tier=1, x=1000, y=1000)

        # Create multiple enemy heroes in range
        hero1 = self.em.create_entity()
        self.em.add_component(hero1, 'position', PositionComponent(1300, 1000))  # 300 away
        self.em.add_component(hero1, 'stats', StatsComponent(
            max_hp=1000, current_hp=1000, max_mana=500, current_mana=500
        ))
        self.em.add_component(hero1, 'hero', HeroComponent(
            hero_id='shadow_fiend', team=1
        ))
        self.em.add_component(hero1, 'collision', CollisionComponent(radius=24))

        hero2 = self.em.create_entity()
        self.em.add_component(hero2, 'position', PositionComponent(1500, 1200))  # ~500 away, still in range
        self.em.add_component(hero2, 'stats', StatsComponent(
            max_hp=1000, current_hp=1000, max_mana=500, current_mana=500
        ))
        self.em.add_component(hero2, 'hero', HeroComponent(
            hero_id='shadow_fiend', team=1
        ))
        self.em.add_component(hero2, 'collision', CollisionComponent(radius=24))

        # Update tower
        self.combat_system.current_time = 5.0
        tower_system.update(self.combat_system, self.combat_system.current_time)

        # Tower should have created projectiles for both enemies
        projectiles = self.em.get_entities_with_component('projectile')
        assert len(projectiles) >= 2, f"Tower should attack all enemies in range, got {len(projectiles)}"

    def test_tower_only_attacks_enemies_in_range(self):
        """Test tower does not attack enemies outside range"""
        from engine.systems.tower_system import TowerSystem

        # Create tower system
        tower_system = TowerSystem(self.em)

        # Create a tower
        tower_id = tower_system.create_tower(team=0, tier=1, x=1000, y=1000)

        # Create enemy hero in range
        hero_in_range = self.em.create_entity()
        self.em.add_component(hero_in_range, 'position', PositionComponent(1500, 1000))  # 500 away
        self.em.add_component(hero_in_range, 'stats', StatsComponent(
            max_hp=1000, current_hp=1000, max_mana=500, current_mana=500
        ))
        self.em.add_component(hero_in_range, 'hero', HeroComponent(
            hero_id='shadow_fiend', team=1
        ))
        self.em.add_component(hero_in_range, 'collision', CollisionComponent(radius=24))

        # Create enemy hero outside range
        hero_out_of_range = self.em.create_entity()
        self.em.add_component(hero_out_of_range, 'position', PositionComponent(2000, 1000))  # 1000 away, out of range
        self.em.add_component(hero_out_of_range, 'stats', StatsComponent(
            max_hp=1000, current_hp=1000, max_mana=500, current_mana=500
        ))
        self.em.add_component(hero_out_of_range, 'hero', HeroComponent(
            hero_id='shadow_fiend', team=1
        ))
        self.em.add_component(hero_out_of_range, 'collision', CollisionComponent(radius=24))

        # Update tower
        self.combat_system.current_time = 5.0
        tower_system.update(self.combat_system, self.combat_system.current_time)

        # Tower should have created projectile only for enemy in range
        projectiles = self.em.get_entities_with_component('projectile')
        assert len(projectiles) == 1, f"Tower should only attack enemy in range, got {len(projectiles)}"

        proj = self.em.get_component(projectiles[0], 'projectile')
        assert proj.target_x == 1500, "Tower should target the enemy in range"