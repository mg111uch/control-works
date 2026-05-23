"""
Track loader for Drift King 2D.
Handles discovery and loading of track files.
"""

import os
from typing import List, Optional
from models.track import Track


class TrackLoader:
    """Loads and caches track files."""
    
    def __init__(self, tracks_dir: str = None):
        """
        Initialize track loader.
        
        Args:
            tracks_dir: Directory containing track files (defaults to tracks/ in package root)
        """
        if tracks_dir is None:
            # Default to tracks directory in package root
            _PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.tracks_dir = os.path.join(_PACKAGE_ROOT, "tracks")
        else:
            self.tracks_dir = tracks_dir
        self._cache = {}
    
    def list_available_tracks(self) -> List[str]:
        """
        Return list of available track files.
        
        Returns:
            List of track names (without .json extension)
        """
        if not os.path.exists(self.tracks_dir):
            return []
        
        tracks = []
        for filename in os.listdir(self.tracks_dir):
            if filename.endswith('.json'):
                track_name = filename[:-5]  # Remove .json extension
                tracks.append(track_name)
        
        return sorted(tracks)
    
    def load_track(self, name: str) -> Track:
        """
        Load track by name (cached).
        
        Args:
            name: Track name (without .json extension)
            
        Returns:
            Loaded Track object
        """
        # Check cache first
        if name in self._cache:
            return self._cache[name]
        
        # Build filepath
        filepath = os.path.join(self.tracks_dir, f"{name}.json")
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Track '{name}' not found at {filepath}")
        
        # Load track
        track = Track(filepath)
        
        # Cache it
        self._cache[name] = track
        
        return track
    
    def load_default_track(self) -> Track:
        """
        Load the default track (simple_oval).
        
        Returns:
            Default Track object
        """
        return self.load_track("simple_oval")
    
    def clear_cache(self) -> None:
        """Clear the track cache."""
        self._cache.clear()
    
    def get_track_info(self, name: str) -> dict:
        """
        Get information about a track without loading it fully.
        
        Args:
            name: Track name
            
        Returns:
            Dictionary with track metadata
        """
        filepath = os.path.join(self.tracks_dir, f"{name}.json")
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Track '{name}' not found")
        
        import json
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return {
            'name': data.get('name', name),
            'version': data.get('version', '1.0'),
            'difficulty': data.get('difficulty', 'unknown'),
            'screen_size': data.get('screen_size', {'width': 600, 'height': 400}),
            'num_elements': len(data.get('track_elements', [])),
            'num_checkpoints': len(data.get('checkpoints', []))
        }
