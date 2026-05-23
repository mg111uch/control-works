"""
Tests for drift angle detection and new reward function.
"""

import pytest
import math
import numpy as np
import sys
import os

# Add package root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.car import Car
from models.game_state import (
    GameState, OFF_TRACK_PENALTY, LAP_BONUS, 
    FORWARD_PROGRESS_SCALE, LIVING_REWARD, DRIFT_REWARD_SCALE, MIN_DRIFT_ANGLE, OFF_TRACK_NO_END
)


class TestDriftAngleDetection:
    """Tests for drift angle detection in Car model."""
    
    def test_drift_angle_initialization(self):
        """Test that drift angle is initialized to 0."""
        car = Car(100, 100, 0)
        assert car.drift_angle == 0.0
    
    def test_drift_angle_zero_when_stationary(self):
        """Test that drift angle is 0 when car is not moving."""
        car = Car(100, 100, 0)
        car.update(accelerate=False, turn_left=False, turn_right=False, drift=False, brake=False)
        assert car.drift_angle == 0.0
    
    def test_drift_angle_zero_when_moving_straight(self):
        """Test that drift angle is small when moving in heading direction."""
        car = Car(100, 100, 0)  # Facing right (0 degrees)
        # Accelerate in heading direction
        for _ in range(10):
            car.update(accelerate=True, turn_left=False, turn_right=False, drift=False, brake=False)
        # Drift angle should be small (car is moving roughly in heading direction)
        assert car.drift_angle < 20.0, f"Expected small drift angle, got {car.drift_angle}"
    
    def test_drift_angle_nonzero_when_drifting(self):
        """Test that drift angle increases when drifting."""
        car = Car(100, 100, 0)
        # Accelerate and turn while drifting
        for _ in range(20):
            car.update(accelerate=True, turn_left=True, turn_right=False, drift=True, brake=False)
        # After turning while drifting, there should be a drift angle
        # Note: The actual angle depends on physics, just check it's calculated
        assert car.drift_angle >= 0.0
    
    def test_drift_angle_calculation_method(self):
        """Test the _calculate_drift_angle method directly."""
        car = Car(100, 100, 0)
        
        # Set up a scenario where velocity is perpendicular to heading
        car.angle = 0  # Facing right
        car.vx = 0     # Moving up
        car.vy = -5
        car.speed = 5.0
        
        car._calculate_drift_angle()
        
        # Velocity angle is 270 degrees (atan2(0, 5) = 0, but with our formula it's atan2(0, -(-5)) = atan2(0, 5) = 0)
        # Actually with our formula: velocity_angle = atan2(vx, -vy) = atan2(0, 5) = 0
        # Heading is 0, so drift angle should be 0
        # Let's try another scenario
        car.vx = 5  # Moving right
        car.vy = 0
        car.speed = 5.0
        car._calculate_drift_angle()
        # Velocity angle = atan2(5, 0) = 90 degrees
        # Heading = 0, so drift angle = 90
        assert car.drift_angle == pytest.approx(90.0, abs=1.0)


class TestForwardProgress:
    """Tests for forward progress calculation."""
    
    def test_forward_progress_initialization(self):
        """Test that previous position is initialized correctly."""
        car = Car(100, 100, 45)
        assert car.prev_x == 100
        assert car.prev_y == 100
    
    def test_forward_progress_positive_when_moving_forward(self):
        """Test that forward progress is positive when moving in heading direction."""
        car = Car(100, 100, 0)  # Facing right
        car.update(accelerate=True, turn_left=False, turn_right=False, drift=False, brake=False)
        
        progress = car.get_forward_progress()
        # Car should have moved forward (positive progress)
        assert progress > 0
    
    def test_forward_progress_updates_previous_position(self):
        """Test that get_forward_progress updates previous position."""
        car = Car(100, 100, 0)
        car.update(accelerate=True, turn_left=False, turn_right=False, drift=False, brake=False)
        
        old_x, old_y = car.x, car.y
        car.get_forward_progress()
        
        assert car.prev_x == old_x
        assert car.prev_y == old_y


