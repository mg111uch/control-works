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
    angle: float = 0  # rotation deg (world→local uses -angle)
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
    
    def __init__(self, filepath: str, rasterize: bool = True):
        """
        Load track from JSON file.

        Args:
            filepath: Path to JSON track file
            rasterize: Build O(1) collision grid for polygon tracks
                (pass False for throwaway validation instances)
        """
        self.filepath = filepath
        self._rasterize_enabled = rasterize
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

        # Collision raster grid (polygon tracks only): O(1) lookups keep
        # ray marching fast; analytic shapes keep the exact path.
        self._grid = None
        if self._rasterize_enabled and any(e.type == 'polygon' for e in self.elements):
            self._grid = self._rasterize(cell=2)

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
                angle=elem_data.get('angle', 0),
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
        if self._grid is not None:
            cell, grid = self._grid
            ix = min(grid.shape[1] - 1, max(0, int(x / cell)))
            iy = min(grid.shape[0] - 1, max(0, int(y / cell)))
            return bool(grid[iy, ix])
        return self._analytic_is_on_track(x, y)

    def _rasterize(self, cell=2):
        """Sample analytic collision onto a coarse boolean grid."""
        import numpy as np
        nx, ny = self.screen_width // cell, self.screen_height // cell
        grid = np.zeros((ny, nx), dtype=bool)
        for iy in range(ny):
            for ix in range(nx):
                grid[iy, ix] = self._analytic_is_on_track(
                    (ix + 0.5) * cell, (iy + 0.5) * cell)
        return (cell, grid)

    def is_on_track_batch(self, xs, ys):
        """Vectorized is_on_track over point arrays (same semantics).

        Same per-point arithmetic as the scalar path (identical results);
        exists so ray marching can query hundreds of points in one call
        instead of one Python call per point.
        """
        import numpy as np
        xs = np.asarray(xs, dtype=np.float64)
        ys = np.asarray(ys, dtype=np.float64)
        if self._grid is not None:
            cell, grid = self._grid
            ix = np.clip((xs / cell).astype(int), 0, grid.shape[1] - 1)
            iy = np.clip((ys / cell).astype(int), 0, grid.shape[0] - 1)
            return np.asarray(grid[iy, ix], dtype=bool)
        on_track = np.zeros(xs.shape, dtype=bool)
        in_hole = np.zeros(xs.shape, dtype=bool)
        for element in self.elements:
            inside = _element_contains_batch(element, xs, ys)
            if element.is_hole:
                in_hole |= inside
            else:
                on_track |= inside
        return on_track & ~in_hole

    def _analytic_is_on_track(self, x: float, y: float) -> bool:
        """Exact element-loop collision (also feeds the rasterizer)."""
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
        if not self._in_bbox(x, y, element):
            return False
        if element.type == 'ellipse':
            # Normalized distance from center (in rotated local frame)
            lx, ly = self._to_local(x, y, element)
            dx = lx / element.radius_x
            dy = ly / element.radius_y
            return (dx ** 2 + dy ** 2) <= 1
        elif element.type == 'rectangle':
            lx, ly = self._to_local(x, y, element)
            half_w = element.width / 2
            half_h = element.height / 2
            return (abs(lx) <= half_w and
                    abs(ly) <= half_h)
        elif element.type == 'polygon':
            return self._in_polygon(x, y, element.vertices or [])

        return False
    @staticmethod
    def _in_bbox(x: float, y: float, element) -> bool:
        """Conservative bounding-box reject (cached on the element)."""
        bb = getattr(element, '_bbox', None)
        if bb is None:
            import math
            a = math.radians(getattr(element, 'angle', 0) or 0)
            ca, sa = abs(math.cos(a)), abs(math.sin(a))
            if element.type == 'ellipse':
                hx = math.sqrt((element.radius_x * ca) ** 2 + (element.radius_y * sa) ** 2)
                hy = math.sqrt((element.radius_x * sa) ** 2 + (element.radius_y * ca) ** 2)
                bb = (element.center_x - hx, element.center_y - hy,
                      element.center_x + hx, element.center_y + hy)
            elif element.type == 'rectangle':
                hx = (element.width * ca + element.height * sa) / 2
                hy = (element.width * sa + element.height * ca) / 2
                bb = (element.center_x - hx, element.center_y - hy,
                      element.center_x + hx, element.center_y + hy)
            elif element.type == 'polygon' and element.vertices:
                xs = [v[0] for v in element.vertices]
                ys = [v[1] for v in element.vertices]
                bb = (min(xs), min(ys), max(xs), max(ys))
            else:
                bb = (-1e9, -1e9, 1e9, 1e9)
            try:
                element._bbox = bb
            except Exception:
                pass
        return bb[0] <= x <= bb[2] and bb[1] <= y <= bb[3]

    @staticmethod
    def _to_local(x: float, y: float, element) -> Tuple[float, float]:
        """World point into the element's rotated local frame."""
        import math
        a = math.radians(getattr(element, 'angle', 0) or 0)
        dx, dy = x - element.center_x, y - element.center_y
        return (dx * math.cos(a) + dy * math.sin(a),
                -dx * math.sin(a) + dy * math.cos(a))

    @staticmethod
    def _in_polygon(x: float, y: float, vertices) -> bool:
        """Ray-casting point-in-polygon (works with [x, y] lists or tuples)."""
        inside = False
        n = len(vertices)
        if n < 3:
            return False
        j = n - 1
        for i in range(n):
            xi, yi = vertices[i][0], vertices[i][1]
            xj, yj = vertices[j][0], vertices[j][1]
            if ((yi > y) != (yj > y)) and \
                    (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            j = i
        return inside
    
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


def _element_contains_batch(element, xs, ys):
    """Vectorized _is_in_element over point arrays (no bbox prefilter).

    Same per-point arithmetic as the scalar path, so results match;
    horizontally-degenerate polygon edges yield nan comparisons (False),
    exactly like the scalar short-circuit.
    """
    import math
    import numpy as np
    if element.type == 'ellipse':
        a = math.radians(getattr(element, 'angle', 0) or 0)
        ca, sa = math.cos(a), math.sin(a)
        dx, dy = xs - element.center_x, ys - element.center_y
        lx = dx * ca + dy * sa
        ly = -dx * sa + dy * ca
        return (lx / element.radius_x) ** 2 + (ly / element.radius_y) ** 2 <= 1
    elif element.type == 'rectangle':
        a = math.radians(getattr(element, 'angle', 0) or 0)
        ca, sa = math.cos(a), math.sin(a)
        dx, dy = xs - element.center_x, ys - element.center_y
        lx = dx * ca + dy * sa
        ly = -dx * sa + dy * ca
        return (np.abs(lx) <= element.width / 2) & (np.abs(ly) <= element.height / 2)
    elif element.type == 'polygon':
        verts = element.vertices or []
        if len(verts) < 3:
            return np.zeros(xs.shape, dtype=bool)
        with np.errstate(all='ignore'):
            v = np.asarray(verts, dtype=np.float64)
            inside = np.zeros(xs.shape, dtype=bool)
            j = len(v) - 1
            for i in range(len(v)):
                xi, yi = v[i][0], v[i][1]
                xj, yj = v[j][0], v[j][1]
                cond = ((yi > ys) != (yj > ys)) & \
                    (xs < (xj - xi) * (ys - yi) / (yj - yi) + xi)
                inside ^= cond
                j = i
            return inside
    return np.zeros(xs.shape, dtype=bool)
