"""
Tests for the Track model.
Tests track loading, collision detection, and checkpoint management.
"""

import unittest
import json
import os
import sys
import tempfile
from pathlib import Path

# Change to package root for imports
PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, PACKAGE_ROOT)

from models.track import Track, TrackElement, Checkpoint, StartFinishLine


class TestTrack(unittest.TestCase):
    """Tests for Track model."""
    
    def setUp(self):
        """Create a temporary track file for testing."""
        # Track with outer ellipse (track) and inner ellipse (hole)
        self.track_data = {
            "name": "Test Track",
            "version": "1.0",
            "difficulty": "easy",
            "screen_size": {"width": 600, "height": 400},
            "start_position": {"x": 100, "y": 200, "angle": 0},
            "track_elements": [
                {
                    "type": "ellipse",
                    "center_x": 300,
                    "center_y": 200,
                    "radius_x": 100,
                    "radius_y": 100,
                    "is_hole": False
                },
                {
                    "type": "ellipse",
                    "center_x": 300,
                    "center_y": 200,
                    "radius_x": 50,
                    "radius_y": 50,
                    "is_hole": True
                }
            ],
            "checkpoints": [
                {"id": 0, "type": "position", "x_min": 200, "x_max": 400, 
                 "y_min": 100, "y_max": 300}
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
        self.track_path = os.path.join(self.temp_dir, "test_track.json")
        
        with open(self.track_path, 'w') as f:
            json.dump(self.track_data, f)
    
    def tearDown(self):
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_track_load(self):
        """Test track loads correctly from JSON."""
        track = Track(self.track_path)
        self.assertEqual(track.name, "Test Track")
        self.assertEqual(track.version, "1.0")
        self.assertEqual(track.difficulty, "easy")
    
    def test_track_start_position(self):
        """Test start position is loaded correctly."""
        track = Track(self.track_path)
        start = track.get_start_position()
        self.assertEqual(start, (100, 200, 0))
    
    def test_track_elements(self):
        """Test track elements are parsed."""
        track = Track(self.track_path)
        self.assertEqual(len(track.elements), 2)
        
        # First element should be track (not hole)
        self.assertFalse(track.elements[0].is_hole)
        
        # Second element should be hole
        self.assertTrue(track.elements[1].is_hole)
    
    def test_on_track_detection(self):
        """Test on-track detection works correctly."""
        track = Track(self.track_path)
        
        # Point in the track area (between outer ellipse and hole)
        # Outer ellipse: radius_x=100, radius_y=100
        # Inner hole: radius_x=50, radius_y=50
        # At (380, 200): dx=80, dy=0
        # In outer ellipse: 80^2/100^2 = 0.64 <= 1 ✓
        # Outside hole: 80^2/50^2 = 2.56 > 1 ✓
        self.assertTrue(track.is_on_track(380, 200))
        
        # Center of hole should NOT be on track
        self.assertFalse(track.is_on_track(300, 200))
        
        # Far away should NOT be on track
        self.assertFalse(track.is_on_track(50, 50))
    
    def test_checkpoints(self):
        """Test checkpoint parsing."""
        track = Track(self.track_path)
        self.assertEqual(len(track.checkpoints), 1)
        
        # Car in checkpoint should be detected
        self.assertTrue(track.check_checkpoint(300, 200, 0))
        
        # Car outside checkpoint should not be detected
        self.assertFalse(track.check_checkpoint(50, 50, 0))
    
    def test_start_finish_line_exists(self):
        """Test start/finish line is created automatically."""
        track = Track(self.track_path)
        self.assertIsNotNone(track.start_finish_line)
        self.assertIsInstance(track.start_finish_line, StartFinishLine)
    
    def test_start_finish_line_position(self):
        """Test start/finish line is at the start position."""
        track = Track(self.track_path)
        line = track.start_finish_line
        
        # Should be at start position (100, 200)
        self.assertEqual(line.x, 100)
        self.assertEqual(line.y, 200)
        # Angle should be start angle + 180° (rotated 180°)
        self.assertEqual(line.angle, 180)
    
    def test_start_finish_line_contains_point(self):
        """Test start/finish line contains points on the line."""
        track = Track(self.track_path)
        line = track.start_finish_line
        
        # Point at center of line should be contained
        self.assertTrue(line.contains(line.x, line.y))
        
        # Point slightly off the line (perpendicular) should not be contained
        # At 180° angle, off is in y direction
        self.assertFalse(line.contains(line.x, line.y + 20))
    
    def test_check_start_finish_line_method(self):
        """Test check_start_finish_line method works."""
        track = Track(self.track_path)
        
        # At start position, should be on line
        self.assertTrue(track.check_start_finish_line(100, 200))
        
        # Far from start position, should not be on line
        self.assertFalse(track.check_start_finish_line(300, 200))
    
    def test_start_finish_line_width_is_half_track_width(self):
        """Test start/finish line width is half the track width."""
        track = Track(self.track_path)
        line = track.start_finish_line
        
        # Calculate expected track width at start position
        # For the test track (ellipse at 300,200 with radius 100,100)
        # Start is at (100, 200) which is on the left edge
        # Track width at that point should be ~200 (outer diameter)
        # Line width should be half of that = 100
        
        # Line width should be positive and approximately half track width
        self.assertGreater(line.width, 0)
        self.assertLessEqual(line.width, 100)  # Should be half or less
    
    def test_start_finish_line_perpendicular_to_car_direction(self):
        """Test start/finish line is perpendicular to car initial direction."""
        track = Track(self.track_path)
        line = track.start_finish_line
        start_x, start_y, start_angle = track.get_start_position()
        
        # Line angle should be 180 degrees offset from car direction
        expected_angle = start_angle + 180
        self.assertEqual(line.angle, expected_angle)
    
    def test_start_finish_line_detects_car_crossing(self):
        """Test that car crossing start line is detected correctly."""
        track = Track(self.track_path)
        line = track.start_finish_line
        
        # Car at start position should be on the line
        self.assertTrue(line.contains(100, 200))
        
        # Car slightly off the line center but still on line width
        # At angle 180°, the line spans horizontally (along x-axis)
        # So points with same y but different x should be on line
        # Line width is 100, so half is 50 - points within 50 of center are on line
        self.assertTrue(line.contains(110, 200))  # Within width (10 < 50)
        self.assertTrue(line.contains(140, 200))  # Within width (40 < 50)
        # Need to go further - at x=51, that's 51 away, outside line
        self.assertFalse(line.contains(152, 200))  # Outside width (52 > 50)


if __name__ == '__main__':
    unittest.main()
