"""Tests for movement system"""
import pytest
import numpy as np
from engine.ecs.entity_manager import EntityManager
from engine.ecs.components import PositionComponent, MovementComponent
from engine.systems.movement_system import MovementSystem


class TestMovementSystem:
    """Test movement system and determinism"""
    
    def setup_method(self):
        """Setup before each test"""
        self.em = EntityManager()
        self.dt = 1.0 / 15.0  # 15 ticks per second
        self.movement_system = MovementSystem(self.em, self.dt)
    
    def test_basic_movement(self):
        """Test basic movement to target"""
        # Create entity with position and movement
        entity_id = self.em.create_entity()
        self.em.add_component(entity_id, 'position', PositionComponent(0, 0))
        self.em.add_component(entity_id, 'movement', MovementComponent(move_speed=300))
        
        # Set target
        self.movement_system.set_move_target(entity_id, 100, 0)
        
        position = self.em.get_component(entity_id, 'position')
        movement = self.em.get_component(entity_id, 'movement')
        
        assert movement.is_moving
        assert movement.target_x == 100
        assert movement.target_y == 0
        
        # Update once
        self.movement_system.update()
        
        # Should have moved (300 units/sec * 1/15 sec = 20 units)
        expected_distance = 300 * self.dt
        assert position.x == pytest.approx(expected_distance, abs=0.01)
        assert position.y == pytest.approx(0, abs=0.01)
        assert movement.is_moving  # Still moving
    
    def test_reach_target(self):
        """Test reaching movement target"""
        entity_id = self.em.create_entity()
        self.em.add_component(entity_id, 'position', PositionComponent(0, 0))
        self.em.add_component(entity_id, 'movement', MovementComponent(move_speed=300))
        
        # Set close target
        self.movement_system.set_move_target(entity_id, 10, 0)
        
        # Update until reached
        for _ in range(10):
            self.movement_system.update()
            movement = self.em.get_component(entity_id, 'movement')
            if not movement.is_moving:
                break
        
        position = self.em.get_component(entity_id, 'position')
        movement = self.em.get_component(entity_id, 'movement')
        
        # Should have reached target
        assert not movement.is_moving
        assert position.x == pytest.approx(10, abs=0.1)
        assert position.y == pytest.approx(0, abs=0.1)
    
    def test_diagonal_movement(self):
        """Test movement at 45 degree angle"""
        entity_id = self.em.create_entity()
        self.em.add_component(entity_id, 'position', PositionComponent(0, 0))
        self.em.add_component(entity_id, 'movement', MovementComponent(move_speed=300))
        
        # Set diagonal target
        self.movement_system.set_move_target(entity_id, 100, 100)
        
        # Update once
        self.movement_system.update()
        
        position = self.em.get_component(entity_id, 'position')
        
        # Should move equal amounts in x and y
        expected_distance = 300 * self.dt
        expected_per_axis = expected_distance / np.sqrt(2)
        
        assert position.x == pytest.approx(expected_per_axis, abs=0.01)
        assert position.y == pytest.approx(expected_per_axis, abs=0.01)
    
    def test_stop_movement(self):
        """Test stopping movement"""
        entity_id = self.em.create_entity()
        self.em.add_component(entity_id, 'position', PositionComponent(0, 0))
        self.em.add_component(entity_id, 'movement', MovementComponent(move_speed=300))
        
        # Start moving
        self.movement_system.set_move_target(entity_id, 1000, 0)
        movement = self.em.get_component(entity_id, 'movement')
        assert movement.is_moving
        
        # Stop
        self.movement_system.stop_movement(entity_id)
        movement = self.em.get_component(entity_id, 'movement')
        
        assert not movement.is_moving
        assert movement.target_x is None
        assert movement.target_y is None
    
    def test_determinism(self):
        """Test that movement is deterministic"""
        # Create two identical entities
        e1 = self.em.create_entity()
        self.em.add_component(e1, 'position', PositionComponent(0, 0))
        self.em.add_component(e1, 'movement', MovementComponent(move_speed=300))
        
        e2 = self.em.create_entity()
        self.em.add_component(e2, 'position', PositionComponent(0, 0))
        self.em.add_component(e2, 'movement', MovementComponent(move_speed=300))
        
        # Set same target
        self.movement_system.set_move_target(e1, 500, 500)
        self.movement_system.set_move_target(e2, 500, 500)
        
        # Update multiple times
        for _ in range(20):
            self.movement_system.update()
        
        pos1 = self.em.get_component(e1, 'position')
        pos2 = self.em.get_component(e2, 'position')
        
        # Positions should be identical (deterministic)
        assert pos1.x == pos2.x
        assert pos1.y == pos2.y
    
    def test_movement_speed_scaling(self):
        """Test different movement speeds"""
        # Fast entity
        e_fast = self.em.create_entity()
        self.em.add_component(e_fast, 'position', PositionComponent(0, 0))
        self.em.add_component(e_fast, 'movement', MovementComponent(move_speed=600))
        
        # Slow entity
        e_slow = self.em.create_entity()
        self.em.add_component(e_slow, 'position', PositionComponent(0, 0))
        self.em.add_component(e_slow, 'movement', MovementComponent(move_speed=300))
        
        # Set same target
        self.movement_system.set_move_target(e_fast, 1000, 0)
        self.movement_system.set_move_target(e_slow, 1000, 0)
        
        # Update once
        self.movement_system.update()
        
        pos_fast = self.em.get_component(e_fast, 'position')
        pos_slow = self.em.get_component(e_slow, 'position')
        
        # Fast should be 2x further
        assert pos_fast.x == pytest.approx(pos_slow.x * 2, abs=0.01)
    
    def test_multiple_entities(self):
        """Test moving multiple entities simultaneously"""
        entities = []
        
        for i in range(5):
            entity_id = self.em.create_entity()
            self.em.add_component(entity_id, 'position', PositionComponent(0, i * 100))
            self.em.add_component(entity_id, 'movement', MovementComponent(move_speed=300))
            self.movement_system.set_move_target(entity_id, 1000, i * 100)
            entities.append(entity_id)
        
        # Update 50 times
        for _ in range(50):
            self.movement_system.update()
        
        # All should have moved
        for entity_id in entities:
            position = self.em.get_component(entity_id, 'position')
            assert position.x > 0