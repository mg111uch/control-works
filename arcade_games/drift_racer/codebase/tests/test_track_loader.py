"""
Tests for the TrackLoader.
Tests track listing, loading, and caching functionality.
"""

import unittest
import sys
import os

# Change to package root for imports
PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, PACKAGE_ROOT)


class TestTrackLoader(unittest.TestCase):
    """Tests for TrackLoader."""
    
    def setUp(self):
        """Change to package root for track loading."""
        self.original_cwd = os.getcwd()
        # Change to package root to find tracks directory
        os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    def tearDown(self):
        """Restore original working directory."""
        os.chdir(self.original_cwd)
    
    def test_list_tracks(self):
        """Test listing available tracks."""
        from controllers.track_loader import TrackLoader
        loader = TrackLoader()
        tracks = loader.list_available_tracks()
        self.assertIn('simple_oval', tracks)
    
    def test_load_default_track(self):
        """Test loading default track."""
        from controllers.track_loader import TrackLoader
        loader = TrackLoader()
        track = loader.load_default_track()
        self.assertEqual(track.name, "Simple Oval")
    
    def test_caching(self):
        """Test track loader caches loaded tracks."""
        from controllers.track_loader import TrackLoader
        loader = TrackLoader()
        
        track1 = loader.load_track('simple_oval')
        track2 = loader.load_track('simple_oval')
        
        # Should be the same object (cached)
        self.assertIs(track1, track2)


if __name__ == '__main__':
    unittest.main()