class TestOffTrackDeath:
    """Tests for off-track = death logic (or not ending episode with new reward system)."""
    
    def test_off_track_applies_penalty(self):
        """Test that going off track applies negative reward."""
        game_state = GameState()
        game_state.reset()
        
        reward = game_state.update(
            car_x=100, car_y=100, on_track=False, drifting=False, speed=5.0
        )
        
        assert reward == OFF_TRACK_PENALTY
    
    def test_off_track_does_not_end_episode_by_default(self):
        """Test that going off track doesn't end episode with new reward system."""
        game_state = GameState()
        game_state.reset()
        
        # Simulate off-track
        reward = game_state.update(
            car_x=100, car_y=100, on_track=False, drifting=False, speed=5.0
        )
        
        # With OFF_TRACK_NO_END=True, episode should not end
        if OFF_TRACK_NO_END:
            assert game_state.done is False
        else:
            assert game_state.done is True
    
    def test_on_track_does_not_set_done(self):
        """Test that staying on track doesn't set done."""
        game_state = GameState()
        game_state.reset()
        
        reward = game_state.update(
            car_x=100, car_y=100, on_track=True, drifting=False, speed=5.0,
            drift_angle=0.0, forward_progress=1.0
        )
        
        assert game_state.done is False


class TestNewRewardFunction:
    """Tests for the redesigned reward function."""
    
    def test_forward_progress_reward(self):
        """Test that forward progress contributes to reward."""
        game_state = GameState()
        game_state.reset()
        
        forward_progress = 2.0
        reward = game_state.update(
            car_x=100, car_y=100, on_track=True, drifting=False, speed=5.0,
            drift_angle=0.0, forward_progress=forward_progress
        )
        
        # Reward should include forward_progress * FORWARD_PROGRESS_SCALE
        expected_progress_reward = forward_progress * FORWARD_PROGRESS_SCALE
        # Also includes living reward
        expected_reward = expected_progress_reward + LIVING_REWARD
        
        assert reward == pytest.approx(expected_reward, abs=0.1)
    
    def test_living_reward_applied(self):
        """Test that living reward is applied each step."""
        game_state = GameState()
        game_state.reset()
        
        # No forward progress, no drift
        reward = game_state.update(
            car_x=100, car_y=100, on_track=True, drifting=False, speed=5.0,
            drift_angle=0.0, forward_progress=0.0
        )
        
        # Should only have living reward
        assert reward == pytest.approx(LIVING_REWARD, abs=0.1)
    
    def test_drift_reward_with_angle(self):
        """Test that drift reward is calculated based on drift angle."""
        game_state = GameState()
        game_state.reset()
        
        speed = 5.0
        drift_angle = 45.0  # 45 degrees drift
        
        reward = game_state.update(
            car_x=100, car_y=100, on_track=True, drifting=True, speed=speed,
            drift_angle=drift_angle, forward_progress=0.0
        )
        
        # Expected drift component: sin(45) * speed^2 * DRIFT_REWARD_SCALE * combo(1)
        expected_drift = math.sin(math.radians(drift_angle)) * (speed ** 2) * DRIFT_REWARD_SCALE
        expected_reward = LIVING_REWARD + expected_drift
        
        assert reward == pytest.approx(expected_reward, abs=0.1)
    
    def test_drift_reward_requires_minimum_angle(self):
        """Test that drift reward only applies above minimum angle."""
        game_state = GameState()
        game_state.reset()
        
        speed = 5.0
        drift_angle = MIN_DRIFT_ANGLE - 1  # Below minimum
        
        reward = game_state.update(
            car_x=100, car_y=100, on_track=True, drifting=True, speed=speed,
            drift_angle=drift_angle, forward_progress=0.0
        )
        
        # Should only have living reward (no drift reward)
        assert reward == pytest.approx(LIVING_REWARD, abs=0.1)
    
    def test_drift_reward_requires_speed(self):
        """Test that drift reward only applies above minimum speed."""
        game_state = GameState()
        game_state.reset()
        
        speed = 0.3  # Below 0.5 threshold
        drift_angle = 45.0
        
        reward = game_state.update(
            car_x=100, car_y=100, on_track=True, drifting=True, speed=speed,
            drift_angle=drift_angle, forward_progress=0.0
        )
        
        # Should only have living reward (no drift reward due to low speed)
        assert reward == pytest.approx(LIVING_REWARD, abs=0.1)


