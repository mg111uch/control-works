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
LAP_BONUS = 750.0  # Must stay < |OFF_TRACK| so suicide loops never pay
FORWARD_PROGRESS_SCALE = 10.0
FORWARD_PROGRESS_CLIP = 5.0  # px/step cap, blocks teleport spikes
LIVING_PENALTY = -0.1  # Per-step penalty, encourages speed (code_fixes.md)
LIVING_REWARD = LIVING_PENALTY  # Backward-compat alias for tests
DRIFT_REWARD_SCALE = 3.0  # Phase-2b: slides must beat raw forward (10x) at speed
DRIFT_REWARD_CAP = 60.0  # Headroom for big fast slides with combo
MIN_DRIFT_ANGLE = 8.0  # Phase-2: easier to enter drift state
COMBO_TICKS_PER_LEVEL = 6  # Phase-2: faster combo buildup rewards sustained slides
LAP_DISTANCE = 2000.0  # Approx px per lap for distance-based progress
MIN_LAP_TICKS = 200  # Anti-spin: min steps between lap counts
SPEED_REWARD_SCALE = 0.5  # Pace pressure: fast lines out-earn slow-safe ones
WALL_APPROACH_SCALE = 4.0  # Wall discipline: fast + wall ahead must cost more
WALL_APPROACH_DIST = 0.3  # normalized ray dist under which penalty applies
WALL_APPROACH_SPEED = 1.0  # speed above which wall proximity is penalized
CP_BONUS = 50.0  # Reward per newly collected checkpoint (exploration pull)
STAGNATION_TICKS = 600  # End episode with no new checkpoint (circlers die fast)


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
        self.drift_score = 0  # drift-only component (analysis, not HUD)
        self.total_score = 0  # cumulative return sourcing HUD score
        self.combo_multiplier = 1
        self.consecutive_drift_ticks = 0
        self.combo_flash_timer = 0
        self.done = False
        self.stagnated = False  # episode ended by no-progress kill
        self.ticks_since_cp = 0  # steps since last new checkpoint
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
        # Episode already over: freeze scoring (manual loop keeps stepping
        # under the game-over screen; without this, off-track bleeds -1000/frame)
        if self.done:
            return 0.0
        self.ticks += 1
        
        # OFF-TRACK: Enforce death - accrued drift gains are forfeited, so
        # fatal slides net negative (suicide farming must not pay).
        if not on_track:
            forfeit = max(0.0, self.drift_score)
            penalty = OFF_TRACK_PENALTY - forfeit
            self.drift_score += penalty
            self.total_score += penalty
            # Reset combo when going off track
            self.consecutive_drift_ticks = 0
            self.combo_multiplier = 1
            self.combo_flash_timer = 0
            # End episode immediately on off-track
            if OFF_TRACK_ENFORCE_DEATH:
                self.done = True
            return penalty
        
        # Track previous laps for bonus calculation
        prev_laps = self.laps_completed
        
        # Check lap progress (returns newly collected checkpoint count)
        new_cps = self._check_lap_progress(car_x, car_y)
        if new_cps:
            self.ticks_since_cp = 0
        else:
            self.ticks_since_cp += 1
        
        # Determine if actually drifting based on drift angle
        actual_drifting = drift_angle >= MIN_DRIFT_ANGLE
        self._is_drifting = actual_drifting
        
        # Update combo multiplier based on drift state
        self._update_combo(on_track, actual_drifting)
        
        # === REWARD FUNCTION ===
        # Living penalty applies only when moving: a parked car scores 0
        # (no idle bleed on the start line), driving still earns positive.
        reward = LIVING_PENALTY if speed > 0.05 else 0.0

        # 0b. Speed reward: pace pressure (slow-safe lines must not out-earn fast ones)
        reward += max(0.0, speed) * SPEED_REWARD_SCALE
        
        # 1. Forward progress reward (primary, clipped)
        fp = float(max(-FORWARD_PROGRESS_CLIP, min(FORWARD_PROGRESS_CLIP, forward_progress)))
        reward += fp * FORWARD_PROGRESS_SCALE
        
        # 3. Drift reward component: sin(drift_angle) * speed^2 * combo, capped
        if actual_drifting and speed > 0.5:
            drift_radians = math.radians(min(drift_angle, 90.0))
            drift_component = math.sin(drift_radians) * (speed ** 2) * DRIFT_REWARD_SCALE
            drift_component *= self.combo_multiplier
            drift_component = min(drift_component, DRIFT_REWARD_CAP)
            reward += drift_component
            self.drift_score += drift_component
        
        # 4. Lap bonus (check if we completed a lap this step)
        if self.laps_completed > prev_laps:
            reward += LAP_BONUS
            self.ticks_since_cp = 0  # laps are progress too
        
        # 4b. Checkpoint bonus: reward visiting new boxes (explores new lobes)
        if new_cps:
            reward += CP_BONUS * new_cps
        
        # Check for game completion (no double bonus: lap bonus already given)
        if self.laps_completed >= self.total_laps:
            self.done = True

        # Stagnation kill: circling visited ground ends the episode (death)
        if not self.done and self.ticks_since_cp >= STAGNATION_TICKS:
            self.done = True
            self.stagnated = True

        # HUD score tracks TOTAL return (was drift-only: froze when not drifting)
        self.total_score += reward

        return reward
    
    def _update_combo(self, on_track: bool, drifting: bool) -> None:
        """Update combo multiplier system."""
        if on_track and drifting:
            self.consecutive_drift_ticks += 1
            # Combo increases every COMBO_TICKS_PER_LEVEL drift ticks on track
            new_multiplier = min(5, 1 + (self.consecutive_drift_ticks // COMBO_TICKS_PER_LEVEL))
            if new_multiplier > self.combo_multiplier:
                self.combo_multiplier = new_multiplier
                self.combo_flash_timer = 90  # Flash for 1.5 seconds at 60fps
        else:
            # Reset combo if off track or not drifting
            self.consecutive_drift_ticks = 0
            self.combo_multiplier = 1
            self.combo_flash_timer = 0
    
    def _check_lap_progress(self, x: float, y: float) -> int:
        """Collect checkpoints (in sequence when track requires it) and count laps.

        Line-crossing laps are gated on the full required set, so looping one
        lobe of a figure-8 scores nothing. Returns newly collected count.
        """
        new_cps = 0
        if self.track:
            required = list(getattr(self.track, 'required_checkpoints', []) or [])
            if required:
                if bool(getattr(self.track, 'sequence_required', False)):
                    while True:
                        remaining = [c for c in required if c not in self.checkpoints_passed]
                        if not remaining:
                            break
                        if self.track.check_checkpoint(x, y, remaining[0]):
                            self.checkpoints_passed.add(remaining[0])
                            new_cps += 1
                        else:
                            break
                else:
                    before = len(self.checkpoints_passed)
                    self.checkpoints_passed.update(self.track.get_checkpoints_passed(x, y))
                    new_cps = len(self.checkpoints_passed) - before
                complete = all(c in self.checkpoints_passed for c in required)
            else:
                complete = True
            if hasattr(self.track, 'start_finish_line'):
                # Use start/finish line for lap counting (gated on checkpoints)
                on_line = self.track.start_finish_line.contains(x, y)
                self._check_line_crossing_lap(x, y, on_line, complete)
            elif required and complete:
                self.laps_completed += 1
                self.checkpoints_passed.clear()
        else:
            # Fallback: original checkpoint logic for figure-8 track
            self._check_figure8_lap(x, y)

        # Update previous position
        self._prev_x = x
        self._prev_y = y
        return new_cps

    def next_checkpoint(self):
        """Center (x, y) of the next required checkpoint, or None.

        After a completed set, aims at the first box of the next lap so the
        egocentric observation always has a target.
        """
        if not self.track:
            return None
        required = list(getattr(self.track, 'required_checkpoints', []) or [])
        remaining = [c for c in required if c not in self.checkpoints_passed]
        if not remaining:
            remaining = required
        if not remaining:
            return None
        for cp in getattr(self.track, 'checkpoints', []):
            if cp.id == remaining[0]:
                return ((cp.x_min + cp.x_max) / 2.0, (cp.y_min + cp.y_max) / 2.0)
        return None
    
    def _is_clockwise_crossing(self, x: float, y: float, prev_x: float, prev_y: float) -> bool:
        """
        Check crossing direction via dot(movement, track forward).
        Robust vs old dy<0-only check which failed on non-oval tracks.
        """
        if prev_x is None or prev_y is None:
            return False
        dx, dy = x - prev_x, y - prev_y
        if dx * dx + dy * dy < 1e-6:  # Not moving
            return False
        try:
            _, _, start_angle = self.track.get_start_position()
        except Exception:
            return dy < 0
        import math as _m
        fx = _m.sin(_m.radians(start_angle))
        fy = -_m.cos(_m.radians(start_angle))
        return (dx * fx + dy * fy) > 0
    
    def _check_line_crossing_lap(self, x: float, y: float, on_line: bool,
                                   gated: bool = True) -> None:
        """
        Distance-based lap progress + direction-gated counting.
        Fixes old +0.01/tick free-lap exploit (spin = lap in 100 ticks).
        A lap only counts when gated (required checkpoint set complete).
        """
        if self._prev_x is not None and self._prev_y is not None:
            import math as _m
            dist = _m.hypot(x - self._prev_x, y - self._prev_y)
            # Hybrid: distance main + small time floor (0.005) so stationary
            # test harnesses still progress; real laps need movement.
            inc = min(0.02, dist / LAP_DISTANCE + 0.005)
            self._lap_progress = min(1.0, self._lap_progress + inc)
        if on_line and gated:
            if self._lap_progress >= 0.9 and (self.ticks - self._last_line_crossing) >= MIN_LAP_TICKS:
                if self._is_clockwise_crossing(x, y, self._prev_x, self._prev_y):
                    self.laps_completed += 1
                    self._lap_progress = 0.0
                    self._last_line_crossing = self.ticks
                    self.checkpoints_passed.clear()  # next lap re-collects
            self._was_on_line = True
        else:
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
        """HUD score = total cumulative return (forward + speed + drift + laps)."""
        return self.total_score
    
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
