"""Unit tests for stair waypoint functionality"""
import pytest
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.systems.stair_geometry import (
    Vec2, StairPolygon, generate_stair_polygon, is_point_in_polygon,
    point_to_segment_distance, distance_point_to_polygon, 
    find_nearest_stair, calculate_stair_progress
)


class TestVec2:
    """Test Vec2 class"""
    
    def test_vec2_creation(self):
        v = Vec2(1.0, 2.0)
        assert v.x == 1.0
        assert v.y == 2.0
    
    def test_vec2_addition(self):
        v1 = Vec2(1.0, 2.0)
        v2 = Vec2(3.0, 4.0)
        v3 = v1 + v2
        assert v3.x == 4.0
        assert v3.y == 6.0
    
    def test_vec2_subtraction(self):
        v1 = Vec2(5.0, 7.0)
        v2 = Vec2(2.0, 3.0)
        v3 = v1 - v2
        assert v3.x == 3.0
        assert v3.y == 4.0
    
    def test_vec2_multiplication(self):
        v = Vec2(2.0, 3.0)
        v2 = v * 2.0
        assert v2.x == 4.0
        assert v2.y == 6.0
    
    def test_vec2_length(self):
        v = Vec2(3.0, 4.0)
        assert abs(v.length() - 5.0) < 1e-10
    
    def test_vec2_normalize(self):
        v = Vec2(3.0, 4.0)
        v_norm = v.normalize()
        assert abs(v_norm.length() - 1.0) < 1e-10


class TestGenerateStairPolygon:
    """Test stair polygon generation"""
    
    def test_generate_stair_polygon_basic(self):
        """Test basic stair polygon generation"""
        p1 = (0.0, 0.0)
        p2 = (100.0, 0.0)
        thickness = 150.0
        
        polygon = generate_stair_polygon(p1, p2, thickness)
        
        assert len(polygon) == 4
        # Check that we have 4 Vec2 points
        for point in polygon:
            assert isinstance(point, Vec2)
    
    def test_generate_stair_polygon_vertical(self):
        """Test vertical stair polygon generation"""
        p1 = (0.0, 0.0)
        p2 = (0.0, 100.0)
        thickness = 150.0
        
        polygon = generate_stair_polygon(p1, p2, thickness)
        
        assert len(polygon) == 4
        # Vertical line should produce horizontal thickness
        # p1_left and p1_right should be symmetric around x=0
        assert abs(polygon[0].x + polygon[1].x) < 1e-10
        assert abs(polygon[2].x + polygon[3].x) < 1e-10
    
    def test_generate_stair_polygon_zero_length(self):
        """Test that zero-length input returns empty list"""
        p1 = (0.0, 0.0)
        p2 = (0.0, 0.0)
        thickness = 150.0
        
        polygon = generate_stair_polygon(p1, p2, thickness)
        assert len(polygon) == 0


class TestPointInPolygon:
    """Test point-in-polygon detection"""
    
    def test_point_inside_square(self):
        """Test point inside a simple square"""
        # Define a unit square
        square = [
            Vec2(0.0, 0.0),
            Vec2(1.0, 0.0),
            Vec2(1.0, 1.0),
            Vec2(0.0, 1.0)
        ]
        
        # Center point should be inside
        center = Vec2(0.5, 0.5)
        assert is_point_in_polygon(center, square) == True
        
        # Corner point should be on edge (treated as inside)
        corner = Vec2(0.0, 0.0)
        assert is_point_in_polygon(corner, square) == True
    
    def test_point_outside_square(self):
        """Test point outside a simple square"""
        square = [
            Vec2(0.0, 0.0),
            Vec2(1.0, 0.0),
            Vec2(1.0, 1.0),
            Vec2(0.0, 1.0)
        ]
        
        # Point outside should return False
        outside = Vec2(2.0, 2.0)
        assert is_point_in_polygon(outside, square) == False
    
    def test_point_in_stair_polygon(self):
        """Test point inside a stair polygon"""
        # Create a simple stair polygon
        p1 = (100.0, 100.0)
        p2 = (200.0, 100.0)
        thickness = 30.0
        
        polygon = generate_stair_polygon(p1, p2, thickness)
        
        # Midpoint of stair should be inside
        midpoint = Vec2(150.0, 100.0)
        assert is_point_in_polygon(midpoint, polygon) == True
        
        # Point far away should be outside
        far_point = Vec2(500.0, 500.0)
        assert is_point_in_polygon(far_point, polygon) == False
    
    def test_empty_polygon(self):
        """Test that empty polygon returns False"""
        point = Vec2(0.0, 0.0)
        assert is_point_in_polygon(point, []) == False
    
    def test_triangle_polygon(self):
        """Test point in triangle"""
        triangle = [
            Vec2(0.0, 0.0),
            Vec2(1.0, 0.0),
            Vec2(0.5, 1.0)
        ]
        
        # Center should be inside
        center = Vec2(0.5, 0.3)
        assert is_point_in_polygon(center, triangle) == True
        
        # Outside should be False
        outside = Vec2(0.5, 1.5)
        assert is_point_in_polygon(outside, triangle) == False


