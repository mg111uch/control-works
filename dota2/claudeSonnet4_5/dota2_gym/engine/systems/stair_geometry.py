"""
Stair Geometry Module

Provides geometry utilities for stair navigation including:
- Vec2: 2D vector operations
- StairPolygon: Represents a stair segment between elevations
- ElevationZone: Represents high-ground/low-ground areas
- Geometry functions: point-in-polygon, segment distance, etc.
"""
import math
from typing import List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Vec2:
    """2D vector with basic operations"""
    x: float
    y: float
    
    def __add__(self, other: 'Vec2') -> 'Vec2':
        return Vec2(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: 'Vec2') -> 'Vec2':
        return Vec2(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar: float) -> 'Vec2':
        return Vec2(self.x * scalar, self.y * scalar)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vec2):
            return False
        return abs(self.x - other.x) < 1e-10 and abs(self.y - other.y) < 1e-10
    
    def length(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y)
    
    def length_squared(self) -> float:
        return self.x * self.x + self.y * self.y
    
    def normalize(self) -> 'Vec2':
        length = self.length()
        if length < 1e-10:
            return Vec2(0.0, 0.0)
        return Vec2(self.x / length, self.y / length)
    
    def dot(self, other: 'Vec2') -> float:
        return self.x * other.x + self.y * other.y
    
    def distance_to(self, other: 'Vec2') -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def __repr__(self) -> str:
        return f"Vec2({self.x:.2f}, {self.y:.2f})"


@dataclass
class ElevationZone:
    """Represents a high-ground or low-ground area"""
    name: str
    elevation: float  # e.g., 1.0 for low ground, 2.0 for high ground
    polygon: List[Vec2]
    
    def is_point_inside(self, point: Vec2) -> bool:
        """Check if point is inside this elevation zone using ray-casting"""
        return is_point_in_polygon(point, self.polygon)
    
    def get_bounding_box(self) -> Tuple[float, float, float, float]:
        """Return (min_x, max_x, min_y, max_y) bounding box"""
        if not self.polygon:
            return (0, 0, 0, 0)
        xs = [p.x for p in self.polygon]
        ys = [p.y for p in self.polygon]
        return (min(xs), max(xs), min(ys), max(ys))


@dataclass
class StairPolygon:
    """Represents a stair segment connecting two elevations"""
    name: str
    p1: Vec2  # Start point
    p2: Vec2  # End point
    polygon: List[Vec2]  # Thickened stair polygon
    thickness: float
    
    @property
    def midpoint(self) -> Vec2:
        """Return the midpoint of the stair segment"""
        return Vec2(
            (self.p1.x + self.p2.x) / 2.0,
            (self.p1.y + self.p2.y) / 2.0
        )
    
    @property
    def length(self) -> float:
        """Return the length of the stair segment"""
        return self.p1.distance_to(self.p2)
    
    def is_point_on_stair(self, point: Vec2, tolerance: float = 1.0) -> bool:
        """Check if point is on or near the stair segment"""
        return point_to_segment_distance(point, self.p1, self.p2) < tolerance
    
    def get_progress_along_stair(self, point: Vec2) -> float:
        """Return progress (0-1) along the stair from p1 to p2"""
        total_length = self.length
        if total_length < 1e-10:
            return 0.0
        return self.p1.distance_to(point) / total_length
    
    def get_direction(self) -> Vec2:
        """Return normalized direction from p1 to p2"""
        direction = self.p2 - self.p1
        return direction.normalize()


# ── Geometry Helper Functions ───────────────────────────────────────────────

def is_point_in_polygon(point: Vec2, polygon: List[Vec2]) -> bool:
    """
    Test if point is inside polygon using ray-casting algorithm.
    Returns True if point is inside the polygon.
    """
    if not polygon:
        return False
    
    n = len(polygon)
    inside = False
    
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i].x, polygon[i].y
        xj, yj = polygon[j].x, polygon[j].y
        
        # Check if ray crosses the edge
        if ((yi > point.y) != (yj > point.y)) and \
           (point.x < (xj - xi) * (point.y - yi) / (yj - yi + 1e-10) + xi):
            inside = not inside
        
        j = i
    
    return inside


