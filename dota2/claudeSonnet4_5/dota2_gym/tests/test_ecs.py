"""Tests for ECS (Entity Component System)"""
import pytest
from engine.ecs.entity_manager import EntityManager
from engine.ecs.components import (
    PositionComponent, VelocityComponent, MovementComponent,
    StatsComponent, HeroComponent, CombatComponent
)


class TestEntityManager:
    """Test Entity Manager"""
    
    def setup_method(self):
        """Setup before each test"""
        self.em = EntityManager()
    
    def test_create_entity(self):
        """Test entity creation"""
        entity_id = self.em.create_entity()
        
        assert entity_id == 0
        assert entity_id in self.em.entities
        
        # Create another
        entity_id2 = self.em.create_entity()
        assert entity_id2 == 1
        assert entity_id2 in self.em.entities
    
    def test_destroy_entity(self):
        """Test entity destruction"""
        entity_id = self.em.create_entity()
        self.em.add_component(entity_id, 'position', PositionComponent(10, 20))
        
        assert entity_id in self.em.entities
        assert self.em.has_component(entity_id, 'position')
        
        self.em.destroy_entity(entity_id)
        
        assert entity_id not in self.em.entities
        assert not self.em.has_component(entity_id, 'position')
    
    def test_add_component(self):
        """Test adding components"""
        entity_id = self.em.create_entity()
        position = PositionComponent(100, 200)
        
        self.em.add_component(entity_id, 'position', position)
        
        assert self.em.has_component(entity_id, 'position')
        retrieved = self.em.get_component(entity_id, 'position')
        assert retrieved.x == 100
        assert retrieved.y == 200
    
    def test_remove_component(self):
        """Test removing components"""
        entity_id = self.em.create_entity()
        self.em.add_component(entity_id, 'position', PositionComponent(10, 20))
        
        assert self.em.has_component(entity_id, 'position')
        
        self.em.remove_component(entity_id, 'position')
        
        assert not self.em.has_component(entity_id, 'position')
        assert self.em.get_component(entity_id, 'position') is None
    
    def test_get_entities_with_component(self):
        """Test querying entities by component"""
        e1 = self.em.create_entity()
        e2 = self.em.create_entity()
        e3 = self.em.create_entity()
        
        self.em.add_component(e1, 'position', PositionComponent(0, 0))
        self.em.add_component(e2, 'position', PositionComponent(10, 10))
        self.em.add_component(e3, 'velocity', VelocityComponent(5, 5))
        
        # Query position
        pos_entities = self.em.get_entities_with_component('position')
        assert len(pos_entities) == 2
        assert e1 in pos_entities
        assert e2 in pos_entities
        assert e3 not in pos_entities
        
        # Query velocity
        vel_entities = self.em.get_entities_with_component('velocity')
        assert len(vel_entities) == 1
        assert e3 in vel_entities
    
    def test_get_entities_with_multiple_components(self):
        """Test querying entities with multiple components"""
        e1 = self.em.create_entity()
        e2 = self.em.create_entity()
        e3 = self.em.create_entity()
        
        self.em.add_component(e1, 'position', PositionComponent(0, 0))
        self.em.add_component(e1, 'velocity', VelocityComponent(1, 1))
        
        self.em.add_component(e2, 'position', PositionComponent(10, 10))
        
        self.em.add_component(e3, 'position', PositionComponent(20, 20))
        self.em.add_component(e3, 'velocity', VelocityComponent(2, 2))
        
        # Query both position and velocity
        entities = self.em.get_entities_with_components('position', 'velocity')
        
        assert len(entities) == 2
        assert e1 in entities
        assert e2 not in entities
        assert e3 in entities
    
    def test_clear(self):
        """Test clearing all entities"""
        e1 = self.em.create_entity()
        e2 = self.em.create_entity()
        self.em.add_component(e1, 'position', PositionComponent(0, 0))
        self.em.add_component(e2, 'position', PositionComponent(10, 10))
        
        assert len(self.em.entities) == 2
        
        self.em.clear()
        
        assert len(self.em.entities) == 0
        assert len(self.em.components) == 0
        assert self.em.next_entity_id == 0


class TestComponents:
    """Test component classes"""
    
    def test_position_component(self):
        """Test PositionComponent"""
        pos = PositionComponent(100.5, 200.7)
        
        assert pos.x == 100.5
        assert pos.y == 200.7
        
        # Test as_array
        arr = pos.as_array()
        assert arr[0] == 100.5
        assert arr[1] == 200.7
        
        # Test distance_to
        pos2 = PositionComponent(103.5, 204.7)
        distance = pos.distance_to(pos2)
        assert abs(distance - 5.0) < 0.01  # 3-4-5 triangle
    
    def test_stats_component(self):
        """Test StatsComponent"""
        stats = StatsComponent(
            max_hp=1000,
            current_hp=1000,
            max_mana=500,
            current_mana=500
        )
        
        assert stats.is_alive()
        
        # Take damage
        damage = stats.take_damage(300)
        assert damage == 300
        assert stats.current_hp == 700
        assert stats.is_alive()
        
        # Kill
        stats.take_damage(700)
        assert stats.current_hp == 0
        assert not stats.is_alive()
    
    def test_combat_component(self):
        """Test CombatComponent"""
        combat = CombatComponent(
            damage_min=50,
            damage_max=60,
            attack_range=500,
            attack_speed=1.7,
            attack_cooldown=1.7
        )
        
        # Should be able to attack at time 0
        assert combat.can_attack(0.0)
        
        # Attack at time 0
        combat.last_attack_time = 0.0
        
        # Should not be able to attack at time 1.0
        assert not combat.can_attack(1.0)
        
        # Should be able to attack at time 1.7
        assert combat.can_attack(1.7)
        
        # Test damage range
        for _ in range(10):
            damage = combat.get_random_damage()
            assert 50 <= damage <= 60
    
    def test_hero_component(self):
        """Test HeroComponent"""
        hero = HeroComponent(
            hero_id='shadow_fiend',
            level=1,
            strength=20,
            agility=20,
            intelligence=20,
            souls=0,
            team=0
        )
        
        assert hero.hero_id == 'shadow_fiend'
        assert hero.level == 1
        assert hero.souls == 0
        assert hero.team == 0
        
        # Add souls
        hero.souls = 10
        assert hero.souls == 10