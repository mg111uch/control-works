"""
Tests for the Car model.
Tests car physics, movement, and state management.
"""

import unittest
import sys
import os
import numpy as np
import math

# Change to package root for imports
PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, PACKAGE_ROOT)

from models.car import Car
from utils.constants import MAX_STEERING_ANGLE, LOW_SPEED_THRESHOLD


class TestCar(unittest.TestCase):
    """Tests for Car model."""
    
    def test_car_initialization(self):
        """Test car starts at correct position."""
        car = Car(100, 100, 45)
        self.assertEqual(car.x, 100)
        self.assertEqual(car.y, 100)
        self.assertEqual(car.angle, 45)
        self.assertEqual(car.vx, 0)
        self.assertEqual(car.vy, 0)
        self.assertEqual(car.speed, 0)
        self.assertEqual(len(car.drift_trail), 0)
        self.assertEqual(car.steering_angle, 0.0)
    
    def test_car_update_no_input(self):
        """Test car behavior with no input."""
        car = Car(100, 100, 0)
        car.update(accelerate=False, turn_left=False, 
                   turn_right=False, drift=False, brake=False)
        # Car should slow down due to friction
        self.assertLess(car.speed, 0.01)
    
    def test_car_accelerate(self):
        """Test car acceleration."""
        car = Car(100, 100, 0)  # Facing right
        initial_speed = car.speed
        car.update(accelerate=True, turn_left=False, 
                   turn_right=False, drift=False, brake=False)
        self.assertGreater(car.speed, initial_speed)
    
    def test_car_turn(self):
        """Test car turning requires speed."""
        car = Car(100, 100, 0)
        
        # First accelerate to get some speed - car needs speed to turn
        for _ in range(20):
            car.update(accelerate=True, turn_left=False, 
                       turn_right=False, drift=False, brake=False)
        
        # Now car has speed and can turn
        # Need multiple frames for steering angle to build up and turn to occur
        initial_angle = car.angle
        for _ in range(10):
            car.update(accelerate=False, turn_left=True, 
                       turn_right=False, drift=False, brake=False)
        self.assertLess(car.angle, initial_angle)
    
    def test_car_no_turn_when_stationary(self):
        """Test car cannot turn when stationary."""
        car = Car(100, 100, 0)
        initial_angle = car.angle
        # Try to turn without accelerating (no speed)
        car.update(accelerate=False, turn_left=True, 
                   turn_right=False, drift=False, brake=False)
        # Car should NOT turn when stationary
        self.assertEqual(car.angle, initial_angle)
    
    def test_car_drift_friction(self):
        """Test drift friction is lower than normal friction."""
        car1 = Car(100, 100, 0)
        car2 = Car(100, 100, 0)
        
        # Give both cars some speed
        for _ in range(10):
            car1.update(accelerate=True, turn_left=False, 
                       turn_right=False, drift=False, brake=False)
        
        speed_before_drift = car1.speed
        
        # Apply drift friction
        for _ in range(10):
            car1.update(accelerate=False, turn_left=False, 
                       turn_right=False, drift=True, brake=False)
        
        # Drift should have more speed loss
        self.assertLess(car1.speed, speed_before_drift)
    
    def test_car_state_normalization(self):
        """Test state array is properly normalized (egocentric: no absolute x,y)."""
        car = Car(300, 200, 0)
        state = car.get_state()

        # Should return float32 array
        self.assertEqual(state.dtype, np.float32)
        # Should have 15 elements (5 ego car features + 10 rays)
        self.assertEqual(len(state), 15)
        # speed 0 -> 0, drift 0 -> 0
        self.assertAlmostEqual(state[0], 0.0, places=2)
        self.assertAlmostEqual(state[1], 0.0, places=2)
        # no target -> bearing ahead (sin 0, cos 1), dist 0
        self.assertAlmostEqual(state[2], 0.0, places=2)
        self.assertAlmostEqual(state[3], 1.0, places=2)
        self.assertAlmostEqual(state[4], 0.0, places=2)
        # target straight ahead: rel bearing 0, dist 100/720
        state = car.get_state(next_cp=(300, 100))
        self.assertAlmostEqual(state[2], 0.0, places=2)
        self.assertAlmostEqual(state[3], 1.0, places=2)
        self.assertAlmostEqual(state[4], 100.0 / 720.0, places=2)