def point_to_segment_distance(point: Vec2, p1: Vec2, p2: Vec2) -> float:
    """Calculate the shortest distance from point to line segment p1-p2"""
    # Vector from p1 to p2
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    
    # Vector from p1 to point
    px = point.x - p1.x
    py = point.y - p1.y
    
    # Calculate projection parameter
    length_sq = dx * dx + dy * dy
    if length_sq < 1e-10:
        # p1 and p2 are the same point
        return math.sqrt(px * px + py * py)
    
    t = max(0.0, min(1.0, (px * dx + py * dy) / length_sq))
    
    # Closest point on segment
    closest_x = p1.x + t * dx
    closest_y = p1.y + t * dy
    
    # Distance from point to closest point
    return math.sqrt((point.x - closest_x)**2 + (point.y - closest_y)**2)


def distance_point_to_polygon(point: Vec2, polygon: List[Vec2]) -> float:
    """Calculate minimum distance from point to polygon edges"""
    if not polygon:
        return float('inf')
    
    if is_point_in_polygon(point, polygon):
        return 0.0
    
    min_dist = float('inf')
    n = len(polygon)
    
    for i in range(n):
        p1 = polygon[i]
        p2 = polygon[(i + 1) % n]
        dist = point_to_segment_distance(point, p1, p2)
        min_dist = min(min_dist, dist)
    
    return min_dist


def generate_stair_polygon(p1: Tuple[float, float], p2: Tuple[float, float], 
                           thickness: float) -> List[Vec2]:
    """
    Generate a thickened stair polygon from a line segment.
    
    Args:
        p1: Start point (x, y)
        p2: End point (x, y)
        thickness: Width of the stair polygon
    
    Returns:
        List of 4 Vec2 points forming the thickened polygon
    """
    # Handle zero-length case
    if abs(p1[0] - p2[0]) < 1e-10 and abs(p1[1] - p2[1]) < 1e-10:
        return []
    
    # Calculate perpendicular offset
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = math.sqrt(dx * dx + dy * dy)
    
    # Normalize and get perpendicular
    nx = -dy / length
    ny = dx / length
    
    half_thickness = thickness / 2.0
    
    # Create 4 corners
    p1_left = Vec2(p1[0] + nx * half_thickness, p1[1] + ny * half_thickness)
    p1_right = Vec2(p1[0] - nx * half_thickness, p1[1] - ny * half_thickness)
    p2_left = Vec2(p2[0] + nx * half_thickness, p2[1] + ny * half_thickness)
    p2_right = Vec2(p2[0] - nx * half_thickness, p2[1] - ny * half_thickness)
    
    return [p1_left, p1_right, p2_right, p2_left]


def find_nearest_stair(point: Vec2, stairs: List[StairPolygon]) -> Optional[StairPolygon]:
    """Find the nearest stair polygon to a given point"""
    if not stairs:
        return None
    
    nearest = None
    min_dist = float('inf')
    
    for stair in stairs:
        # Check if point is already on this stair
        if stair.is_point_on_stair(point, stair.thickness):
            return stair
        
        # Otherwise find distance to midpoint
        dist = point.distance_to(stair.midpoint)
        if dist < min_dist:
            min_dist = dist
            nearest = stair
    
    return nearest


def calculate_stair_progress(point: Vec2, stair: StairPolygon) -> float:
    """Calculate progress (0-1) along a stair from p1 to p2"""
    return stair.get_progress_along_stair(point)


def get_elevation_at_position(point: Vec2, zones: List[ElevationZone]) -> float:
    """
    Get elevation level at a given position.
    Returns 1.0 for low ground (default), or higher for high ground.
    """
    for zone in zones:
        if zone.is_point_inside(point):
            return zone.elevation
    return 1.0  # Default low ground elevation


