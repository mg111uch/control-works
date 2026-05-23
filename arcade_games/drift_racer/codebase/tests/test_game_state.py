"""
Tests for the GameState model.
Tests scoring, combo system, and game progression.
"""

import unittest
import sys
import os
import json
import tempfile

# Change to package root for imports
PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, PACKAGE_ROOT)

from models.game_state import GameState


class TestGameState(unittest.TestCase):
    """Tests for GameState model."""
    
    def test_initial_state(self):
        """Test game state initializes correctly."""
        state = GameState()
        self.assertEqual(state.laps_completed, 0)
        self.assertEqual(state.score, 0)
        self.assertEqual(state.combo_multiplier, 1)
        self.assertFalse(state.done)
    
    def test_update_on_track(self):
        """Test score update when on track."""
        state = GameState()
        reward = state.update(
            car_x=300, car_y=200,
            on_track=True, drifting=False, speed=5.0,
            drift_angle=0.0, forward_progress=1.0
        )
        # Reward includes forward progress and living penalty
        self.assertGreater(reward, -1)  # Living penalty is -0.1, forward progress adds positive
    
    def test_update_off_track(self):
        """Test score penalty when off track."""
        state = GameState()
        reward = state.update(
            car_x=50, car_y=50,
            on_track=False, drifting=False, speed=5.0
        )
        self.assertLess(reward, 0)
        self.assertLess(state.score, 0)
    
    def test_drift_bonus(self):
        """Test drifting gives bonus points."""
        state = GameState()
        reward_no_drift = state.update(
            car_x=300, car_y=200,
            on_track=True, drifting=False, speed=5.0,
            drift_angle=0.0, forward_progress=1.0
        )
        
        state2 = GameState()
        # Drift requires drift_angle >= MIN_DRIFT_ANGLE (10 degrees)
        reward_drift = state2.update(
            car_x=300, car_y=200,
            on_track=True, drifting=True, speed=5.0,
            drift_angle=30.0, forward_progress=1.0  # 30 degree drift angle
        )
        
        self.assertGreater(reward_drift, reward_no_drift)
    
    def test_combo_multiplier(self):
        """Test combo multiplier increases with consecutive drifts."""
        state = GameState()
        
        # Multiple drift ticks on track with actual drift angle
        for _ in range(15):
            state.update(
                car_x=300, car_y=200,
                on_track=True, drifting=True, speed=5.0,
                drift_angle=30.0, forward_progress=1.0  # Need drift angle for combo
            )
        
        self.assertGreater(state.combo_multiplier, 1)
    
    def test_combo_reset_off_track(self):
        """Test combo resets when going off track (but with OFF_TRACK_NO_END=True, episode may not end)."""
        from models.game_state import OFF_TRACK_NO_END
        state = GameState()
        
        # Build up combo with actual drift angle
        for _ in range(15):
            state.update(
                car_x=300, car_y=200,
                on_track=True, drifting=True, speed=5.0,
                drift_angle=30.0, forward_progress=1.0
            )
        
        self.assertGreater(state.combo_multiplier, 1)
        
        # Go off track
        state.update(
            car_x=50, car_y=50,
            on_track=False, drifting=False, speed=5.0
        )
        
        # With OFF_TRACK_NO_END=True, game may not be done
        # But the combo should definitely be reset
        if OFF_TRACK_NO_END:
            # Combo should reset but done may still be False
            self.assertEqual(state.combo_multiplier, 1)
        else:
            # After off-track, game is done
            self.assertTrue(state.done)
    
    def test_game_completion(self):
        """Test game ends after completing all laps."""
        state = GameState(total_laps=2)
        
        # Complete 2 laps (mock by setting laps directly)
        state.laps_completed = 2
        
        reward = state.update(
            car_x=300, car_y=200,
            on_track=True, drifting=False, speed=5.0,
            drift_angle=0.0, forward_progress=1.0
        )
        
        self.assertTrue(state.done)
        self.assertGreater(reward, 0)  # Bonus for completion
    
    def test_lap_counting_with_start_finish_line(self):
        """Test lap counting with start/finish line."""
        # Create a test track with start/finish line
        track_data = {
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
        
        temp_dir = tempfile.mkdtemp()
        track_path = os.path.join(temp_dir, "test_track.json")
        
        with open(track_path, 'w') as f:
            json.dump(track_data, f)
        
        from models.track import Track
        track = Track(track_path)
        state = GameState(track=track, total_laps=3)
        
        # Initially no laps completed
        self.assertEqual(state.laps_completed, 0)
        
        # Simulate being away from start/finish line (making progress)
        for _ in range(200):
            state.update(car_x=300, car_y=200, on_track=True, drifting=False, speed=5.0,
                        drift_angle=0.0, forward_progress=1.0)
        
        # Should have made progress towards a lap
        self.assertGreater(state._lap_progress, 0)
        
        # Simulate crossing the start/finish line in clockwise direction
        # Set previous position to simulate coming from below (clockwise)
        state._prev_x = 100
        state._prev_y = 210  # Higher y (below start line)
        
        state.update(car_x=100, car_y=190, on_track=True, drifting=False, speed=5.0,
                    drift_angle=0.0, forward_progress=1.0)
        
        # Should have completed a lap
        self.assertEqual(state.laps_completed, 1)
        
        # Clean up
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_multiple_laps(self):
        """Test completing multiple laps."""
        # Create a test track with start/finish line
        track_data = {
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
        
        temp_dir = tempfile.mkdtemp()
        track_path = os.path.join(temp_dir, "test_track.json")
        
        with open(track_path, 'w') as f:
            json.dump(track_data, f)
        
        from models.track import Track
        track = Track(track_path)
        state = GameState(track=track, total_laps=3)
        
        # Complete 3 laps
        for lap in range(3):
            # Simulate being away from start/finish line
            for _ in range(200):
                state.update(car_x=300, car_y=200, on_track=True, drifting=False, speed=5.0,
                            drift_angle=0.0, forward_progress=1.0)
            
            # Cross the start/finish line in clockwise direction
            state._prev_x = 100
            state._prev_y = 210  # Coming from below (clockwise)
            state.update(car_x=100, car_y=190, on_track=True, drifting=False, speed=5.0,
                        drift_angle=0.0, forward_progress=1.0)
        
        # All laps completed
        self.assertEqual(state.laps_completed, 3)
        self.assertTrue(state.done)
        
        # Clean up
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_lap_progress_resets(self):
        """Test lap progress resets after completing a lap."""
        # Create a test track with start/finish line
        track_data = {
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
        
        temp_dir = tempfile.mkdtemp()
        track_path = os.path.join(temp_dir, "test_track.json")
        
        with open(track_path, 'w') as f:
            json.dump(track_data, f)
        
        from models.track import Track
        track = Track(track_path)
        state = GameState(track=track, total_laps=3)
        
        # Make progress
        for _ in range(200):
            state.update(car_x=300, car_y=200, on_track=True, drifting=False, speed=5.0,
                        drift_angle=0.0, forward_progress=1.0)
        
        progress_before = state._lap_progress
        self.assertGreater(progress_before, 0)
        
        # Cross start/finish line in clockwise direction
        state._prev_x = 100
        state._prev_y = 210  # Coming from below (clockwise)
        state.update(car_x=100, car_y=190, on_track=True, drifting=False, speed=5.0,
                    drift_angle=0.0, forward_progress=1.0)
        
        # Progress should reset after lap completion
        self.assertEqual(state._lap_progress, 0)
        
        # Clean up
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()


class TestDirectionalLapCounting(unittest.TestCase):
    """Tests for clockwise-only lap counting."""
    
    def _create_test_track(self):
        """Create a test track for lap counting tests."""
        track_data = {
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
        
        temp_dir = tempfile.mkdtemp()
        track_path = os.path.join(temp_dir, "test_track.json")
        
        with open(track_path, 'w') as f:
            json.dump(track_data, f)
        
        from models.track import Track
        track = Track(track_path)
        
        return track, temp_dir
    
    def test_clockwise_crossing_counts_lap(self):
        """Test that crossing start line in clockwise direction counts a lap."""
        track, temp_dir = self._create_test_track()
        state = GameState(track=track, total_laps=3)
        
        # Simulate making progress around the track
        for _ in range(200):
            state.update(car_x=300, car_y=200, on_track=True, drifting=False, speed=5.0,
                        drift_angle=0.0, forward_progress=1.0)
        
        # Simulate crossing start line in clockwise direction (moving upward, y decreasing)
        # Previous position: y=210, current position: y=190 (moving upward)
        state._prev_x = 100
        state._prev_y = 210  # Higher y (below start line)
        
        # Cross the line moving upward (clockwise)
        state.update(car_x=100, car_y=190, on_track=True, drifting=False, speed=5.0,
                    drift_angle=0.0, forward_progress=1.0)
        
        # Should have completed a lap
        self.assertEqual(state.laps_completed, 1)
        
        # Clean up
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_counter_clockwise_crossing_ignored(self):
        """Test that crossing start line in counter-clockwise direction does NOT count a lap."""
        track, temp_dir = self._create_test_track()
        state = GameState(track=track, total_laps=3)
        
        # Simulate making progress around the track
        for _ in range(200):
            state.update(car_x=300, car_y=200, on_track=True, drifting=False, speed=5.0,
                        drift_angle=0.0, forward_progress=1.0)
        
        # Simulate crossing start line in counter-clockwise direction (moving downward, y increasing)
        # Previous position: y=190, current position: y=210 (moving downward)
        state._prev_x = 100
        state._prev_y = 190  # Lower y (above start line)
        
        # Cross the line moving downward (counter-clockwise)
        state.update(car_x=100, car_y=210, on_track=True, drifting=False, speed=5.0,
                    drift_angle=0.0, forward_progress=1.0)
        
        # Should NOT have completed a lap (wrong direction)
        self.assertEqual(state.laps_completed, 0)
        
        # Clean up
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_is_clockwise_crossing_method(self):
        """Test the _is_clockwise_crossing method directly."""
        track, temp_dir = self._create_test_track()
        state = GameState(track=track, total_laps=3)
        
        # Test clockwise crossing (moving upward, dy < 0)
        is_clockwise = state._is_clockwise_crossing(
            x=100, y=190,  # Current position
            prev_x=100, prev_y=210  # Previous position (higher y)
        )
        self.assertTrue(is_clockwise)
        
        # Test counter-clockwise crossing (moving downward, dy > 0)
        is_clockwise = state._is_clockwise_crossing(
            x=100, y=210,  # Current position
            prev_x=100, prev_y=190  # Previous position (lower y)
        )
        self.assertFalse(is_clockwise)
        
        # Test with no previous position
        is_clockwise = state._is_clockwise_crossing(
            x=100, y=200,
            prev_x=None, prev_y=None
        )
        self.assertFalse(is_clockwise)
        
        # Clean up
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_multiple_clockwise_laps(self):
        """Test completing multiple laps in clockwise direction."""
        track, temp_dir = self._create_test_track()
        state = GameState(track=track, total_laps=3)
        
        for lap in range(3):
            # Simulate making progress around the track
            for _ in range(200):
                state.update(car_x=300, car_y=200, on_track=True, drifting=False, speed=5.0,
                            drift_angle=0.0, forward_progress=1.0)
            
            # Set previous position for clockwise crossing
            state._prev_x = 100
            state._prev_y = 210  # Coming from below
            
            # Cross the start line clockwise (moving upward)
            state.update(car_x=100, car_y=190, on_track=True, drifting=False, speed=5.0,
                        drift_angle=0.0, forward_progress=1.0)
        
        # All 3 laps completed
        self.assertEqual(state.laps_completed, 3)
        self.assertTrue(state.done)
        
        # Clean up
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_mixed_direction_crossings(self):
        """Test that only clockwise crossings count when mixed with counter-clockwise."""
        track, temp_dir = self._create_test_track()
        state = GameState(track=track, total_laps=5)
        
        # Make progress and cross clockwise (should count)
        for _ in range(200):
            state.update(car_x=300, car_y=200, on_track=True, drifting=False, speed=5.0,
                        drift_angle=0.0, forward_progress=1.0)
        state._prev_x = 100
        state._prev_y = 210
        state.update(car_x=100, car_y=190, on_track=True, drifting=False, speed=5.0,
                    drift_angle=0.0, forward_progress=1.0)
        self.assertEqual(state.laps_completed, 1)
        
        # Make progress and cross counter-clockwise (should NOT count)
        for _ in range(200):
            state.update(car_x=300, car_y=200, on_track=True, drifting=False, speed=5.0,
                        drift_angle=0.0, forward_progress=1.0)
        state._prev_x = 100
        state._prev_y = 190
        state.update(car_x=100, car_y=210, on_track=True, drifting=False, speed=5.0,
                    drift_angle=0.0, forward_progress=1.0)
        self.assertEqual(state.laps_completed, 1)  # Still 1, not 2
        
        # Make progress and cross clockwise again (should count)
        for _ in range(200):
            state.update(car_x=300, car_y=200, on_track=True, drifting=False, speed=5.0,
                        drift_angle=0.0, forward_progress=1.0)
        state._prev_x = 100
        state._prev_y = 210
        state.update(car_x=100, car_y=190, on_track=True, drifting=False, speed=5.0,
                    drift_angle=0.0, forward_progress=1.0)
        self.assertEqual(state.laps_completed, 2)  # Now 2
        
        # Clean up
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_previous_position_tracking(self):
        """Test that previous position is tracked correctly."""
        track, temp_dir = self._create_test_track()
        state = GameState(track=track, total_laps=3)
        
        # Initially no previous position
        self.assertIsNone(state._prev_x)
        self.assertIsNone(state._prev_y)
        
        # After first update, previous position should be set
        state.update(car_x=300, car_y=200, on_track=True, drifting=False, speed=5.0,
                    drift_angle=0.0, forward_progress=1.0)
        self.assertEqual(state._prev_x, 300)
        self.assertEqual(state._prev_y, 200)
        
        # After second update, previous position should be updated
        state.update(car_x=310, car_y=210, on_track=True, drifting=False, speed=5.0,
                    drift_angle=0.0, forward_progress=1.0)
        self.assertEqual(state._prev_x, 310)
        self.assertEqual(state._prev_y, 210)
        
        # Clean up
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