class TestPointToSegmentDistance:
    """Test point to segment distance calculation"""
    
    def test_point_on_segment(self):
        """Test distance when point is on segment"""
        point = Vec2(0.5, 0.0)
        p1 = Vec2(0.0, 0.0)
        p2 = Vec2(1.0, 0.0)
        
        dist = point_to_segment_distance(point, p1, p2)
        assert dist == 0.0
    
    def test_point_perpendicular_to_segment(self):
        """Test distance when point is perpendicular to segment"""
        point = Vec2(0.5, 0.5)
        p1 = Vec2(0.0, 0.0)
        p2 = Vec2(1.0, 0.0)
        
        dist = point_to_segment_distance(point, p1, p2)
        assert abs(dist - 0.5) < 1e-10
    
    def test_point_beyond_segment_end(self):
        """Test distance when point is beyond segment end"""
        point = Vec2(1.5, 0.0)
        p1 = Vec2(0.0, 0.0)
        p2 = Vec2(1.0, 0.0)
        
        dist = point_to_segment_distance(point, p1, p2)
        assert abs(dist - 0.5) < 1e-10


class TestFindNearestStair:
    """Test finding nearest stair"""
    
    def test_find_nearest_stair(self):
        """Test finding nearest stair from multiple options"""
        # Create two stairs
        stair1 = StairPolygon(
            name="S_1",
            p1=Vec2(0.0, 0.0),
            p2=Vec2(100.0, 0.0),
            polygon=generate_stair_polygon((0.0, 0.0), (100.0, 0.0), 30.0),
            thickness=30.0
        )
        stair2 = StairPolygon(
            name="S_2",
            p1=Vec2(500.0, 500.0),
            p2=Vec2(600.0, 500.0),
            polygon=generate_stair_polygon((500.0, 500.0), (600.0, 500.0), 30.0),
            thickness=30.0
        )
        
        stairs = [stair1, stair2]
        
        # Point near stair1 should return stair1
        near_stair1 = Vec2(50.0, 50.0)
        nearest = find_nearest_stair(near_stair1, stairs)
        assert nearest == stair1
        
        # Point near stair2 should return stair2
        near_stair2 = Vec2(550.0, 550.0)
        nearest = find_nearest_stair(near_stair2, stairs)
        assert nearest == stair2
    
    def test_find_nearest_stair_empty_list(self):
        """Test that empty list returns None"""
        point = Vec2(0.0, 0.0)
        nearest = find_nearest_stair(point, [])
        assert nearest is None


class TestCalculateStairProgress:
    """Test calculating progress along a stair"""
    
    def test_progress_at_start(self):
        """Test progress at start of stair"""
        stair = StairPolygon(
            name="S_1",
            p1=Vec2(0.0, 0.0),
            p2=Vec2(100.0, 0.0),
            polygon=generate_stair_polygon((0.0, 0.0), (100.0, 0.0), 30.0),
            thickness=30.0
        )
        
        at_start = Vec2(0.0, 0.0)
        progress = calculate_stair_progress(at_start, stair)
        assert abs(progress - 0.0) < 1e-10
    
    def test_progress_at_middle(self):
        """Test progress at middle of stair"""
        stair = StairPolygon(
            name="S_1",
            p1=Vec2(0.0, 0.0),
            p2=Vec2(100.0, 0.0),
            polygon=generate_stair_polygon((0.0, 0.0), (100.0, 0.0), 30.0),
            thickness=30.0
        )
        
        at_middle = Vec2(50.0, 0.0)
        progress = calculate_stair_progress(at_middle, stair)
        assert abs(progress - 0.5) < 1e-10
    
    def test_progress_at_end(self):
        """Test progress at end of stair"""
        stair = StairPolygon(
            name="S_1",
            p1=Vec2(0.0, 0.0),
            p2=Vec2(100.0, 0.0),
            polygon=generate_stair_polygon((0.0, 0.0), (100.0, 0.0), 30.0),
            thickness=30.0
        )
        
        at_end = Vec2(100.0, 0.0)
        progress = calculate_stair_progress(at_end, stair)
        assert abs(progress - 1.0) < 1e-10


class TestStairPolygon:
    """Test StairPolygon class"""
    
    def test_midpoint_calculation(self):
        """Test midpoint calculation"""
        stair = StairPolygon(
            name="S_1",
            p1=Vec2(0.0, 0.0),
            p2=Vec2(100.0, 100.0),
            polygon=[],
            thickness=30.0
        )
        
        midpoint = stair.midpoint
        assert abs(midpoint.x - 50.0) < 1e-10
        assert abs(midpoint.y - 50.0) < 1e-10


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
