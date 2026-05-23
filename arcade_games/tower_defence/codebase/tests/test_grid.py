"""
Tests for Grid System
"""
import pytest
import math

CELL_SIZE = 40
PATH_Y = 200
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400


def snap_to_grid(x, y):
    """Snap coordinates to nearest grid cell center"""
    grid_x = (x // CELL_SIZE) * CELL_SIZE + CELL_SIZE // 2
    grid_y = (y // CELL_SIZE) * CELL_SIZE + CELL_SIZE // 2
    return grid_x, grid_y


def is_on_path(y):
    """Check if a grid cell is on the enemy path"""
    path_top = PATH_Y - 15
    path_bottom = PATH_Y + 15
    return path_top <= y <= path_bottom


class TestGridSystem:
    """Tests for grid snapping functionality"""
    
    def test_snap_to_grid_basic(self):
        """Test basic grid snapping"""
        x, y = snap_to_grid(50, 50)
        assert x == 60
        assert y == 60
    
    def test_snap_to_grid_middle_of_cell(self):
        """Test snapping from middle of cell"""
        x, y = snap_to_grid(21, 21)
        assert x == 20
        assert y == 20
    
    def test_snap_to_grid_second_cell(self):
        """Test snapping from second cell"""
        x, y = snap_to_grid(50, 50)
        assert x == 60
        assert y == 60
        
        x, y = snap_to_grid(50, 60)
        assert x == 60
        assert y == 60
    
    def test_snap_to_grid_edge(self):
        """Test snapping from edge of screen"""
        x, y = snap_to_grid(0, 0)
        assert x == 20
        assert y == 20
        
        x, y = snap_to_grid(SCREEN_WIDTH - 1, SCREEN_HEIGHT - 1)
        assert x == 580
        assert y == 380
    
    def test_grid_cell_centers(self):
        """Test that grid centers are calculated correctly"""
        for cell_x in range(0, SCREEN_WIDTH // CELL_SIZE):
            for cell_y in range(0, SCREEN_HEIGHT // CELL_SIZE):
                expected_x = cell_x * CELL_SIZE + CELL_SIZE // 2
                expected_y = cell_y * CELL_SIZE + CELL_SIZE // 2
                x, y = snap_to_grid(cell_x * CELL_SIZE, cell_y * CELL_SIZE)
                assert x == expected_x
                assert y == expected_y


class TestPathDetection:
    """Tests for path detection"""
    
    def test_is_on_path_center(self):
        """Test that path center is detected"""
        assert is_on_path(PATH_Y) == True
    
    def test_is_on_path_edges(self):
        """Test path edges"""
        assert is_on_path(PATH_Y - 15) == True
        assert is_on_path(PATH_Y + 15) == True
    
    def test_is_on_path_outside(self):
        """Test outside path"""
        assert is_on_path(PATH_Y - 16) == False
        assert is_on_path(PATH_Y + 16) == False
        assert is_on_path(0) == False
        assert is_on_path(100) == False
    
    def test_is_on_path_far_outside(self):
        """Test far outside path"""
        assert is_on_path(0) == False
        assert is_on_path(SCREEN_HEIGHT - 1) == False
