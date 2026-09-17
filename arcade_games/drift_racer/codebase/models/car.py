"""
Car physics model for Drift King 2D.
Contains all car physics logic extracted from the original monolithic code.
"""

import math
from typing import Dict, Optional
import numpy as np
import sys
import os

# Add package root to path for imports
_PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, _PACKAGE_ROOT)

from utils.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    ACCELERATION, FRICTION, DRIFT_FRICTION,
    TURN_SPEED, BRAKE_FRICTION, GLOW_COLORS,
    MAX_STEERING_ANGLE, MIN_TURN_RADIUS, 
    MAX_SPEED_FOR_TURNING, LOW_SPEED_THRESHOLD
)
from utils.ray_caster import RayCaster


class Car:
    """
    Car physics model.
    
    Handles all car movement, drifting, and drift trail rendering.
    """
    
    def __init__(self, x: float, y: float, angle: float):
        """
        Initialize car at given position and angle.
        
        Args:
            x: Initial x position
            y: Initial y position
            angle: Initial angle in degrees (0 = facing right)
        """
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.angle = angle
        self.speed = 0
        self.drift_trail = []  # Store trail positions for glowing effect
        self._max_trail_length = 20
        
        # Steering state
        self.steering_angle = 0.0  # Current steering angle in degrees (-MAX to +MAX)
        
        # Ray casting for track boundary detection
        self.ray_caster = RayCaster(num_rays=10, fov=180.0, max_distance=200.0)
        self._track = None  # Set later for ray casting
        
        # Drift angle tracking
        self.drift_angle = 0.0  # Angle between velocity vector and car heading
        self.prev_x = x
        self.prev_y = y
    
    def set_track(self, track) -> None:
        """Set the track for ray casting."""
        self._track = track
    
    @property
    def ray_distances(self) -> np.ndarray:
        """
        Get ray cast distances to track boundaries.
        Returns normalized distances (0-1) for ML training.
        """
        if self._track is None:
            return np.zeros(10)  # Return zeros if no track set
        return self.ray_caster.cast_rays(self.x, self.y, self.angle, self._track)
    
    def update(self, accelerate: bool, turn_left: bool, turn_right: bool, 
               drift: bool, brake: bool) -> None:
        """
        Update car physics based on input actions.
        
        Args:
            accelerate: Whether to apply acceleration
            turn_left: Whether to turn left
            turn_right: Whether to turn right
            drift: Whether drift mode is active
            brake: Whether brake is applied
        """
        if accelerate:
            self.vx += ACCELERATION * math.sin(math.radians(self.angle))
            self.vy -= ACCELERATION * math.cos(math.radians(self.angle))
        
        # Realistic steering with dynamic turn radius
        # Turn radius increases with speed - car turns sharper at low speed
        # Maximum steering lock limits how much the wheels can turn
        self._update_steering(turn_left, turn_right)
        
        # Apply friction based on input
        if brake:
            friction = BRAKE_FRICTION
        elif drift:
            friction = DRIFT_FRICTION
        else:
            friction = FRICTION
        
        self.vx *= friction
        self.vy *= friction
        self.x += self.vx
        self.y += self.vy
        # No screen wrap: leaving track must yield is_on_track=False
        # so GameState off-track death triggers instead of teleporting.
        self.speed = math.sqrt(self.vx**2 + self.vy**2)
        
        # Calculate drift angle (angle between velocity vector and car heading)
        self._calculate_drift_angle()
        
        # Add to drift trail (always add, but glow only during drift)
        self.drift_trail.append((self.x, self.y, self.angle))
        # Keep only last N trail points for performance
        if len(self.drift_trail) > self._max_trail_length:
            self.drift_trail.pop(0)
    
    def _calculate_drift_angle(self) -> None:
        """
        Calculate the drift angle between velocity vector and car heading.
        
        Drift angle is the difference between where the car is pointing (heading)
        and where it's actually moving (velocity direction).
        A larger angle indicates more drift/slide.
        """
        if self.speed < 0.1:
            # Not moving fast enough to have meaningful drift
            self.drift_angle = 0.0
            return
        
        # Calculate velocity direction angle
        velocity_angle = math.degrees(math.atan2(self.vx, -self.vy))
        
        # Calculate difference between heading and velocity direction
        # Wrap to [0, 180]: heading is unbounded (accumulates spins),
        # velocity_angle is [-180, 180], so a single `if > 180` check
        # mis-scores multi-spin deltas (e.g. 270 -> 90 max drift).
        angle_diff = abs((self.angle - velocity_angle + 180.0) % 360.0 - 180.0)
        
        self.drift_angle = angle_diff
    
    def _update_steering(self, turn_left: bool, turn_right: bool) -> None:
        """
        Update steering with dynamic turn radius based on speed.
        
        Physics model:
        - Turn radius increases with speed (car can't turn sharply at high speed)
        - Maximum steering lock limits wheel angle
        - At low speed, car can achieve minimum turn radius
        - At high speed, turn radius is much larger
        
        Args:
            turn_left: Whether to steer left
            turn_right: Whether to steer right
        """
        # Calculate target steering angle based on input
        target_steering = 0.0
        if turn_left:
            target_steering = -MAX_STEERING_ANGLE
        if turn_right:
            target_steering = MAX_STEERING_ANGLE
        
        # Smoothly interpolate steering angle (simulates steering wheel response)
        steering_speed = 5.0  # Degrees per frame
        if self.steering_angle < target_steering:
            self.steering_angle = min(self.steering_angle + steering_speed, target_steering)
        elif self.steering_angle > target_steering:
            self.steering_angle = max(self.steering_angle - steering_speed, target_steering)
        
        # Apply steering lock - clamp to maximum
        self.steering_angle = max(-MAX_STEERING_ANGLE, min(MAX_STEERING_ANGLE, self.steering_angle))
        
        # Only turn if car is moving above threshold
        if self.speed < LOW_SPEED_THRESHOLD:
            return
        
        # Calculate effective turn rate based on speed
        # At low speed: can turn sharply (small turn radius)
        # At high speed: turn radius increases (larger turn radius)
        # 
        # New formula: turn_rate inversely proportional to speed
        # At low speed: high turn rate (sharp turning)
        # At high speed: low turn rate (gentle turning)
        # 
        # Using formula: angular_velocity = steering_factor / (speed + speed_offset)
        # This ensures at very low speed, turn is limited, and at higher speed, turn is gentler
        
        if abs(self.steering_angle) > 0.1:
            # Convert steering angle to radians for calculation
            steering_rad = math.radians(self.steering_angle)
            
            # Base turn factor - determines how responsive steering is
            base_turn_factor = 0.15
            
            # Speed offset prevents division by zero and limits low-speed turning
            speed_offset = 2.0
            
            # Calculate angular velocity:
            # - At low speed (speed=0.5): angular_velocity = base / (0.5+2) * tan(steering) ~ small
            # - At medium speed (speed=3): angular_velocity = base / (3+2) * tan(steering) ~ moderate
            # - At high speed (speed=8): angular_velocity = base / (8+2) * tan(steering) ~ small
            angular_velocity = (base_turn_factor / (self.speed + speed_offset)) * math.tan(steering_rad)
            
            # Convert to degrees and apply
            self.angle += math.degrees(angular_velocity)
    
    def get_forward_progress(self) -> float:
        """
        Calculate forward progress based on movement in car's heading direction.
        
        Returns:
            Distance moved in the direction the car is facing (can be negative)
        """
        # Direction car is facing
        heading_x = math.sin(math.radians(self.angle))
        heading_y = -math.cos(math.radians(self.angle))
        
        # Movement vector (guard against teleport jumps)
        dx = self.x - self.prev_x
        dy = self.y - self.prev_y
        if abs(dx) > SCREEN_WIDTH / 2 or abs(dy) > SCREEN_HEIGHT / 2:
            dx, dy = 0.0, 0.0
        
        # Dot product gives forward movement
        forward_progress = dx * heading_x + dy * heading_y
        
        # Update previous position
        self.prev_x = self.x
        self.prev_y = self.y
        
        return forward_progress
    
    def get_state(self, next_cp=None) -> np.ndarray:
        """
        Get egocentric state array for AI training (no absolute position,
        so policies transfer across track shapes).

        Args:
            next_cp: Optional (x, y) center of next checkpoint target.

        Returns:
            State array with 15 features:
            - 5 car features: speed, drift_angle, sin/cos bearing to next
              checkpoint, normalized distance to it (all track-relative)
            - 10 ray distances to track boundaries (normalized)
        """
        if next_cp is None:
            sin_b, cos_b, dist_n = 0.0, 1.0, 0.0
        else:
            cx, cy = next_cp
            bearing = math.degrees(math.atan2(cx - self.x, -(cy - self.y)))
            rel = (bearing - self.angle + 180.0) % 360.0 - 180.0
            sin_b = math.sin(math.radians(rel))
            cos_b = math.cos(math.radians(rel))
            dist_n = float(np.clip(math.hypot(cx - self.x, cy - self.y) / 720.0, 0.0, 1.0))
        # Base car state (egocentric only)
        car_state = np.array([
            float(np.clip(self.speed / 10.0, 0.0, 2.0)),
            float(np.clip(self.drift_angle / 180.0, 0.0, 1.0)),
            sin_b,
            cos_b,
            dist_n,
        ], dtype=np.float32)
        
        # Ray cast distances (10 rays, normalized)
        ray_state = self.ray_distances.astype(np.float32)
        
        return np.concatenate([car_state, ray_state]).astype(np.float32)
    
    def draw(self, screen) -> None:
        """
        Draw the car and ray casting visualization to the screen.
        
        Args:
            screen: Pygame surface to draw on
        """
        self._draw_drift_trail(screen)
        self._draw_car_body(screen)
        self._draw_rays(screen)
    
    def _draw_rays(self, screen) -> None:
        """
        Draw ray casting visualization.
        Green rays = hitting track (safe)
        Red rays = hitting boundary (obstacle)
        """
        if self._track is None:
            return
        # Cast rays first to populate visualization data
        self.ray_caster.cast_rays(self.x, self.y, self.angle, self._track)
        self.ray_caster.draw_rays(screen, self.x, self.y, 
                                  color_safe=(0, 255, 0),  # Green
                                  color_boundary=(255, 0, 0))  # Red
    
    def _draw_drift_trail(self, screen) -> None:
        """Draw glowing drift trail."""
        import pygame
        for i, (tx, ty, t_angle) in enumerate(self.drift_trail):
            # Fade effect: brighter at car, dimmer further back
            alpha = (i + 1) / len(self.drift_trail)
            glow_color = GLOW_COLORS[min(i // 3, len(GLOW_COLORS) - 1)]
            trail_size = int(3 + alpha * 4)
            # Draw small rotated trail segment
            trail_end_x = tx + 3 * math.sin(math.radians(t_angle))
            trail_end_y = ty - 3 * math.cos(math.radians(t_angle))
            pygame.draw.line(screen, glow_color, (tx, ty), (trail_end_x, trail_end_y), trail_size)
    
    def _draw_car_body(self, screen) -> None:
        """Draw car body as rotated rectangle."""
        import pygame
        from utils.constants import CAR_WIDTH, CAR_HEIGHT, RED, WHITE
        
        angle_rad = math.radians(self.angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        # Car center
        cx, cy = self.x, self.y
        
        # Calculate corner points for a rectangle
        half_w = CAR_WIDTH // 2
        half_h = CAR_HEIGHT // 2
        
        # Corners relative to center, then rotate
        corners = [
            (cx + half_w * sin_a - half_h * cos_a, cy - half_w * cos_a - half_h * sin_a),  # Front-right
            (cx + half_w * sin_a + half_h * cos_a, cy - half_w * cos_a + half_h * sin_a),  # Front-left
            (cx - half_w * sin_a + half_h * cos_a, cy + half_w * cos_a + half_h * sin_a),  # Back-left
            (cx - half_w * sin_a - half_h * cos_a, cy + half_w * cos_a - half_h * sin_a),  # Back-right
        ]
        
        # Draw car body
        pygame.draw.polygon(screen, RED, corners)
        # Add car outline
        pygame.draw.polygon(screen, WHITE, corners, 2)
