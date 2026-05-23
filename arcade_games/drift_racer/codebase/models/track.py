"""
Track data model for Drift King 2D.
Loads track definitions from JSON files and provides track detection logic.
"""

import json
import os
from typing import Tuple, List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class StartFinishLine:
    """Represents a start/finish line for lap counting."""
    x: float
    y: float
    angle: float  # Angle of the line in degrees (perpendicular to track direction)
    width: float  # Width of the line (spanning the track)
    
    def contains(self, x: float, y: float) -> bool:
        """Check if point is within the start/finish line."""
        import math
        # The line angle is perpendicular to car direction
        # We need to check if the point is within the line's width and thickness
        
        # Translate to line center
        dx = x - self.x
        dy = y - self.y
        
        # Rotate point to align with line's local coordinate system
        # The line spans along its angle, so we check perpendicular distance
        angle_rad = math.radians(self.angle)
        cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
        
        # Local coordinates: 
        # local_x = distance along the line direction
        # local_y = distance perpendicular to the line (thickness direction)
        local_x = dx * cos_a + dy * sin_a
        local_y = -dx * sin_a + dy * cos_a
        
        # Check if within line width (along local_x) and thickness (local_y)
        return (abs(local_x) <= self.width / 2 and abs(local_y) <= 15)


@dataclass
class TrackElement:
    """Represents a single track element (ellipse, rectangle, etc.)."""
    type: str
    center_x: float
    center_y: float
    radius_x: float = 0
    radius_y: float = 0
    width: float = 0
    height: float = 0
    is_hole: bool = False
    color: Optional[Tuple[int, int, int]] = None
    border_width: int = 2
    vertices: Optional[List[Tuple[float, float]]] = None
    
    @property
    def rect(self) -> Tuple[int, int, int, int]:
        """Get pygame rect tuple for ellipse/rectangle elements."""
        return (
            int(self.center_x - self.radius_x),
            int(self.center_y - self.radius_y),
            int(self.radius_x * 2),
            int(self.radius_y * 2)
        )


@dataclass
class Checkpoint:
    """Represents a checkpoint for lap tracking."""
    id: int
    type: str
    x_min: float = 0
    x_max: float = 0
    y_min: float = 0
    y_max: float = 0
    
    def contains(self, x: float, y: float) -> bool:
        """Check if point is within checkpoint bounds."""
        return (self.x_min <= x <= self.x_max and 
                self.y_min <= y <= self.y_max)