def can_cross_elevation_directly(from_pos: Vec2, to_pos: Vec2, 
                                   zones: List[ElevationZone],
                                   stairs: List[StairPolygon]) -> bool:
    """
    Check if direct movement between positions is allowed.
    Returns False if crossing elevation boundary without using a stair.
    """
    from_elev = get_elevation_at_position(from_pos, zones)
    to_elev = get_elevation_at_position(to_pos, zones)
    
    # Same elevation - always allowed
    if from_elev == to_elev:
        return True
    
    # Different elevations - need to check if crossing a stair
    for stair in stairs:
        if segments_intersect(
            (from_pos.x, from_pos.y), (to_pos.x, to_pos.y),
            (stair.p1.x, stair.p1.y), (stair.p2.x, stair.p2.y)
        ):
            return True
    
    return False


def segments_intersect(a1: Tuple[float, float], a2: Tuple[float, float],
                       b1: Tuple[float, float], b2: Tuple[float, float]) -> bool:
    """
    Test if line segment a1-a2 intersects with segment b1-b2.
    Returns True if they intersect (including endpoint touching).
    """
    x1, y1 = a1
    x2, y2 = a2
    x3, y3 = b1
    x4, y4 = b2
    
    # Calculate denominators
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    
    # If denom is 0, lines are parallel
    if abs(denom) < 1e-10:
        return False
    
    # Calculate intersection parameters
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
    
    # Check if intersection is within both segments
    return -1e-10 <= t <= 1 + 1e-10 and -1e-10 <= u <= 1 + 1e-10


def heuristic(a: Vec2, b: Vec2) -> float:
    """Euclidean distance heuristic for pathfinding"""
    return a.distance_to(b)


def distance(a: Vec2, b: Vec2) -> float:
    """Euclidean distance between two points"""
    return a.distance_to(b)


class PriorityQueue:
    """A priority queue for A* algorithm."""
    
    def __init__(self):
        self.elements = []
    
    def empty(self) -> bool:
        return len(self.elements) == 0
    
    def put(self, item: any, priority: float) -> None:
        heapq.heappush(self.elements, (priority, item))
    
    def get(self) -> any:
        return heapq.heappop(self.elements)[1]


import heapq


def find_path_a_star(start: Vec2, goal: Vec2, high_polys: List[List[Vec2]],
                      stairs: List[StairPolygon]) -> Optional[List[Vec2]]:
    """
    A* pathfinding to navigate from start to goal.
    Uses stair endpoints as waypoints.
    Returns list of waypoints to follow, or None if no path found.
    """
    nodes = []
    node_positions = []
    
    # Add start position as first node
    nodes.append(('start', start))
    node_positions.append(start)
    
    # Add stair endpoints as potential waypoints
    for i, stair in enumerate(stairs):
        nodes.append((f'stair_{i}_p1', stair.p1))
        node_positions.append(stair.p1)
        nodes.append((f'stair_{i}_p2', stair.p2))
        node_positions.append(stair.p2)
    
    # Add goal position as last node
    nodes.append(('goal', goal))
    node_positions.append(goal)
    
    # Build adjacency list
    n = len(nodes)
    adjacency = [[] for _ in range(n)]
    
    elevation_zones = []
    for poly in high_polys:
        elevation_zones.append(ElevationZone(
            name=f"high_ground_{len(elevation_zones)}",
            elevation=2.0,
            polygon=poly
        ))
    
    for i in range(n):
        for j in range(n):
            if i != j:
                from_pos = node_positions[i]
                to_pos = node_positions[j]
                if can_move_direct(from_pos, to_pos, elevation_zones, stairs):
                    dist = distance(from_pos, to_pos)
                    adjacency[i].append((j, dist))
    
    # Check if direct path exists
    if can_move_direct(start, goal, elevation_zones, stairs):
        return [goal]
    
    # A* algorithm
    start_idx = 0
    goal_idx = n - 1
    
    frontier = PriorityQueue()
    frontier.put(start_idx, 0)
    
    came_from = {start_idx: None}
    cost_so_far = {start_idx: 0}
    
    while not frontier.empty():
        current = frontier.get()
        
        if current == goal_idx:
            break
        
        for next_node, cost in adjacency[current]:
            new_cost = cost_so_far[current] + cost
            
            if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                cost_so_far[next_node] = new_cost
                priority = new_cost + heuristic(node_positions[next_node], node_positions[goal_idx])
                frontier.put(next_node, priority)
                came_from[next_node] = current
    
    # Reconstruct path
    if goal_idx not in came_from:
        return None
    
    path = []
    current = goal_idx
    while current is not None:
        path.append(node_positions[current])
        current = came_from[current]
    
    path.reverse()
    return path


