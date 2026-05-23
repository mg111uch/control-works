"""Movement system with deterministic NumPy calculations"""
import numpy as np
from typing import Optional, List, Tuple
from engine.ecs.entity_manager import EntityManager
from engine.ecs.components import PositionComponent, MovementComponent, CollisionComponent
from engine.systems.stair_geometry import Vec2


class MovementSystem:
    """
    Handles entity movement with deterministic calculations.
    Uses fixed timestep and NumPy for reproducibility.
    Supports body blocking - entities cannot walk through each other.
    Supports stair waypoints for elevation changes.
    """
    
    def __init__(self, entity_manager: EntityManager, dt: float = 1/15, game_model=None):
        self.entity_manager = entity_manager
        self.dt = dt  # Fixed timestep (66.6ms)
        self.stair_registry = None  # Will be set via set_stair_registry
        self.spatial_hash = None  # Will be set via set_spatial_hash
        self.game_model = game_model  # Reference to game model
        self._blocking_entities_cache = set()  # Cache of entities that block movement
        self._cache_valid = False  # Flag to track if cache is valid
    
    def set_spatial_hash(self, spatial_hash) -> None:
        """Set the spatial hash for efficient collision detection"""
        self.spatial_hash = spatial_hash
    
    def set_stair_registry(self, registry) -> None:
        """Set the stair registry for stair-aware pathfinding"""
        self.stair_registry = registry
    
    def update(self) -> None:
        """Update all entities with movement"""
        entities = self.entity_manager.get_entities_with_components('position', 'movement')
        
        for entity_id in entities:
            self._update_entity_movement(entity_id)
    
    def _invalidate_cache(self) -> None:
        """Invalidate the blocking entities cache"""
        self._cache_valid = False
    
    def _get_blocking_entities(self) -> set:
        """Get all entities that block movement (cached for performance)"""
        if not self._cache_valid:
            self._blocking_entities_cache = set()
            for entity_id in self.entity_manager.get_entities_with_components('position', 'collision'):
                collision = self.entity_manager.get_component(entity_id, 'collision')
                if collision and collision.blocks_movement:
                    self._blocking_entities_cache.add(entity_id)
            self._cache_valid = True
        return self._blocking_entities_cache
    
    def _update_entity_movement(self, entity_id: int) -> None:
        """Update movement for a single entity"""
        get = self.entity_manager.get_component  # Local caching for performance
        
        position = get(entity_id, 'position')
        movement = get(entity_id, 'movement')
        
        if not movement.is_moving or movement.target_x is None:
            return
        
        # Check if current target is reached and we have waypoints
        if movement.waypoint_queue and self._is_at_target(position, movement):
            self._advance_to_next_waypoint(entity_id, position, movement)
            return
        
        # Get collision radius for this entity
        collision = self.entity_manager.get_component(entity_id, 'collision')
        entity_radius = collision.radius if collision else 24.0
        
        # Use NumPy for deterministic calculations
        current = np.array([position.x, position.y], dtype=np.float32)
        target = np.array([movement.target_x, movement.target_y], dtype=np.float32)
        
        # Calculate direction and distance
        direction = target - current
        distance = np.linalg.norm(direction)
        
        # Check if reached target
        if distance < 1.0:
            self._handle_target_reached(entity_id, position, movement)
            return
        
        # Normalize direction
        direction = direction / distance
        
        # Calculate move distance this tick
        move_distance = movement.move_speed * self.dt
        
        if move_distance >= distance:
            # Will reach target this tick
            new_pos = np.array([movement.target_x, movement.target_y], dtype=np.float32)
        else:
            # Move toward target (linear interpolation)
            new_pos = current + direction * move_distance
        
        # Check for body blocking collision
        collision_result = self._check_body_blocking(entity_id, position, new_pos, entity_radius)
        
        if collision_result['blocked']:
            # Try to find alternative path around the blocker
            alt_pos = self._find_around_obstacle(entity_id, position, new_pos, entity_radius, 
                                                  collision_result['blocker_id'], direction, move_distance)
            if alt_pos is not None:
                # Found a way around - move there
                position.x = float(alt_pos[0])
                position.y = float(alt_pos[1])
                position.changed = True
            else:
                # No alternative found - stop
                self._stop_movement(entity_id, movement)
        else:
            # Move to new position
            position.x = float(new_pos[0])
            position.y = float(new_pos[1])
            position.changed = True
            
            # Check if reached target
            if move_distance >= distance:
                self._handle_target_reached(entity_id, position, movement)
    
    def _is_at_target(self, position: PositionComponent, movement: MovementComponent) -> bool:
        """Check if entity is at the current movement target"""
        dx = position.x - movement.target_x
        dy = position.y - movement.target_y
        return (dx * dx + dy * dy) < 1.0  # 1 unit tolerance
    
    def _advance_to_next_waypoint(self, entity_id: int, position: PositionComponent, 
                                   movement: MovementComponent) -> None:
        """Advance to the next waypoint in the queue"""
        if not movement.waypoint_queue:
            return
        
        # Remove the waypoint we just reached
        movement.waypoint_queue.pop(0)
        
        if movement.waypoint_queue:
            # Move to next waypoint
            next_wp = movement.waypoint_queue[0]
            movement.target_x = next_wp[0]
            movement.target_y = next_wp[1]
        elif movement.final_target_x is not None:
            # All waypoints done, move to final target
            movement.target_x = movement.final_target_x
            movement.target_y = movement.final_target_y
            movement.final_target_x = None
            movement.final_target_y = None
            movement.waypoint_queue = []
        else:
            # No more targets
            self._stop_movement(entity_id, movement)
    
    def _handle_target_reached(self, entity_id: int, position: PositionComponent, 
                                movement: MovementComponent) -> None:
        """Handle when an entity reaches its movement target"""
        position.x = movement.target_x
        position.y = movement.target_y
        
        # Check if we need to advance to next waypoint
        if movement.waypoint_queue:
            self._advance_to_next_waypoint(entity_id, position, movement)
        elif movement.final_target_x is not None:
            # All waypoints done, move to final target
            movement.target_x = movement.final_target_x
            movement.target_y = movement.final_target_y
            movement.final_target_x = None
            movement.final_target_y = None
        else:
            # Movement complete
            self._stop_movement(entity_id, movement)
    
    def _stop_movement(self, entity_id: int, movement: MovementComponent) -> None:
        """Stop entity movement and clear all targets"""
        movement.is_moving = False
        movement.target_x = None
        movement.target_y = None
        movement.final_target_x = None
        movement.final_target_y = None
        movement.waypoint_queue = []
        movement.current_stair_id = None
        movement.on_stair = False
    
    def _find_around_obstacle(self, entity_id: int, current_pos: PositionComponent, 
                               target_pos: np.ndarray, entity_radius: float, blocker_id: int,
                               original_direction: np.ndarray, move_distance: np.ndarray) -> np.ndarray:
        """
        Find an alternative path around a blocking entity.
        Tries multiple directions to slide around the obstacle.
        Returns the new position or None if no valid path found.
        """
        get = self.entity_manager.get_component  # Local caching for performance
        
        # Get blocker position and radius
        blocker_collision = get(blocker_id, 'collision')
        blocker_pos = get(blocker_id, 'position')
        
        if not blocker_collision or not blocker_pos:
            return None
        
        blocker_radius = blocker_collision.radius
        blocker_center = np.array([blocker_pos.x, blocker_pos.y], dtype=np.float32)
        
        combined_radius = entity_radius + blocker_radius
        
        # Calculate direction from blocker to target
        to_target = target_pos - blocker_center
        to_target_dist = np.linalg.norm(to_target)
        if to_target_dist > 0:
            to_target = to_target / to_target_dist
        
        # Direction from blocker to current position
        from_blocker = np.array([current_pos.x, current_pos.y], dtype=np.float32) - blocker_center
        from_blocker_dist = np.linalg.norm(from_blocker)
        if from_blocker_dist > 0:
            from_blocker = from_blocker / from_blocker_dist
        
        # Try sliding around the blocker on both sides
        # Find perpendicular directions
        perp1 = np.array([-from_blocker[1], from_blocker[0]])  # 90 degrees
        perp2 = np.array([from_blocker[1], -from_blocker[0]])  # -90 degrees
        
        # Blend direction: mostly toward target, slightly around obstacle
        # Try 8 different directions around the obstacle
        test_directions = []
        
        # Calculate arc of directions that go around the blocker
        for angle_frac in np.linspace(-1.0, 1.0, 9):  # -1 to 1 represents the arc
            # Interpolate between from_blocker direction and around direction
            if angle_frac < 0:
                # Go the "left" way around (via perp1)
                test_dir = from_blocker * abs(angle_frac) + perp1 * (1 - abs(angle_frac))
            else:
                # Go the "right" way around (via perp2)
                test_dir = from_blocker * abs(angle_frac) + perp2 * (1 - abs(angle_frac))
            
            test_dir = test_dir / np.linalg.norm(test_dir) if np.linalg.norm(test_dir) > 0 else from_blocker
            test_directions.append(test_dir)
        
        # Also try the original direction (in case blocker moved)
        test_directions.append(original_direction)
        
        best_pos = None
        best_score = float('-inf')
        
        for test_dir in test_directions:
            # Proposed new position
            proposed_pos = np.array([current_pos.x, current_pos.y], dtype=np.float32) + test_dir * move_distance
            
            # Check if this position is valid (not colliding with anything)
            if self._is_position_valid(entity_id, proposed_pos, entity_radius):
                # Score by how close it gets to the actual target
                to_final_target = np.linalg.norm(target_pos - proposed_pos)
                score = -to_final_target  # Lower distance is better
                
                if score > best_score:
                    best_score = score
                    best_pos = proposed_pos
        
        return best_pos
    
    def _is_position_valid(self, entity_id: int, pos: np.ndarray, entity_radius: float) -> bool:
        """Check if a position is valid (not colliding with any blocking entity)"""
        # Use spatial hash for efficient lookup if available
        
        # Determine search radius based on entity radius
        search_radius = entity_radius + 100  # Max collision radius + buffer
        
        # Get potential nearby entities using spatial hash
        if self.spatial_hash is not None:
            nearby_entities = self.spatial_hash.query_radius(pos[0], pos[1], search_radius)
        else:
            # Fallback to cached blocking entities list
            nearby_entities = self._get_blocking_entities()
        
        for other_id in nearby_entities:
            if other_id == entity_id:
                continue
            
            other_collision = self.entity_manager.get_component(other_id, 'collision')
            if not other_collision or not other_collision.blocks_movement:
                continue
            
            other_pos = self.entity_manager.get_component(other_id, 'position')
            if not other_pos:
                continue
            
            other_radius = other_collision.radius
            combined_radius = entity_radius + other_radius
            
            dx = pos[0] - other_pos.x
            dy = pos[1] - other_pos.y
            distance = np.sqrt(dx * dx + dy * dy)
            
            if distance < combined_radius:
                return False
        
        return True
    
    def _check_body_blocking(self, entity_id: int, current_pos: PositionComponent, 
                              target_pos: np.ndarray, entity_radius: float) -> dict:
        """
        Check if movement would cause collision with a blocking entity.
        Returns {'blocked': bool, 'blocker_id': int or None}
        """
        # Use spatial hash for efficient lookup if available
        
        # Determine search radius based on entity radius
        search_radius = entity_radius + 100  # Max collision radius + buffer
        
        # Get potential nearby entities using spatial hash
        if self.spatial_hash is not None:
            nearby_entities = self.spatial_hash.query_radius(target_pos[0], target_pos[1], search_radius)
        else:
            # Fallback to cached blocking entities list
            nearby_entities = self._get_blocking_entities()
        
        for other_id in nearby_entities:
            if other_id == entity_id:
                continue
            
            # Get collision component of other entity
            other_collision = self.entity_manager.get_component(other_id, 'collision')
            if not other_collision or not other_collision.blocks_movement:
                continue
            
            # Get position of other entity
            other_pos = self.entity_manager.get_component(other_id, 'position')
            if not other_pos:
                continue
            
            # Check if target position would overlap with other entity
            other_radius = other_collision.radius
            combined_radius = entity_radius + other_radius
            
            # Distance from target position to other entity
            dx = target_pos[0] - other_pos.x
            dy = target_pos[1] - other_pos.y
            distance = np.sqrt(dx * dx + dy * dy)
            
            if distance < combined_radius:
                # Collision detected - check if we're already overlapping
                # (allow movement if already overlapping, just can't move closer)
                current_dx = current_pos.x - other_pos.x
                current_dy = current_pos.y - other_pos.y
                current_distance = np.sqrt(current_dx * current_dx + current_dy * current_dy)
                
                if current_distance < combined_radius:
                    # Already overlapping - allow movement away but not closer
                    move_dx = target_pos[0] - current_pos.x
                    move_dy = target_pos[1] - current_pos.y
                    dot_product = move_dx * (other_pos.x - current_pos.x) + move_dy * (other_pos.y - current_pos.y)
                    if dot_product > 0:
                        # Moving toward the blocking entity
                        return {'blocked': True, 'blocker_id': other_id}
                else:
                    # Not already overlapping - collision would occur
                    return {'blocked': True, 'blocker_id': other_id}
        
        return {'blocked': False, 'blocker_id': None}
    
    def set_move_target(self, entity_id: int, target_x: float, target_y: float) -> bool:
        """
        Set movement target for an entity.
        Uses stair waypoints if direct movement is not possible.
        """
        movement = self.entity_manager.get_component(entity_id, 'movement')
        position = self.entity_manager.get_component(entity_id, 'position')
        
        if not movement or not position:
            return False
        
        # NEW: Check if already moving to this exact target (Fix 3)
        if movement.is_moving:
            if (movement.final_target_x == target_x and movement.final_target_y == target_y) or \
               (movement.target_x == target_x and movement.target_y == target_y):
                return True  # Already moving there, don't recalculate
        
        # Get current and target positions as Vec2
        current_pos = Vec2(position.x, position.y)
        target_pos = Vec2(target_x, target_y)
        
        # Check if we have a stair registry
        if self.stair_registry is None:
            # No stair registry - use direct movement
            movement.target_x = float(target_x)
            movement.target_y = float(target_y)
            movement.is_moving = True
            movement.waypoint_queue = []
            movement.final_target_x = None
            movement.final_target_y = None
            return True
        
        # Check if direct movement is possible
        if self.stair_registry.can_move_directly(current_pos, target_pos):
            # Direct movement allowed
            movement.target_x = float(target_x)
            movement.target_y = float(target_y)
            movement.is_moving = True
            movement.waypoint_queue = []
            movement.final_target_x = None
            movement.final_target_y = None
            return True
        
        # Need stair waypoints - find optimal path
        waypoints = self.stair_registry.find_stair_waypoints(current_pos, target_pos)
        
        # Better path cost comparison (Fix 4)
        if waypoints and len(waypoints) > 1:
            # Calculate total path distance
            total_path_dist = 0
            for i in range(len(waypoints) - 1):
                total_path_dist += (waypoints[i+1] - waypoints[i]).length()
            
            direct_dist = (target_pos - current_pos).length()
            
            # Only reject if path is 3x longer (stairs ALWAYS require detour)
            if total_path_dist > direct_dist * 3.0:
                waypoints = None
        
        if waypoints and len(waypoints) > 1:
            # We have a path with waypoints - reset movement state atomically (Fix 2)
            movement.waypoint_queue.clear()
            movement.current_stair_id = None
            movement.on_stair = False
            
            movement.final_target_x = target_x
            movement.final_target_y = target_y
            
            # Skip the first waypoint (it's the current position or very close)
            movement.waypoint_queue = [(wp.x, wp.y) for wp in waypoints[1:-1]]
            
            # Set first target - use None for direct targets when using stairs (Fix 4)
            if movement.waypoint_queue:
                first_wp = movement.waypoint_queue[0]
                movement.target_x = first_wp[0]
                movement.target_y = first_wp[1]
            else:
                movement.target_x = target_x
                movement.target_y = target_y
            
            movement.is_moving = True
            return True
        else:
            # No path found
            movement.is_moving = False
            movement.target_x = None
            movement.target_y = None
            return False
    
    def stop_movement(self, entity_id: int) -> bool:
        """Stop entity movement"""
        movement = self.entity_manager.get_component(entity_id, 'movement')
        if not movement:
            return False
        
        movement.is_moving = False
        movement.target_x = None
        movement.target_y = None
        movement.final_target_x = None
        movement.final_target_y = None
        movement.waypoint_queue = []
        movement.current_stair_id = None
        movement.on_stair = False
        movement.path_cache = None
        movement.path_cache_target = None
        return True
    
    def find_path(self, entity_id: int, start_x: float, start_y: float, goal_x: float, goal_y: float) -> Optional[List[Tuple[float, float]]]:
        """
        Find path from start to goal using elevation-aware A* with stair routing (FIX 4)
        Returns list of waypoints or None if no path found.
        """
        movement = self.entity_manager.get_component(entity_id, 'movement')
        if not movement:
            return None
        
        # Check path cache first
        if movement.path_cache and movement.path_cache_target == (goal_x, goal_y):
            if movement.path_recalc_cooldown > 0:
                return movement.path_cache
        
        # Get elevations
        from_elev = self.game_model.get_elevation_at_position(start_x, start_y)
        to_elev = self.game_model.get_elevation_at_position(goal_x, goal_y)
        
        path = None
        
        # Handle elevation changes with stairs (FIX 4)
        if from_elev != to_elev:
            stair_waypoint = self._find_nearest_stair(start_x, start_y, from_elev, to_elev)
            if stair_waypoint:
                # Path: start -> stair -> goal
                path1 = self._astar(start_x, start_y, stair_waypoint[0], stair_waypoint[1])
                path2 = self._astar(stair_waypoint[0], stair_waypoint[1], goal_x, goal_y)
                if path1 and path2:
                    path = path1[:-1] + path2
        
        # Fallback to direct A* if no stair path
        if not path:
            path = self._astar(start_x, start_y, goal_x, goal_y)
        
        # Cache the result
        if path:
            movement.path_cache = path
            movement.path_cache_target = (goal_x, goal_y)
            movement.path_recalc_cooldown = 0.5
        
        return path
    
    def _astar(self, start_x: float, start_y: float, goal_x: float, goal_y: float) -> Optional[List[Tuple[float, float]]]:
        """
        A* pathfinding with elevation-aware heuristic (FIX 5)
        Validates elevation transitions (FIX 9)
        """
        import heapq
        
        grid_size = 50  # Grid-based pathfinding
        start_node = (int(start_x // grid_size), int(start_y // grid_size))
        goal_node = (int(goal_x // grid_size), int(goal_y // grid_size))
        
        if start_node == goal_node:
            return [(start_x, start_y), (goal_x, goal_y)]
        
        # Priority queue: (f_score, node)
        frontier = [(0, start_node)]
        came_from = {start_node: None}
        g_score = {start_node: 0}
        
        while frontier:
            _, current = heapq.heappop(frontier)
            
            if current == goal_node:
                # Reconstruct path
                path = [(start_x, start_y)]
                node = goal_node
                while node != start_node:
                    path.append((node[0] * grid_size + grid_size/2, node[1] * grid_size + grid_size/2))
                    node = came_from[node]
                path.append((goal_x, goal_y))
                return path
            
            # Check neighbors (8-directional)
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                next_node = (current[0] + dx, current[1] + dy)
                next_x = next_node[0] * grid_size + grid_size/2
                next_y = next_node[1] * grid_size + grid_size/2
                
                # Validate elevation transition (FIX 9)
                current_elev = self.game_model.get_elevation_at_position(
                    current[0] * grid_size, current[1] * grid_size
                )
                next_elev = self.game_model.get_elevation_at_position(next_x, next_y)
                
                if current_elev != next_elev:
                    # Only allow transition if on stair
                    if not self.game_model.stair_geometry.is_on_stair(
                        current[0] * grid_size, current[1] * grid_size
                    ):
                        continue  # Skip this neighbor
                
                # Calculate costs
                move_cost = 1.0 if dx == 0 or dy == 0 else 1.414  # Diagonal is longer
                tentative_g = g_score[current] + move_cost
                
                if next_node not in g_score or tentative_g < g_score[next_node]:
                    # Elevation-aware heuristic (FIX 5)
                    h = abs(next_node[0] - goal_node[0]) + abs(next_node[1] - goal_node[1])
                    if current_elev != next_elev:
                        h += 1000  # Penalty for elevation mismatch
                    
                    came_from[next_node] = current
                    g_score[next_node] = tentative_g
                    f_score = tentative_g + h
                    heapq.heappush(frontier, (f_score, next_node))
        
        return None  # No path found
    
    def _find_nearest_stair(self, x: float, y: float, from_elev: float, to_elev: float) -> Optional[Tuple[float, float]]:
        """Find nearest stair connecting elevations (FIX 4)"""
        stairs = self.game_model.stair_geometry.get_stair_polygons_dict()
        if not stairs:
            return None
        
        min_dist = float('inf')
        nearest = None
        
        for stair_id, stair_data in stairs.items():
            if stair_data.get('from_elevation') == from_elev and stair_data.get('to_elevation') == to_elev:
                # Use stair center as waypoint
                center = stair_data.get('center', 
                    stair_data['waypoints'][0] if stair_data.get('waypoints') else None)
                if center:
                    dist = ((x - center[0])**2 + (y - center[1])**2)**0.5
                    if dist < min_dist:
                        min_dist = dist
                        nearest = center
        
        return nearest
