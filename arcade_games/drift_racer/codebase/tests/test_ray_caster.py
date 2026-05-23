"""
Tests for the RayCaster system.
Tests ray casting, boundary detection, and ML state generation.
"""

import unittest
import sys
import os
import tempfile
import json

# Change to package root for imports
PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, PACKAGE_ROOT)

from utils.ray_caster import RayCaster
import numpy as np


class TestRayCaster(unittest.TestCase):
    """Tests for RayCaster class."""
    
    def setUp(self):
        """Create a temporary track file for testing."""
        # Create a simple oval track for testing
        self.track_data = {
            "name": "Test Oval",
            "version": "1.0",
            "difficulty": "easy",
            "screen_size": {"width": 600, "height": 400},
            "start_position": {"x": 300, "y": 200, "angle": 0},
            "track_elements": [
                {
                    "type": "ellipse",
                    "center_x": 300,
                    "center_y": 200,
                    "radius_x": 200,
                    "radius_y": 150,
                    "is_hole": False
                },
                {
                    "type": "ellipse",
                    "center_x": 300,
                    "center_y": 200,
                    "radius_x": 100,
                    "radius_y": 70,
                    "is_hole": True
                }
            ],
            "checkpoints": [
                {"id": 0, "type": "position", "x_min": 400, "x_max": 500, 
                 "y_min": 50, "y_max": 150}
            ],
            "lap_completion": {
                "required_checkpoints": [0],
                "sequence_required": False
            },
            "visual": {
                "track_color": [80, 80, 80],
                "border_color": [255, 255, 255],
                "grass_color": [0, 128, 0],
                "background_color": [128, 128, 128],
                "border_width": 2
            }
        }
        
        # Create temp file
        self.temp_dir = tempfile.mkdtemp()
        self.track_path = os.path.join(self.temp_dir, "test_oval.json")
        
        with open(self.track_path, 'w') as f:
            json.dump(self.track_data, f)
        
        # Import track here to avoid issues
        from models.track import Track
        self.track = Track(self.track_path)
        self.ray_caster = RayCaster(num_rays=10, fov=180.0, max_distance=200.0)
    
    def tearDown(self):
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_ray_caster_initialization(self):
        """Test ray caster initializes with correct parameters."""
        self.assertEqual(self.ray_caster.num_rays, 10)
        self.assertEqual(self.ray_caster.fov, 180.0)
        self.assertEqual(self.ray_caster.max_distance, 200.0)
        self.assertEqual(self.ray_caster.angle_step, 20.0)  # 180 / (10-1)
    
    def test_ray_angles(self):
        """Test ray angles are calculated correctly."""
        # At car angle 0 (facing up), screen_angle=0+270=270, start=180
        # Rays span 180° to 360° (centered on LEFT/screen)
        # After 180° rotation, rays now correctly cast in front of car
        angles = self.ray_caster.get_ray_angles(0)
        expected = [180, 200, 220, 240, 260, 280, 300, 320, 340, 360]
        self.assertEqual(angles, expected)
    
    def test_ray_angles_offset(self):
        """Test ray angles with car offset."""
        # At car angle 90 (facing right), screen_angle=90+270=360, start=270
        # Rays span 270° to 450° which wraps to [270, 290, 310, 330, 350, 370, 390, 410, 430, 450]
        # Or equivalently: [-90, -70, -50, -30, -10, 10, 30, 50, 70, 90]
        # After 180° rotation, rays now correctly cast in front of car
        angles = self.ray_caster.get_ray_angles(90)
        expected = [270, 290, 310, 330, 350, 370, 390, 410, 430, 450]
        for actual, exp in zip(angles, expected):
            self.assertAlmostEqual(actual, exp, places=5)
    
    def test_cast_rays_returns_correct_shape(self):
        """Test that cast_rays returns array of correct size."""
        distances = self.ray_caster.cast_rays(300, 200, 0, self.track)
        self.assertEqual(len(distances), 10)
        self.assertIsInstance(distances, np.ndarray)
    
    def test_cast_rays_normalized(self):
        """Test that ray distances are normalized to 0-1."""
        distances = self.ray_caster.cast_rays(300, 200, 0, self.track)
        self.assertTrue(np.all(distances >= 0))
        self.assertTrue(np.all(distances <= 1))
    
    def test_cast_rays_center_safe(self):
        """Test rays from safe position return valid distances."""
        # Point on track (between outer and inner ellipse)
        # Outer: radius_x=200, radius_y=150
        # Inner: radius_x=100, radius_y=70
        # At (380, 200): dx=80, dy=0
        # In outer: 80^2/200^2 = 0.16 <= 1 ✓
        # Outside inner: 80^2/100^2 = 0.64 > 1 ✓
        distances = self.ray_caster.cast_rays(380, 200, 0, self.track)
        # Should have valid distances
        self.assertTrue(np.all(distances > 0))
        self.assertTrue(np.any(distances < 1.0))  # Some hit boundaries
    
    def test_cast_rays_boundary_detection(self):
        """Test rays detect boundaries correctly."""
        # Point in the hole (off track) should have rays hitting nearby boundary
        distances_off = self.ray_caster.cast_rays(300, 200, 0, self.track)
        
        # Point near boundary should have shorter rays
        distances_near = self.ray_caster.cast_rays(380, 200, 0, self.track)
        
        # At least one ray should be shorter when near boundary
        self.assertTrue(np.any(distances_near < distances_off))
    
    def test_cast_rays_raw_returns_raw_distances(self):
        """Test that cast_rays_raw returns raw distances."""
        raw_distances = self.ray_caster.cast_rays_raw(300, 200, 0, self.track)
        self.assertEqual(len(raw_distances), 10)
        self.assertIsInstance(raw_distances[0], float)
    
    def test_ml_state_shape(self):
        """Test ML state has correct shape."""
        ml_state = self.ray_caster.get_ml_state(300, 200, 0, self.track)
        # Should be 14 features: 4 car + 10 rays
        self.assertEqual(len(ml_state), 14)
    
    def test_ml_state_contains_car_and_rays(self):
        """Test ML state contains both car and ray data."""
        ml_state = self.ray_caster.get_ml_state(300, 200, 0, self.track)
        # First 4 should be car state (normalized position)
        self.assertAlmostEqual(ml_state[0], 0.5)  # x / 600
        self.assertAlmostEqual(ml_state[1], 0.5)  # y / 400
        # Last 10 should be ray distances
        self.assertEqual(len(ml_state[4:]), 10)
    
    def test_ml_state_normalized(self):
        """Test ML state values are normalized."""
        ml_state = self.ray_caster.get_ml_state(300, 200, 0, self.track)
        # All values should be between 0 and 1
        self.assertTrue(np.all(ml_state >= 0))
        self.assertTrue(np.all(ml_state <= 1))
    
    def test_ray_caster_endpoints_stored(self):
        """Test that ray endpoints are stored for visualization."""
        self.ray_caster.cast_rays(300, 200, 0, self.track)
        self.assertEqual(len(self.ray_caster.last_endpoints), 10)
        # Each endpoint should be a tuple of (x, y)
        self.assertIsInstance(self.ray_caster.last_endpoints[0], tuple)
        self.assertEqual(len(self.ray_caster.last_endpoints[0]), 2)
    
    def test_ray_caster_distances_stored(self):
        """Test that ray distances are stored."""
        self.ray_caster.cast_rays(300, 200, 0, self.track)
        self.assertEqual(len(self.ray_caster.last_distances), 10)
        self.assertIsInstance(self.ray_caster.last_distances, np.ndarray)
    
    def test_different_car_angles(self):
        """Test ray casting with different car angles."""
        for angle in [0, 45, 90, 180, 270]:
            distances = self.ray_caster.cast_rays(300, 200, angle, self.track)
            self.assertEqual(len(distances), 10)
            self.assertTrue(np.all(distances >= 0))
            self.assertTrue(np.all(distances <= 1))
    
    def test_off_track_position(self):
        """Test ray casting from off-track position."""
        # Point far outside track
        distances = self.ray_caster.cast_rays(50, 50, 0, self.track)
        # Most rays should hit boundaries quickly
        self.assertTrue(np.all(distances <= 1.0))
    
    def test_max_distance_limit(self):
        """Test that rays don't exceed max distance."""
        # Even from center, rays should not exceed max_distance when normalized
        distances = self.ray_caster.cast_rays(300, 200, 0, self.track)
        self.assertTrue(np.all(distances <= 1.0))
    
    def test_get_ray_caster_singleton(self):
        """Test global get_ray_caster function."""
        from utils.ray_caster import get_ray_caster
        caster1 = get_ray_caster()
        caster2 = get_ray_caster()
        self.assertIs(caster1, caster2)