def can_move_direct(from_pos: Vec2, to_pos: Vec2, 
                    zones: List[ElevationZone],
                    stairs: List[StairPolygon]) -> bool:
    """
    Check if entity can move directly from from_pos to to_pos.
    Returns True if movement is allowed.
    """
    from_elev = get_elevation_at_position(from_pos, zones)
    to_elev = get_elevation_at_position(to_pos, zones)
    
    # Check if crossing any stair
    crossing_stair = False
    for stair in stairs:
        if segments_intersect(
            (from_pos.x, from_pos.y), (to_pos.x, to_pos.y),
            (stair.p1.x, stair.p1.y), (stair.p2.x, stair.p2.y)
        ):
            crossing_stair = True
            break
    
    # If elevation changes and not crossing stair, movement is blocked
    if from_elev != to_elev and not crossing_stair:
        return False
    
    # If both on same elevation, movement is always allowed
    if from_elev == to_elev:
        return True
    
    # If crossing stair, allow movement
    return crossing_stair


def get_stair_endpoints(stairs: List[StairPolygon]) -> List[Vec2]:
    """Extract unique endpoints from stairs"""
    endpoints = []
    seen = set()
    
    for stair in stairs:
        p1_key = (round(stair.p1.x, 3), round(stair.p1.y, 3))
        p2_key = (round(stair.p2.x, 3), round(stair.p2.y, 3))
        
        if p1_key not in seen:
            endpoints.append(stair.p1)
            seen.add(p1_key)
        if p2_key not in seen:
            endpoints.append(stair.p2)
            seen.add(p2_key)
    
    return endpoints


def find_nearest_stair_to_position(position: Vec2, stairs: List[StairPolygon],
                                    current_elev: float,
                                    max_search_distance: float = 200.0) -> Tuple[Optional[StairPolygon], Optional[Vec2]]:
    """
    Find the nearest stair that leads to the opposite elevation.
    
    Args:
        position: Current position
        stairs: List of stair polygons to search
        current_elev: Current elevation level
        max_search_distance: Maximum search radius (default 200.0 units)
    
    Returns:
        Tuple of (stair, nearest_endpoint) or (None, None) if no suitable stair
    """
    if not stairs:
        return None, None
    
    nearest_stair = None
    nearest_endpoint = None
    min_dist = float('inf')
    
    for stair in stairs:
        # NEW: Quick distance filter BEFORE detailed checks
        stair_center_x = (stair.p1.x + stair.p2.x) / 2
        stair_center_y = (stair.p1.y + stair.p2.y) / 2
        approx_dist = ((position.x - stair_center_x)**2 + (position.y - stair_center_y)**2)**0.5
        
        if approx_dist > max_search_distance:
            continue  # Skip distant stairs
        
        # Check if stair is usable (connects different elevations)
        p1_elev = get_elevation_at_position(stair.p1, [])
        p2_elev = get_elevation_at_position(stair.p2, [])
        
        # For simplicity, assume stairs always connect different elevations
        if abs(p1_elev - p2_elev) < 1e-10:
            continue
        
        # Find closest endpoint to position
        dist1 = position.distance_to(stair.p1)
        dist2 = position.distance_to(stair.p2)
        
        # Check which endpoint is on current elevation
        if abs(p1_elev - current_elev) < 1e-10 and dist1 < min_dist:
            nearest_stair = stair
            nearest_endpoint = stair.p1
            min_dist = dist1
        elif abs(p2_elev - current_elev) < 1e-10 and dist2 < min_dist:
            nearest_stair = stair
            nearest_endpoint = stair.p2
            min_dist = dist2
    
    return nearest_stair, nearest_endpoint
