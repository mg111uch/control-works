"""
Tests for Damage System
"""
import pytest
import constants
from ecs.components import HealthComponent, EnemyComponent, BulletComponent, TowerComponent
from ecs.base import Entity


class TestDamageSystem:
    """Tests for damage system"""
    
    def test_enemy_takes_damage(self):
        """Test enemy takes damage correctly"""
        health = HealthComponent(30)
        assert health.health == 30
        
        # Take 5 damage
        is_dead = health.take_damage(5)
        assert is_dead == False
        assert health.health == 25
    
    def test_enemy_survives_multiple_hits(self):
        """Test enemy survives multiple hits"""
        health = HealthComponent(30)
        
        # Take 5 damage 3 times = 15 total
        health.take_damage(5)
        health.take_damage(5)
        is_dead = health.take_damage(5)
        
        assert is_dead == False
        assert health.health == 15
    
    def test_enemy_dies_at_zero_health(self):
        """Test enemy dies when health reaches zero"""
        health = HealthComponent(30)
        
        # Take 10 damage 3 times = 30 total
        health.take_damage(10)
        health.take_damage(10)
        is_dead = health.take_damage(10)
        
        assert is_dead == True
        assert health.health == 0
    
    def test_enemy_dies_below_zero_health(self):
        """Test enemy dies when health goes below zero"""
        health = HealthComponent(30)
        
        # Take 30 damage - exactly to zero
        is_dead = health.take_damage(30)
        
        assert is_dead == True
        assert health.health == 0
    
    def test_bullet_has_correct_damage(self):
        """Test bullet component has correct damage from config"""
        enemy = Entity(1)
        config = {'bullet_color': (255, 0, 0), 'bullet_size': 3, 'damage': 5}
        
        bullet = BulletComponent(enemy, config)
        
        assert bullet.damage == 5
    
    def test_bullet_damage_from_tower_config(self):
        """Test bullet gets damage from tower config"""
        enemy = Entity(1)
        tower_config = {
            'range': 100,
            'color': (0, 255, 0),
            'cooldown': 1.0,
            'damage': 5,
            'bullet_color': (255, 255, 0),
            'bullet_size': 3
        }
        
        bullet = BulletComponent(enemy, tower_config)
        
        assert bullet.damage == 5
    
    def test_enemy_health_from_wave(self):
        """Test enemy health scales with wave"""
        # Wave 1 enemy
        enemy_comp = EnemyComponent(1)
        assert enemy_comp.max_health == 30  # 20 + 1*10
        
        # Wave 2 enemy
        enemy_comp2 = EnemyComponent(2)
        assert enemy_comp2.max_health == 40  # 20 + 2*10
    
    def test_full_damage_cycle(self):
        """Test full damage cycle: enemy with 30 health takes 5 damage hits"""
        # Create enemy with wave 1 health (30)
        enemy = Entity(1)
        enemy_comp = EnemyComponent(1)
        enemy.add_component(enemy_comp)
        health = HealthComponent(enemy_comp.max_health)
        enemy.add_component(health)
        
        # Create bullet with 5 damage (current artillery damage)
        bullet_config = {'bullet_color': (0, 0, 0), 'bullet_size': 3, 'damage': 5}
        bullet = BulletComponent(enemy, bullet_config)
        
        # Verify starting health
        assert health.health == 30
        
        # Hit 1: 30 - 5 = 25 (alive)
        is_dead = health.take_damage(bullet.damage)
        assert is_dead == False
        assert health.health == 25
        
        # Hit 2: 25 - 5 = 20 (alive)
        is_dead = health.take_damage(bullet.damage)
        assert is_dead == False
        assert health.health == 20
        
        # Hit 3: 20 - 5 = 15 (alive)
        is_dead = health.take_damage(bullet.damage)
        assert is_dead == False
        assert health.health == 15
        
        # Hit 4: 15 - 5 = 10 (alive)
        is_dead = health.take_damage(bullet.damage)
        assert is_dead == False
        assert health.health == 10
        
        # Hit 5: 10 - 5 = 5 (alive)
        is_dead = health.take_damage(bullet.damage)
        assert is_dead == False
        assert health.health == 5
        
        # Hit 6: 5 - 5 = 0 (dead)
        is_dead = health.take_damage(bullet.damage)
        assert is_dead == True
        assert health.health == 0

    def test_integration_tower_to_bullet_damage(self):
        """Test that tower config damage is passed to bullet correctly"""
        # Create a mock tower entity
        tower_entity = Entity(1)
        tower_config = constants.TOWER_TYPES['artillery']
        tower_component = TowerComponent('artillery', tower_config)
        tower_entity.add_component(tower_component)
        
        # Create bullet from tower
        enemy_entity = Entity(2)
        bullet_component = BulletComponent(enemy_entity, tower_component.config)
        
        # Verify damage is correctly passed
        assert bullet_component.damage == tower_config['damage']
        assert bullet_component.damage == 5  # Current artillery damage