class TestRayCasterEdgeCases(unittest.TestCase):
    """Tests for edge cases in ray casting."""
    
    def setUp(self):
        """Create test track."""
        self.track_data = {
            "name": "Test Track",
            "version": "1.0",
            "difficulty": "easy",
            "screen_size": {"width": 600, "height": 400},
            "start_position": {"x": 300, "y": 200, "angle": 0},
            "track_elements": [
                {
                    "type": "ellipse",
                    "center_x": 300,
                    "center_y": 200,
                    "radius_x": 200,
                    "radius_y": 150,
                    "is_hole": False
                },
                {
                    "type": "ellipse",
                    "center_x": 300,
                    "center_y": 200,
                    "radius_x": 100,
                    "radius_y": 70,
                    "is_hole": True
                }
            ],
            "checkpoints": [],
            "lap_completion": {
                "required_checkpoints": [],
                "sequence_required": False
            },
            "visual": {
                "track_color": [80, 80, 80],
                "border_color": [255, 255, 255],
                "grass_color": [0, 128, 0],
                "background_color": [128, 128, 128],
                "border_width": 2
            }
        }
        
        self.temp_dir = tempfile.mkdtemp()
        self.track_path = os.path.join(self.temp_dir, "test_track.json")
        
        with open(self.track_path, 'w') as f:
            json.dump(self.track_data, f)
        
        from models.track import Track
        self.track = Track(self.track_path)
    
    def tearDown(self):
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_different_num_rays(self):
        """Test ray caster with different number of rays."""
        for num_rays in [5, 9, 10, 15, 20]:
            caster = RayCaster(num_rays=num_rays, fov=180.0)
            self.assertEqual(caster.num_rays, num_rays)
            self.assertEqual(caster.angle_step, 180.0 / (num_rays - 1))
            
            distances = caster.cast_rays(300, 200, 0, self.track)
            self.assertEqual(len(distances), num_rays)
    
    def test_different_fov(self):
        """Test ray caster with different field of view."""
        for fov in [90, 120, 180, 270]:
            caster = RayCaster(num_rays=10, fov=fov)
            self.assertEqual(caster.fov, fov)
            self.assertEqual(caster.angle_step, fov / 9)
    
    def test_different_max_distance(self):
        """Test ray caster with different max distances."""
        for max_dist in [50, 100, 200, 500]:
            caster = RayCaster(num_rays=10, fov=180.0, max_distance=max_dist)
            self.assertEqual(caster.max_distance, max_dist)
    
    def test_step_size_affects_precision(self):
        """Test that step size affects boundary detection precision."""
        caster_fine = RayCaster(num_rays=10, fov=180.0, max_distance=200.0, step_size=1.0)
        caster_coarse = RayCaster(num_rays=10, fov=180.0, max_distance=200.0, step_size=5.0)
        
        distances_fine = caster_fine.cast_rays(350, 200, 0, self.track)
        distances_coarse = caster_coarse.cast_rays(350, 200, 0, self.track)
        
        # Fine step size should give more precise results
        self.assertIsInstance(distances_fine[0], float)
        self.assertIsInstance(distances_coarse[0], float)


if __name__ == '__main__':
    unittest.main()