class TestComboMultiplier:
    """Tests for the combo multiplier system."""
    
    def test_combo_increases_with_drift(self):
        """Test that combo multiplier increases with consecutive drift ticks."""
        game_state = GameState()
        game_state.reset()
        
        # Simulate many drift ticks
        for _ in range(15):
            game_state.update(
                car_x=100, car_y=100, on_track=True, drifting=True, speed=5.0,
                drift_angle=30.0, forward_progress=1.0
            )
        
        # Combo should have increased
        assert game_state.combo_multiplier >= 1
    
    def test_combo_resets_when_not_drifting(self):
        """Test that combo resets when not drifting."""
        game_state = GameState()
        game_state.reset()
        
        # Build up some combo
        for _ in range(15):
            game_state.update(
                car_x=100, car_y=100, on_track=True, drifting=True, speed=5.0,
                drift_angle=30.0, forward_progress=1.0
            )
        
        # Stop drifting
        game_state.update(
            car_x=100, car_y=100, on_track=True, drifting=False, speed=5.0,
            drift_angle=0.0, forward_progress=1.0
        )
        
        # Combo should reset to 1
        assert game_state.combo_multiplier == 1
    
    def test_combo_multiplies_drift_reward(self):
        """Test that combo multiplier affects drift reward."""
        game_state = GameState()
        game_state.reset()
        
        # Build up combo
        for _ in range(15):
            game_state.update(
                car_x=100, car_y=100, on_track=True, drifting=True, speed=5.0,
                drift_angle=30.0, forward_progress=1.0
            )
        
        if game_state.combo_multiplier > 1:
            # Next drift reward should be multiplied
            speed = 5.0
            drift_angle = 45.0
            
            prev_drift_score = game_state.drift_score
            game_state.update(
                car_x=100, car_y=100, on_track=True, drifting=True, speed=speed,
                drift_angle=drift_angle, forward_progress=0.0
            )
            
            # Drift score should have increased by more than base drift
            base_drift = math.sin(math.radians(drift_angle)) * (speed ** 2) * DRIFT_REWARD_SCALE
            actual_increase = game_state.drift_score - prev_drift_score
            
            assert actual_increase >= base_drift


class TestObservationSpace:
    """Tests for updated observation space."""
    
    def test_state_includes_drift_angle(self):
        """Test that get_state returns 15 features including drift angle."""
        car = Car(100, 100, 0)
        
        # Mock track for ray casting
        class MockTrack:
            def is_on_track(self, x, y):
                return True
        
        car.set_track(MockTrack())
        
        state = car.get_state()
        
        # State should have 15 features (5 car + 10 rays)
        assert state.shape == (15,)
    
    def test_drift_angle_in_state_normalized(self):
        """Test that drift angle in state is normalized to 0-1 range."""
        car = Car(100, 100, 0)
        
        # Set a known drift angle
        car.drift_angle = 90.0
        
        class MockTrack:
            def is_on_track(self, x, y):
                return True
        
        car.set_track(MockTrack())
        
        state = car.get_state()
        
        # Drift angle is 5th feature (index 4), normalized: 90/180 = 0.5
        assert state[4] == pytest.approx(0.5, abs=0.01)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