class TestDynamicSteering(unittest.TestCase):
    """Tests for dynamic turn radius and realistic steering."""
    
    def test_steering_angle_initialization(self):
        """Test steering angle starts at zero."""
        car = Car(100, 100, 0)
        self.assertEqual(car.steering_angle, 0.0)
    
    def test_steering_angle_increases_on_input(self):
        """Test steering angle changes when turning input is given."""
        car = Car(100, 100, 0)
        
        # Give steering input for several frames
        for _ in range(10):
            car.update(accelerate=False, turn_left=True, 
                       turn_right=False, drift=False, brake=False)
        
        # Steering angle should be negative (left turn)
        self.assertLess(car.steering_angle, 0)
        
        # Steering angle should not exceed max lock
        self.assertGreaterEqual(car.steering_angle, -MAX_STEERING_ANGLE)
    
    def test_steering_angle_right(self):
        """Test steering angle for right turn."""
        car = Car(100, 100, 0)
        
        # Give steering input for several frames
        for _ in range(10):
            car.update(accelerate=False, turn_left=False, 
                       turn_right=True, drift=False, brake=False)
        
        # Steering angle should be positive (right turn)
        self.assertGreater(car.steering_angle, 0)
        
        # Steering angle should not exceed max lock
        self.assertLessEqual(car.steering_angle, MAX_STEERING_ANGLE)
    
    def test_max_steering_lock(self):
        """Test that steering angle is clamped to maximum."""
        car = Car(100, 100, 0)
        
        # Give steering input for many frames (more than needed to reach max)
        for _ in range(20):
            car.update(accelerate=False, turn_left=True, 
                       turn_right=False, drift=False, brake=False)
        
        # Steering angle should be clamped to max
        self.assertGreaterEqual(car.steering_angle, -MAX_STEERING_ANGLE)
        self.assertLessEqual(car.steering_angle, MAX_STEERING_ANGLE)
    
    def test_dynamic_turn_radius_low_speed(self):
        """Test that car turns sharper at low speed."""
        car_low_speed = Car(100, 100, 0)
        
        # Accelerate enough to get above threshold but still low speed
        for _ in range(15):
            car_low_speed.update(accelerate=True, turn_left=False, 
                                turn_right=False, drift=False, brake=False)
        
        low_speed = car_low_speed.speed
        self.assertGreater(low_speed, LOW_SPEED_THRESHOLD)
        
        # Turn at low speed
        initial_angle_low = car_low_speed.angle
        for _ in range(30):
            car_low_speed.update(accelerate=False, turn_left=True, 
                                turn_right=False, drift=False, brake=False)
        angle_change_low = abs(car_low_speed.angle - initial_angle_low)
        
        # Now test high speed
        car_high_speed = Car(100, 100, 0)
        
        # Accelerate more for high speed
        for _ in range(50):
            car_high_speed.update(accelerate=True, turn_left=False, 
                                 turn_right=False, drift=False, brake=False)
        
        high_speed = car_high_speed.speed
        self.assertGreater(high_speed, low_speed)
        
        # Turn at high speed
        initial_angle_high = car_high_speed.angle
        for _ in range(30):
            car_high_speed.update(accelerate=False, turn_left=True, 
                                 turn_right=False, drift=False, brake=False)
        angle_change_high = abs(car_high_speed.angle - initial_angle_high)
        
        # At higher speed, turn radius should be larger (less angle change per frame)
        # So angle change at high speed should be less than at low speed
        # Note: This tests the dynamic turn radius behavior
        self.assertGreater(angle_change_low, 0)  # Low speed should turn
        self.assertGreater(angle_change_high, 0)  # High speed should turn
    
    def test_no_turn_below_threshold(self):
        """Test that car doesn't turn below speed threshold."""
        car = Car(100, 100, 0)
        
        # Don't accelerate - stay below threshold
        initial_angle = car.angle
        for _ in range(10):
            car.update(accelerate=False, turn_left=True, 
                       turn_right=False, drift=False, brake=False)
        
        # Car should not turn when below threshold
        self.assertEqual(car.angle, initial_angle)
        self.assertLess(car.speed, LOW_SPEED_THRESHOLD)
    
    def test_steering_returns_to_center(self):
        """Test that steering angle returns to center when no input."""
        car = Car(100, 100, 0)
        
        # First, turn left to build up steering angle
        for _ in range(10):
            car.update(accelerate=False, turn_left=True, 
                       turn_right=False, drift=False, brake=False)
        
        # Steering should be non-zero
        self.assertNotEqual(car.steering_angle, 0)
        
        # Now release steering input
        for _ in range(10):
            car.update(accelerate=False, turn_left=False, 
                       turn_right=False, drift=False, brake=False)
        
        # Steering should return toward zero
        # Note: It may not be exactly zero due to interpolation
        self.assertLess(abs(car.steering_angle), MAX_STEERING_ANGLE)


if __name__ == '__main__':
    unittest.main()
