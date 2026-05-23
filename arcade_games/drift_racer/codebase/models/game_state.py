"""
Game state model for Drift King 2D.
Handles scoring, lap counting, and game progress tracking.
"""

import time
import math
from typing import Dict, Any, Optional
import sys
import os

# Add package root to path for imports
_PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, _PACKAGE_ROOT)

from models.track import Track


# Reward constants
OFF_TRACK_PENALTY = -1000.0  # Large negative penalty for off-track (death)
OFF_TRACK_ENFORCE_DEATH = True  # End episode on off-track
OFF_TRACK_NO_END = False  # Backward compatibility - now we enforce death
LAP_BONUS = 1000.0  # Increased lap bonus for completion
FORWARD_PROGRESS_SCALE = 10.0
LIVING_REWARD = 0.5  # Positive reward for staying on track (encourages survival)
DRIFT_REWARD_SCALE = 0.5
MIN_DRIFT_ANGLE = 10.0  # Minimum angle to be considered drifting


class GameState:
    """
    Game state tracking.
    
    Manages score, laps, checkpoints, combo system, and game completion.
    """
    
    def __init__(self, track: Optional[Track] = None, total_laps: int = 10):
        """
        Initialize game state.
        
        Args:
            track: Optional track for checkpoint-based lap completion
            total_laps: Number of laps required to complete the game
        """
        self.track = track
        self.total_laps = total_laps
        self.reset()
    
    def reset(self) -> None:
        """Reset game state to initial values."""
        self.laps_completed = 0
        self.checkpoints_passed = set()
        self.drift_score = 0
        self.combo_multiplier = 1
        self.consecutive_drift_ticks = 0
        self.combo_flash_timer = 0
        self.done = False
        self.start_time = time.time()
        self.ticks = 0
        self._lap_progress = 0.0  # Progress towards next lap (0.0 to 1.0)
        self._last_line_crossing = 0  # Ticks since last line crossing
        self._prev_laps = 0  # Track previous lap count for bonus
        self._is_drifting = False  # Current drift state
        self._prev_x = None  # Previous x position for direction detection
        self._prev_y = None  # Previous y position for direction detection
        self._was_on_line = False  # Whether car was on start/finish line last tick
    
    def update(self, car_x: float, car_y: float, on_track: bool, 
               drifting: bool, speed: float, drift_angle: float = 0.0,
               forward_progress: float = 0.0) -> float:
        """
        Update game state based on car position and actions.
        
        Args:
            car_x: Car x position
            car_y: Car y position
            on_track: Whether car is on track
            drifting: Whether car is drifting (input action)
            speed: Current car speed
            drift_angle: Angle between velocity and heading (degrees)
            forward_progress: Distance moved in heading direction
            
        Returns:
            Current step reward
        """
        self.ticks += 1
        
        # OFF-TRACK: Enforce death - immediately end episode with large negative reward
        if not on_track:
            self.drift_score += OFF_TRACK_PENALTY
            # Reset combo when going off track
            self.consecutive_drift_ticks = 0
            self.combo_multiplier = 1
            self.combo_flash_timer = 0
            # End episode immediately on off-track
            if OFF_TRACK_ENFORCE_DEATH:
                self.done = True
                return OFF_TRACK_PENALTY
            else:
                return OFF_TRACK_PENALTY
        
        # Track previous laps for bonus calculation
        prev_laps = self.laps_completed
        
        # Check lap progress
        self._check_lap_progress(car_x, car_y)
        
        # Determine if actually drifting based on drift angle
        actual_drifting = drift_angle >= MIN_DRIFT_ANGLE
        self._is_drifting = actual_drifting
        
        # Update combo multiplier based on drift state
        self._update_combo(on_track, actual_drifting)
        
        # === REWARD FUNCTION ===
        reward = 0.0
        
        # 0. Living reward: Positive reward for staying on track (encourages survival)
        reward += LIVING_REWARD
        
        # 1. Forward progress reward (primary reward)
        reward += forward_progress * FORWARD_PROGRESS_SCALE
        
        # 3. Drift reward component: sin(drift_angle) * speed^2 * combo
        if actual_drifting and speed > 0.5:
            drift_radians = math.radians(drift_angle)
            drift_component = math.sin(drift_radians) * (speed ** 2) * DRIFT_REWARD_SCALE
            drift_component *= self.combo_multiplier
            reward += drift_component
            self.drift_score += drift_component
        
        # 4. Lap bonus (check if we completed a lap this step)
        if self.laps_completed > prev_laps:
            reward += LAP_BONUS
        
        # Check for game completion
        if self.laps_completed >= self.total_laps:
            self.done = True
            reward += LAP_BONUS  # Extra bonus for completing all laps
        
        return reward
    
    def _update_combo(self, on_track: bool, drifting: bool) -> None:
        """Update combo multiplier system."""
        if on_track and drifting:
            self.consecutive_drift_ticks += 1
            # Combo increases every 10 drift ticks on track
            new_multiplier = min(5, 1 + (self.consecutive_drift_ticks // 10))
            if new_multiplier > self.combo_multiplier:
                self.combo_multiplier = new_multiplier
                self.combo_flash_timer = 90  # Flash for 1.5 seconds at 60fps
        else:
            # Reset combo if off track or not drifting
            self.consecutive_drift_ticks = 0
            self.combo_multiplier = 1
            self.combo_flash_timer = 0
    
    def _check_lap_progress(self, x: float, y: float) -> None:
        """Track lap progress using checkpoints and start/finish line."""
        if self.track and hasattr(self.track, 'start_finish_line'):
            # Use start/finish line for lap counting
            on_line = self.track.start_finish_line.contains(x, y)
            self._check_line_crossing_lap(x, y, on_line)
            # Update previous position for next tick
            self._prev_x = x
            self._prev_y = y
        elif self.track:
            # Use track-defined checkpoints
            passed = self.track.get_checkpoints_passed(x, y)
            self.checkpoints_passed.update(passed)
            
            # Check if all required checkpoints passed for a lap
            if all(cp in self.checkpoints_passed for cp in self.required_checkpoints):
                self.laps_completed += 1
                self.checkpoints_passed.clear()
        else:
            # Fallback: original checkpoint logic for figure-8 track
            self._check_figure8_lap(x, y)
        
        # Update previous position
        self._prev_x = x
        self._prev_y = y
    
    def _is_clockwise_crossing(self, x: float, y: float, prev_x: float, prev_y: float) -> bool:
        """
        Check if the car is crossing the start/finish line in a clockwise direction.
        
        For an oval track with start position on the left side:
        - Clockwise motion means the car approaches from below (higher y) and exits above (lower y)
        - The car should be moving upward (negative y direction) when crossing
        
        Args:
            x: Current x position
            y: Current y position
            prev_x: Previous x position
            prev_y: Previous y position
            
        Returns:
            True if crossing in clockwise direction
        """
        if prev_x is None or prev_y is None:
            return False
        
        # Get start position to determine track orientation
        start_x, start_y, start_angle = self.track.get_start_position()
        
        # Calculate direction of movement
        dy = y - prev_y
        
        # For clockwise motion on an oval:
        # - When crossing the start/finish line on the left side of the track
        # - The car should be moving upward (dy < 0, i.e., y decreasing)
        # - This means the car is coming from the bottom of the track
        
        # The start position is on the left side of the oval
        # For clockwise: car goes left-side → top → right-side → bottom → back to left-side
        # So when crossing start line, car should be moving upward (negative dy)
        
        is_clockwise = dy < 0  # Moving upward (y decreasing) indicates clockwise
        
        return is_clockwise
    
    def _check_line_crossing_lap(self, x: float, y: float, on_line: bool) -> None:
        """
        Check for lap completion using start/finish line.
        Uses a simple state machine to detect line crossings.
        Only counts laps when crossing in clockwise direction.
        """
        if on_line:
            # Car is on the start/finish line
            if self._lap_progress >= 0.9:  # Already almost completed a lap
                # Check if crossing in clockwise direction
                if self._is_clockwise_crossing(x, y, self._prev_x, self._prev_y):
                    # Valid lap completion (clockwise direction)
                    self.laps_completed += 1
                    self._lap_progress = 0.0
                    self._last_line_crossing = self.ticks
            # Mark that we're on the line
            self._was_on_line = True
        else:
            # Car is off the line, increment progress
            # Progress increases as car moves away from line
            self._lap_progress = min(1.0, self._lap_progress + 0.01)
            self._was_on_line = False
    
    def _check_figure8_lap(self, x: float, y: float) -> None:
        """Original checkpoint logic for figure-8 track."""
        from utils.constants import (
            CENTER_X, CENTER_Y, LOOP_RADIUS_X, LOOP_RADIUS_Y,
            RIGHT_CENTER_X, LEFT_CENTER_X
        )
        
        # Divide each loop into checkpoints (0-3 for right, 4-7 for left)
        # Right loop checkpoints
        if x > RIGHT_CENTER_X + LOOP_RADIUS_X * 0.5:
            if y < CENTER_Y - LOOP_RADIUS_Y * 0.3:
                self.checkpoints_passed.add(0)  # Top-right
            elif y > CENTER_Y + LOOP_RADIUS_Y * 0.3:
                self.checkpoints_passed.add(3)  # Bottom-right
        if x < RIGHT_CENTER_X:
            if y < CENTER_Y:
                self.checkpoints_passed.add(1)  # Middle-right top
            else:
                self.checkpoints_passed.add(2)  # Middle-right bottom
        
        # Left loop checkpoints
        if x < LEFT_CENTER_X - LOOP_RADIUS_X * 0.5:
            if y < CENTER_Y - LOOP_RADIUS_Y * 0.3:
                self.checkpoints_passed.add(4)  # Top-left
            elif y > CENTER_Y + LOOP_RADIUS_Y * 0.3:
                self.checkpoints_passed.add(7)  # Bottom-left
        if x > LEFT_CENTER_X:
            if y < CENTER_Y:
                self.checkpoints_passed.add(5)  # Middle-left top
            else:
                self.checkpoints_passed.add(6)  # Middle-left bottom
        
        # Check for lap completion (pass all checkpoints on one loop)
        if (len(self.checkpoints_passed) >= 4 and 
            0 in self.checkpoints_passed and 3 in self.checkpoints_passed):
            # Completed right loop
            self.laps_completed += 1
            self.checkpoints_passed = set([4, 5, 6, 7])  # Reset to left loop checkpoints
        elif (len(self.checkpoints_passed) >= 4 and 
              4 in self.checkpoints_passed and 7 in self.checkpoints_passed):
            # Completed left loop
            self.laps_completed += 1
            self.checkpoints_passed = set([0, 1, 2, 3])  # Reset to right loop checkpoints
    
    @property
    def required_checkpoints(self) -> list:
        """Get required checkpoints for lap completion."""
        if self.track:
            return self.track.required_checkpoints
        return [0, 1, 2, 3, 4, 5, 6, 7]
    
    def update_combo_flash(self) -> None:
        """Update combo flash timer."""
        if self.combo_flash_timer > 0:
            self.combo_flash_timer -= 1
    
    @property
    def score(self) -> float:
        """Get current drift score."""
        return self.drift_score
    
    @property
    def combo_text(self) -> str:
        """Get combo text for HUD."""
        if self.combo_multiplier > 1:
            return f"COMBO x{self.combo_multiplier}"
        return ""
    
    @property
    def game_time(self) -> float:
        """Get elapsed game time in seconds."""
        return time.time() - self.start_time
