"""
Ray casting system for track boundary detection.
10 rays spanning 180° FOV with visualization support.
"""

import math
from typing import List, Tuple
import numpy as np


class RayCaster:
    """Ray casting system for track boundary detection."""
    
    def __init__(self, num_rays: int = 10, fov: float = 180.0, 
                 max_distance: float = 200.0, step_size: float = 2.0):
        """
        Initialize ray caster.
        
        Args:
            num_rays: Number of rays (10 for 180° with 20° intervals)
            fov: Field of view in degrees (180)
            max_distance: Maximum ray distance
            step_size: Step size for ray marching
        """
        self.num_rays = num_rays
        self.fov = fov
        self.max_distance = max_distance
        self.step_size = step_size
        
        # Calculate angle step: 180° / (10 - 1) = 20°
        self.angle_step = fov / (num_rays - 1)
        
        # Store last cast results for visualization
        self.last_endpoints: List[Tuple[float, float]] = []
        self.last_distances: np.ndarray = np.zeros(num_rays)
    
    def cast_rays(self, car_x: float, car_y: float, car_angle: float,
                  track) -> np.ndarray:
        """
        Cast 10 rays over 180° FOV and return normalized distances.
        Rays extend in FRONT of the car (relative to car heading).
        
        Args:
            car_x, car_y: Car position
            car_angle: Car heading in degrees (0 = facing up)
            track: Track object with is_on_track method
            
        Returns:
            Array of 10 normalized distances (0-1) for ML input
        """
        distances = []
        endpoints = []
        
        # Convert game angle to screen angle for ray casting
        # In game: 0°=up, 90°=right, 180°=down, 270°=left
        # Screen: 0°=right, 90°=down, 180°=left, 270°=up
        # To convert game angle to screen: rotate 180° 
        # Game 0° (up) = Screen 180° (left) = add 270° to game angle
        # screen = car_angle + 270° (rotate 180°)
        
        screen_angle = car_angle + 270
        
        start_angle = screen_angle - self.fov / 2
        
        for i in range(self.num_rays):
            angle = start_angle + i * self.angle_step
            dist, end_x, end_y = self._cast_single_ray(
                car_x, car_y, angle, track
            )
            distances.append(dist)
            endpoints.append((end_x, end_y))
        
        # Store for visualization
        self.last_endpoints = endpoints
        self.last_distances = np.array(distances)
        
        # Normalize to 0-1 range
        return np.clip(np.array(distances) / self.max_distance, 0.0, 1.0)
    
    def cast_rays_raw(self, car_x: float, car_y: float, car_angle: float,
                      track) -> List[float]:
        """
        Cast rays and return raw distances (not normalized).
        Rays extend in FRONT of the car (relative to car heading).
        
        Args:
            car_x, car_y: Car position
            car_angle: Car heading in degrees
            track: Track object
            
        Returns:
            List of raw distances to boundaries
        """
        distances = []
        
        screen_angle = car_angle + 270
        start_angle = screen_angle - self.fov / 2
        
        for i in range(self.num_rays):
            angle = start_angle + i * self.angle_step
            dist, end_x, end_y = self._cast_single_ray(
                car_x, car_y, angle, track
            )
            distances.append(dist)
        
        return distances
    
    def _cast_single_ray(self, start_x: float, start_y: float, 
                         angle_degrees: float, track
                         ) -> Tuple[float, float, float]:
        """
        Cast single ray and find distance to boundary.
        
        Returns:
            Tuple of (distance, end_x, end_y)
        """
        angle_rad = math.radians(angle_degrees)
        cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
        
        distance = 0.0
        x, y = start_x, start_y
        prev_on_track = track.is_on_track(x, y)
        
        while distance < self.max_distance:
            x += cos_a * self.step_size
            y += sin_a * self.step_size
            distance += self.step_size
            
            current_on_track = track.is_on_track(x, y)
            if current_on_track != prev_on_track:
                # Boundary crossed - binary search for exact position
                boundary_x, boundary_y = self._find_boundary(
                    x - cos_a * self.step_size, y - sin_a * self.step_size,
                    x, y, angle_rad, track
                )
                actual_dist = math.sqrt(
                    (boundary_x - start_x)**2 + (boundary_y - start_y)**2
                )
                return actual_dist, boundary_x, boundary_y
            
            prev_on_track = current_on_track
        
        # No boundary hit - return max distance endpoint
        return self.max_distance, x, y
    
    def _find_boundary(self, x1: float, y1: float, x2: float, y2: float,
                      angle_rad: float, track) -> Tuple[float, float]:
        """Binary search for exact boundary position."""
        cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
        for _ in range(10):
            mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
            if track.is_on_track(mid_x, mid_y):
                x1, y1 = mid_x, mid_y
            else:
                x2, y2 = mid_x, mid_y
        return (x1 + x2) / 2, (y1 + y2) / 2
    
    def get_ray_angles(self, car_angle: float) -> List[float]:
        """
        Get 10 ray angles relative to WORLD coordinates.
        Rays extend in FRONT of the car.
        
        Args:
            car_angle: Car heading in degrees
            
        Returns:
            List of angles for each ray
        """
        screen_angle = car_angle + 270
        start_angle = screen_angle - self.fov / 2
        return [start_angle + i * self.angle_step for i in range(self.num_rays)]
    
    def get_ml_state(self, car_x: float, car_y: float, car_angle: float,
                     track, screen_width: int = 600, screen_height: int = 400
                     ) -> np.ndarray:
        """
        Get combined state for neural network input.
        
        Args:
            car_x, car_y: Car position
            car_angle: Car heading in degrees
            track: Track object
            
        Returns:
            Combined state array (14 features: 4 car + 10 rays)
        """
        # Base car state (normalized)
        car_state = np.array([
            car_x / screen_width,
            car_y / screen_height,
            (car_angle % 360) / 360.0,
            0.0  # Speed placeholder - set externally if needed
        ])
        
        # Ray cast readings (10 rays)
        ray_state = self.cast_rays(car_x, car_y, car_angle, track)
        
        return np.concatenate([car_state, ray_state])
    
    def draw_rays(self, screen, car_x: float, car_y: float,
                  color_safe: Tuple[int, int, int] = (0, 255, 0),
                  color_boundary: Tuple[int, int, int] = (255, 0, 0),
                  line_width: int = 1) -> None:
        """
        Draw ray casting visualization.
        
        Args:
            screen: Pygame surface
            car_x, car_y: Car position
            color_safe: Color for rays hitting track (green)
            color_boundary: Color for rays hitting boundary (red)
            line_width: Line width for rays
        """
        import pygame
        
        if not self.last_endpoints or len(self.last_endpoints) == 0:
            return
        
        # Get ray lengths from stored distances
        distances = self.last_distances
        max_dist = self.max_distance
        
        for i, (end_x, end_y) in enumerate(self.last_endpoints):
            # Determine color: red if ray hit boundary early, green otherwise
            ray_length = math.sqrt((end_x - car_x)**2 + (end_y - car_y)**2)
            
            # If ray is significantly shorter than max, it hit a boundary
            if ray_length < max_dist * 0.95:
                color = color_boundary
            else:
                color = color_safe
            
            pygame.draw.line(
                screen, color,
                (car_x, car_y), (end_x, end_y),
                line_width
            )
            
            # Draw endpoint dot
            pygame.draw.circle(screen, color, (int(end_x), int(end_y)), 3)