class Track:
    """
    Track data model loaded from JSON file.
    
    Handles track element parsing, collision detection, and checkpoint tracking.
    """
    
    def __init__(self, filepath: str):
        """
        Load track from JSON file.
        
        Args:
            filepath: Path to JSON track file
        """
        self.filepath = filepath
        self.data = self._load(filepath)
        self.elements = self._parse_elements()
        self.checkpoints = self._parse_checkpoints()
        self._setup_track_data()
    
    def _load(self, filepath: str) -> Dict[str, Any]:
        """Load and parse JSON file."""
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def _setup_track_data(self) -> None:
        """Extract commonly used track data."""
        self.name = self.data.get('name', 'Unknown Track')
        self.version = self.data.get('version', '1.0')
        self.difficulty = self.data.get('difficulty', 'medium')
        
        # Screen size override if present
        screen_size = self.data.get('screen_size', {})
        self.screen_width = screen_size.get('width', 600)
        self.screen_height = screen_size.get('height', 400)
        
        # Visual settings
        visual = self.data.get('visual', {})
        self.track_color = tuple(visual.get('track_color', [80, 80, 80]))
        self.border_color = tuple(visual.get('border_color', [255, 255, 255]))
        self.grass_color = tuple(visual.get('grass_color', [0, 128, 0]))
        self.background_color = tuple(visual.get('background_color', [128, 128, 128]))
        self.border_width = visual.get('border_width', 2)
        
        # Lap completion settings
        lap_config = self.data.get('lap_completion', {})
        self.required_checkpoints = lap_config.get('required_checkpoints', [])
        self.sequence_required = lap_config.get('sequence_required', False)
        
        # Start/finish line
        self.start_finish_line = self._create_start_finish_line()
    
    def _parse_elements(self) -> List[TrackElement]:
        """Parse track elements from JSON data."""
        elements = []
        visual = self.data.get('visual', {})
        track_color = tuple(visual.get('track_color', [80, 80, 80]))
        grass_color = tuple(visual.get('grass_color', [0, 128, 0]))
        
        for elem_data in self.data.get('track_elements', []):
            element = TrackElement(
                type=elem_data.get('type', 'ellipse'),
                center_x=elem_data.get('center_x', 0),
                center_y=elem_data.get('center_y', 0),
                radius_x=elem_data.get('radius_x', 0),
                radius_y=elem_data.get('radius_y', 0),
                width=elem_data.get('width', 0),
                height=elem_data.get('height', 0),
                is_hole=elem_data.get('is_hole', False),
                color=grass_color if elem_data.get('is_hole', False) else track_color,
                border_width=visual.get('border_width', 2),
                vertices=elem_data.get('vertices', None)
            )
            elements.append(element)
        
        return elements
    
    def _parse_checkpoints(self) -> List[Checkpoint]:
        """Parse checkpoints from JSON data."""
        checkpoints = []
        for cp_data in self.data.get('checkpoints', []):
            checkpoint = Checkpoint(
                id=cp_data.get('id', 0),
                type=cp_data.get('type', 'position'),
                x_min=cp_data.get('x_min', 0),
                x_max=cp_data.get('x_max', 0),
                y_min=cp_data.get('y_min', 0),
                y_max=cp_data.get('y_max', 0)
            )
            checkpoints.append(checkpoint)
        return checkpoints
    
    def _create_start_finish_line(self) -> StartFinishLine:
        """
        Create start/finish line at the start position.
        Spans half the track width based on track elements.
        """
        start_x, start_y, start_angle = self.get_start_position()
        
        # Calculate track width at start position
        track_width = self._get_track_width_at(start_x, start_y)
        
        # Rotate line 180° from car direction (perpendicular to track, rotated 90° more)
        line_angle = start_angle + 180
        
        return StartFinishLine(
            x=start_x,
            y=start_y,
            angle=line_angle,
            width=track_width / 2  # Half the track width
        )
    
    def _get_track_width_at(self, x: float, y: float) -> float:
        """
        Calculate track width at a specific position.
        Used for start/finish line sizing.
        """
        # For ellipse tracks, calculate width at position
        for element in self.elements:
            if element.type == 'ellipse' and not element.is_hole:
                # Calculate direction from center to position
                dx = x - element.center_x
                dy = y - element.center_y
                
                if dx == 0 and dy == 0:
                    return element.radius_x * 2
                
                # Calculate perpendicular distance (half-width of ellipse at that angle)
                # For ellipse: width at angle theta = 2 * a * b / sqrt((b*cos(theta))^2 + (a*sin(theta))^2)
                import math
                theta = math.atan2(dy, dx)
                cos_t, sin_t = math.cos(theta), math.sin(theta)
                denominator = math.sqrt((element.radius_x * cos_t)**2 + (element.radius_y * sin_t)**2)
                if denominator > 0:
                    half_width = element.radius_x * element.radius_y / denominator
                    return half_width * 2
        
        # Default width if no track elements found
        return 100.0
    
    def get_start_position(self) -> Tuple[float, float, float]:
        """
        Get car start position from track data.
        
        Returns:
            Tuple of (x, y, angle)
        """
        start = self.data.get('start_position', {})
        return (
            start.get('x', 300),
            start.get('y', 200),
            start.get('angle', 0)
        )
    
    def is_on_track(self, x: float, y: float) -> bool:
        """
        Check if position (x, y) is on valid track surface.
        
        Args:
            x: X coordinate to check
            y: Y coordinate to check
            
        Returns:
            True if on track, False otherwise
        """
        on_track = False
        in_hole = False
        
        for element in self.elements:
            if element.is_hole:
                if self._is_in_element(x, y, element):
                    in_hole = True
            else:
                if self._is_in_element(x, y, element):
                    on_track = True
        
        return on_track and not in_hole
    
    def _is_in_element(self, x: float, y: float, element: TrackElement) -> bool:
        """
        Check if point is within a track element.
        
        Args:
            x: X coordinate to check
            y: Y coordinate to check
            element: Track element to check against
            
        Returns:
            True if point is within element bounds
        """
        if element.type == 'ellipse':
            # Normalized distance from center
            dx = (x - element.center_x) / element.radius_x
            dy = (y - element.center_y) / element.radius_y
            return (dx ** 2 + dy ** 2) <= 1
        elif element.type == 'rectangle':
            half_w = element.width / 2
            half_h = element.height / 2
            return (abs(x - element.center_x) <= half_w and 
                    abs(y - element.center_y) <= half_h)
        
        return False
    
    def check_checkpoint(self, x: float, y: float, checkpoint_id: int) -> bool:
        """
        Check if car is at given checkpoint.
        
        Args:
            x: Car x position
            y: Car y position
            checkpoint_id: ID of checkpoint to check
            
        Returns:
            True if car is at checkpoint
        """
        for checkpoint in self.checkpoints:
            if checkpoint.id == checkpoint_id:
                return checkpoint.contains(x, y)
        return False
    
    def get_checkpoints_passed(self, x: float, y: float) -> List[int]:
        """
        Get list of all checkpoints the car has passed.
        
        Args:
            x: Car x position
            y: Car y position
            
        Returns:
            List of checkpoint IDs that contain the car
        """
        passed = []
        for checkpoint in self.checkpoints:
            if checkpoint.contains(x, y):
                passed.append(checkpoint.id)
        return passed
    
    def check_start_finish_line(self, x: float, y: float) -> bool:
        """
        Check if car has crossed the start/finish line.
        
        Args:
            x: Car x position
            y: Car y position
            
        Returns:
            True if car is on the start/finish line
        """
        return self.start_finish_line.contains(x, y)
