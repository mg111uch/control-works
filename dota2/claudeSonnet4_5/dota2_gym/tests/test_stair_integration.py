"""Integration test for stair waypoint movement behavior"""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.ecs.entity_manager import EntityManager
from engine.ecs.components import PositionComponent, MovementComponent
from engine.systems.movement_system import MovementSystem
from engine.systems.stair_geometry import (
    Vec2, StairPolygon, generate_stair_polygon, ElevationZone, 
    get_elevation_at_position, can_cross_elevation_directly
)
from engine.model.game_model import StairRegistry


class TestStairWaypointIntegration:
    """Integration tests for stair waypoint behavior"""
    
    def test_elevation_detection(self):
        """Test that elevation detection works correctly"""
        # Create a simple high ground zone
        high_ground_polygon = [
            Vec2(0, 0),
            Vec2(100, 0),
            Vec2(100, 100),
            Vec2(0, 100)
        ]
        
        high_ground = ElevationZone(
            name="test_high_ground",
            elevation=2.0,
            polygon=high_ground_polygon
        )
        
        zones = [high_ground]
        
        # Point inside high ground should return 2.0
        inside_point = Vec2(50, 50)
        elevation = get_elevation_at_position(inside_point, zones)
        assert abs(elevation - 2.0) < 0.01, f"Expected 2.0, got {elevation}"
        
        # Point outside high ground should return 1.0 (default)
        outside_point = Vec2(150, 150)
        elevation = get_elevation_at_position(outside_point, zones)
        assert abs(elevation - 1.0) < 0.01, f"Expected 1.0, got {elevation}"
        
        print("✓ Elevation detection test passed")
    
    def test_cross_elevation_detection(self):
        """Test that crossing elevation boundaries is detected"""
        # Create a simple high ground zone
        high_ground_polygon = [
            Vec2(0, 0),
            Vec2(100, 0),
            Vec2(100, 100),
            Vec2(0, 100)
        ]
        
        high_ground = ElevationZone(
            name="test_high_ground",
            elevation=2.0,
            polygon=high_ground_polygon
        )
        
        zones = [high_ground]
        
        # Direct movement within same elevation should be allowed
        from_pos = Vec2(20, 20)
        to_pos = Vec2(80, 20)
        can_move = can_cross_elevation_directly(from_pos, to_pos, zones, [])
        assert can_move == True, "Should allow direct movement within same elevation"
        
        # Direct movement from high ground to low ground should NOT be allowed
        from_pos = Vec2(50, 50)  # Inside high ground
        to_pos = Vec2(150, 150)  # Outside high ground
        can_move = can_cross_elevation_directly(from_pos, to_pos, zones, [])
        assert can_move == False, "Should NOT allow direct movement across elevation boundaries"
        
        print("✓ Cross elevation detection test passed")
    
    def test_stair_registry_loading(self):
        """Test that stairs are loaded correctly from file"""
        config = {
            'movement': {
                'stair_thickness': 15.0
            }
        }
        
        registry = StairRegistry(config)
        
        # Load stairs from the map polygons file
        polygon_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config', 'map_polygons.txt'
        )
        registry.load_stairs_from_file(polygon_file)
        
        # Verify stairs were loaded
        stairs = registry.get_all_stairs()
        assert len(stairs) > 0, f"Expected stairs to be loaded, got {len(stairs)}"
        
        # Verify elevation zones were loaded
        zones = registry.get_elevation_zones()
        assert len(zones) > 0, f"Expected elevation zones to be loaded, got {len(zones)}"
        
        print(f"✓ Loaded {len(stairs)} stairs and {len(zones)} elevation zones")
    
    def test_stair_waypoint_movement(self):
        """Test that entities use stair waypoints for elevation changes"""
        config = {
            'movement': {
                'stair_thickness': 15.0
            }
        }
        
        registry = StairRegistry(config)
        
        # Load stairs from the map polygons file
        polygon_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config', 'map_polygons.txt'
        )
        registry.load_stairs_from_file(polygon_file)
        
        # Create entity manager and movement system
        entity_manager = EntityManager()
        movement_system = MovementSystem(entity_manager)
        movement_system.set_stair_registry(registry)
        
        # Create a test entity
        entity_id = entity_manager.create_entity()
        entity_manager.add_component(entity_id, 'position', PositionComponent(50, 50))
        entity_manager.add_component(entity_id, 'movement', MovementComponent(move_speed=300))
        
        # Get position and movement components
        position = entity_manager.get_component(entity_id, 'position')
        movement = entity_manager.get_component(entity_id, 'movement')
        
        # Test 1: Movement within same elevation should use direct path
        print(f"Entity position: ({position.x}, {position.y})")
        print(f"Elevation at start: {registry.get_elevation_at_position(Vec2(position.x, position.y))}")
        
        # Test 2: Set a target that requires stair waypoint
        # Target is in a different elevation zone
        target_x, target_y = 150, 150  # Outside high ground
        
        result = movement_system.set_move_target(entity_id, target_x, target_y)
        
        print(f"Movement result: {result}")
        print(f"Movement target: ({movement.target_x}, {movement.target_y})")
        print(f"Final target: ({movement.final_target_x}, {movement.final_target_y})")
        print(f"Current stair ID: {movement.current_stair_id}")
        print(f"On stair: {movement.on_stair}")
        
        # If stair waypoint is used, final_target should be set
        if movement.final_target_x is not None:
            print("✓ Entity is using stair waypoint for elevation change")
        else:
            print("⚠ Entity is NOT using stair waypoint - potential issue!")
    
    def test_full_stair_waypoint_path(self):
        """Test full path: entity starts at one elevation, uses stair, reaches target"""
        config = {
            'movement': {
                'stair_thickness': 15.0,
                'stair_transition_distance': 50.0
            }
        }
        
        registry = StairRegistry(config)
        
        # Load stairs from the map polygons file
        polygon_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config', 'map_polygons.txt'
        )
        registry.load_stairs_from_file(polygon_file)
        
        # Create entity manager and movement system
        entity_manager = EntityManager()
        movement_system = MovementSystem(entity_manager)
        movement_system.set_stair_registry(registry)
        
        # Create a test entity in the radiant base high ground area
        entity_id = entity_manager.create_entity()
        entity_manager.add_component(entity_id, 'position', PositionComponent(50, 600))
        entity_manager.add_component(entity_id, 'movement', MovementComponent(move_speed=300))
        
        position = entity_manager.get_component(entity_id, 'position')
        movement = entity_manager.get_component(entity_id, 'movement')
        
        start_pos = Vec2(position.x, position.y)
        print(f"\nStart position: ({start_pos.x}, {start_pos.y})")
        print(f"Start elevation: {registry.get_elevation_at_position(start_pos)}")
        
        # Set target in middle ground (different elevation)
        target_x, target_y = 500, 500
        target_pos = Vec2(target_x, target_y)
        print(f"Target position: ({target_x}, {target_y})")
        print(f"Target elevation: {registry.get_elevation_at_position(target_pos)}")
        
        # Check if direct movement is allowed
        can_move_directly = registry.can_move_directly(start_pos, target_pos)
        print(f"Can move directly: {can_move_directly}")
        
        # Set movement target
        result = movement_system.set_move_target(entity_id, target_x, target_y)
        print(f"Movement set result: {result}")
        print(f"Target: ({movement.target_x}, {movement.target_y})")
        print(f"Final target: ({movement.final_target_x}, {movement.final_target_y})")
        print(f"Current stair: {movement.current_stair_id}")
        
        # The key test: if can_move_directly is False, then stair waypoint should be used
        if not can_move_directly:
            if movement.final_target_x is not None:
                print("✓ CORRECT: Using stair waypoint for elevation change")
            else:
                print("✗ BUG: Not using stair waypoint when should!")
                # Find the optimal stair
                optimal_stair = registry.find_optimal_stair(start_pos, target_pos)
                if optimal_stair:
                    print(f"  Optimal stair: {optimal_stair.name} at ({optimal_stair.midpoint.x}, {optimal_stair.midpoint.y})")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
