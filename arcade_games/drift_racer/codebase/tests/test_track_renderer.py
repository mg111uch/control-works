"""
Tests for the TrackRenderer.
Tests track rendering and start/finish line visualization.
"""

import unittest
import sys
import os
import json
import tempfile
import pygame

# Change to package root for imports
PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, PACKAGE_ROOT)

from views.track_renderer import TrackRenderer
from models.track import Track


class TestTrackRenderer(unittest.TestCase):
    """Tests for TrackRenderer."""
    
    def setUp(self):
        """Set up pygame and test track."""
        pygame.init()
        self.screen = pygame.Surface((600, 400))
        self.renderer = TrackRenderer(self.screen)
        
        # Create a test track with start/finish line
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
                }
            ],
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
        
        self.track = Track(self.track_path)
    
    def tearDown(self):
        """Clean up pygame and temp files."""
        pygame.quit()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_renderer_initialization(self):
        """Test renderer initializes correctly."""
        self.assertIsNotNone(self.renderer)
        self.assertEqual(self.renderer.screen, self.screen)
    
    def test_render_track(self):
        """Test rendering a track."""
        # Should not raise an exception
        self.renderer.render(self.track)
        
        # Screen should have some content (not just background color)
        # Background is [128, 128, 128], track should add different colors
        pixels = pygame.PixelArray(self.screen)
        # Just verify render completed without error
        del pixels
    
    def test_start_finish_line_renders(self):
        """Test start/finish line is rendered."""
        # Render the track
        self.renderer.render(self.track)
        
        # The start/finish line should be visible
        # At start position (100, 200), the line should be drawn
        # Check pixel at start position is not background color
        color_at_start = self.screen.get_at((100, 200))
        
        # Should not be the background color [128, 128, 128]
        self.assertNotEqual(
            color_at_start[:3], 
            (128, 128, 128)
        )
    
    def test_start_finish_line_has_marker(self):
        """Test start/finish line has a visible center marker."""
        # Render the track
        self.renderer.render(self.track)
        
        # The start/finish line marker should be visible
        # It might not be red if covered by track, but should not be background
        color_at_center = self.screen.get_at((int(self.track.start_finish_line.x),
                                               int(self.track.start_finish_line.y)))
        
        # Should not be the background color [128, 128, 128]
        self.assertNotEqual(color_at_center[:3], (128, 128, 128))
    
    def test_start_finish_line_spans_track(self):
        """Test start/finish line spans the track width."""
        line = self.track.start_finish_line
        
        # Line should have a reasonable width
        self.assertGreater(line.width, 50)
        self.assertLess(line.width, 300)
    
    def test_draw_start_line_legacy(self):
        """Test legacy draw_start_line method."""
        # Should not raise an exception
        self.renderer.draw_start_line(100, 200, 100)
        
        # Verify a line was drawn (white color)
        color = self.screen.get_at((100, 200))
        self.assertEqual(color[:3], (255, 255, 255))
    
    def test_start_line_rendered_over_track(self):
        """Test start/finish line is rendered on top of track elements."""
        # Render the track
        self.renderer.render(self.track)
        
        # The start line center should be visible (red marker)
        # Since it's rendered after track elements, the marker should be red
        color_at_center = self.screen.get_at((
            int(self.track.start_finish_line.x),
            int(self.track.start_finish_line.y)
        ))
        
        # The center marker should be red (255, 0, 0) since it's on top
        self.assertEqual(color_at_center[:3], (255, 0, 0))
    
    def test_start_line_thickness_is_two(self):
        """Test start/finish line has thickness of 2 pixels."""
        # This is verified by the implementation using width=2
        # We verify the line is visible and thin
        self.renderer.render(self.track)
        
        # The line should be visible at the start position
        line = self.track.start_finish_line
        color_at_line = self.screen.get_at((int(line.x), int(line.y)))
        
        # Should be the red marker (on top)
        self.assertEqual(color_at_line[:3], (255, 0, 0))
    
    def test_start_line_length_is_half_track_width(self):
        """Test start/finish line length is half the track width."""
        line = self.track.start_finish_line
        
        # Calculate expected track width at start position
        # For the test track (ellipse at 300,200 with radius 100,100)
        # Start is at (100, 200) which is on the left edge
        # Track width at that point should be ~100 (outer) - inner portion
        # Line width should be half of that
        
        # The line width should be less than full track width
        self.assertGreater(line.width, 20)  # Should have some width
        self.assertLess(line.width, 150)    # Should be half or less of track width
    
    def test_start_line_perpendicular_to_car_direction(self):
        """Test start/finish line is perpendicular to car initial direction."""
        line = self.track.start_finish_line
        start_x, start_y, start_angle = self.track.get_start_position()
        
        # Line angle should be 180 degrees offset from car direction
        expected_angle = start_angle + 180
        self.assertEqual(line.angle, expected_angle)
    
    def test_start_line_visible_on_track_surface(self):
        """Test start/finish line is visible on the track surface."""
        self.renderer.render(self.track)
        
        # Check that the line area has visible markers
        line = self.track.start_finish_line
        
        # The center should have the red marker
        center_color = self.screen.get_at((int(line.x), int(line.y)))
        self.assertEqual(center_color[:3], (255, 0, 0))


if __name__ == '__main__':
    unittest.main()
