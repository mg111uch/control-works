"""Validity tests for procedurally generated tracks."""
import importlib.util
import os
import sys
import unittest

TRAINING_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'training')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

_spec = importlib.util.spec_from_file_location(
    'gen_track', os.path.join(TRAINING_DIR, 'gen_track.py'))
gen_track = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen_track)

from models.track import Track
from models.game_state import GameState


def _load(data):
    import json
    import tempfile
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        path = f.name
    track = Track(path)
    os.unlink(path)
    return track


class TestGenTrack(unittest.TestCase):
    def _check(self, seed, lobes, shape=None):
        data, _ = gen_track.generate(seed, lobes, shape=shape)
        track = _load(data)
        # spawn on asphalt
        sx, sy, _ = track.get_start_position()
        self.assertTrue(track.is_on_track(sx, sy), f'seed {seed} spawn off asphalt')
        # boxes: ids ordered, all centers asphalt, sequence required
        self.assertTrue(track.sequence_required)
        self.assertEqual(track.required_checkpoints, list(range(len(track.checkpoints))))
        for cp in track.checkpoints:
            cx, cy = (cp.x_min + cp.x_max) / 2, (cp.y_min + cp.y_max) / 2
            self.assertTrue(track.is_on_track(cx, cy), f'seed {seed} box {cp.id} off asphalt')
        # lap completes by walking boxes in order + crossing line
        gs = GameState(track=track)
        for cid in track.required_checkpoints:
            cp = [c for c in track.checkpoints if c.id == cid][0]
            gs.update((cp.x_min + cp.x_max) / 2, (cp.y_min + cp.y_max) / 2,
                      True, False, 2.0, 0.0, 1.0)
        self.assertEqual(gs.laps_completed, 0)
        # cross the line along the track's forward direction (angle 180 runs +y)
        _, _, sangle = track.get_start_position()
        s = 1 if sangle == 180 else -1
        for _ in range(300):
            gs.update(sx, sy + 2 * s, True, False, 2.0, 0.0, 1.0)
        gs._prev_x, gs._prev_y = sx, sy - 5 * s
        gs.update(sx, sy + 5 * s, True, False, 2.0, 0.0, 1.0)
        self.assertEqual(gs.laps_completed, 1, f'seed {seed} lap did not count')
        return data

    def test_two_lobe_seeds(self):
        for seed in [7, 11, 21]:
            data = self._check(seed, 2)
            self.assertGreaterEqual(len(data['checkpoints']), 6)

    def test_one_lobe_seeds(self):
        for seed in [3, 5]:
            data = self._check(seed, 1)
            self.assertGreaterEqual(len(data['checkpoints']), 4)

    def test_shape_families(self):
        for shape, seed in [('rect', 50), ('stadium', 51), ('ellipse', 52),
                            ('spline', 200)]:
            data = self._check(seed, 1, shape=shape)
            self.assertGreaterEqual(len(data['checkpoints']), 4)

    def test_rotated_element_collision(self):
        """Rotated rect must contain its local interior, exclude exterior."""
        import json
        import tempfile
        data = {
            'name': 't', 'version': '1.0', 'difficulty': 'easy',
            'screen_size': {'width': 600, 'height': 400},
            'start_position': {'x': 300, 'y': 200, 'angle': 0},
            'track_elements': [
                {'type': 'rectangle', 'center_x': 300, 'center_y': 200,
                 'width': 240, 'height': 120, 'angle': 30, 'is_hole': False},
                {'type': 'rectangle', 'center_x': 300, 'center_y': 200,
                 'width': 120, 'height': 60, 'angle': 30, 'is_hole': True},
            ],
            'checkpoints': [],
            'lap_completion': {'required_checkpoints': [], 'sequence_required': False},
            'visual': {},
        }
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            path = f.name
        from models.track import Track
        track = Track(path)
        os.unlink(path)
        # center is inside the hole
        self.assertFalse(track.is_on_track(300, 200))
        # local +x axis point on the ring: rotate (90, 0) by +30deg
        import math
        a = math.radians(30)
        px, py = 300 + 90 * math.cos(a), 200 + 90 * math.sin(a)
        self.assertTrue(track.is_on_track(px, py))
        # far corner outside
        self.assertFalse(track.is_on_track(100, 100))

    def test_polygon_collision(self):
        """Polygon elements: inside/outside/hole behave."""
        import json
        import tempfile
        sq = [[0, 0], [100, 0], [100, 100], [0, 100]]
        hole = [[30, 30], [70, 30], [70, 70], [30, 70]]
        data = {
            'name': 't', 'version': '1.0', 'difficulty': 'easy',
            'screen_size': {'width': 600, 'height': 400},
            'start_position': {'x': 10, 'y': 50, 'angle': 0},
            'track_elements': [
                {'type': 'polygon', 'center_x': 50, 'center_y': 50,
                 'vertices': sq, 'is_hole': False},
                {'type': 'polygon', 'center_x': 50, 'center_y': 50,
                 'vertices': hole, 'is_hole': True},
            ],
            'checkpoints': [],
            'lap_completion': {'required_checkpoints': [], 'sequence_required': False},
            'visual': {},
        }
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            path = f.name
        from models.track import Track
        track = Track(path)
        os.unlink(path)
        self.assertTrue(track.is_on_track(10, 50))  # ring left
        self.assertFalse(track.is_on_track(50, 50))  # hole center
        self.assertFalse(track.is_on_track(200, 200))  # outside


if __name__ == '__main__':
    unittest.main()