# Global ray caster instance for easy access
_default_ray_caster: RayCaster = None

def get_ray_caster() -> RayCaster:
    """Get the global ray caster instance."""
    global _default_ray_caster
    if _default_ray_caster is None:
        _default_ray_caster = RayCaster(num_rays=10, fov=180.0, max_distance=200.0)
    return _default_ray_caster


if __name__ == "__main__":
    # Test ray caster
    from models.track import Track
    
    # Load test track
    track = Track("tracks/simple_oval.json")
    
    # Create ray caster
    ray_caster = RayCaster(num_rays=10, fov=180.0, max_distance=200.0)
    
    # Test from start position
    start_x, start_y, start_angle = track.get_start_position()
    
    print(f"Testing ray caster from ({start_x}, {start_y}) facing {start_angle}°")
    print(f"Ray angles: {[f'{a:.1f}°' for a in ray_caster.get_ray_angles(start_angle)]}")
    
    # Cast rays
    normalized = ray_caster.cast_rays(start_x, start_y, start_angle, track)
    print(f"Normalized distances: {[f'{d:.2f}' for d in normalized]}")
    
    # Get ML state
    ml_state = ray_caster.get_ml_state(start_x, start_y, start_angle, track)
    print(f"ML state shape: {ml_state.shape}")
