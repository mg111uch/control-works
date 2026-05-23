# Staircase Waypoint Implementation - Enhanced

## Overview

Implemented staircase waypoint navigation for movable entities in a 3-tier elevation system. Entities can only cross elevation boundaries through staircase polygons. **Now with adaptive sampling, spatial indexing, and direction-aware stair selection.**

## 3-Tier Elevation System

### Elevation Levels
- **High Ground (elevation 2.0):** Areas defined by high ground polygons
  - Radiant_base_high_ground
  - Dire_base_high_ground
  - Bottom_right_high_ground
  - Top_left_high_ground

- **Middle Ground (elevation 1.0):** Default elevation for areas not bounded by any polygon

- **Low Ground (elevation 0.0):** River_low_ground polygon

## Implementation Details

### 1. Stair Geometry Module (`engine/systems/stair_geometry.py`)

**Classes:**
- `Vec2`: 2D vector class with arithmetic operations
- `ElevationZone`: Represents an area with specific elevation
- `StairPolygon`: Represents a stair with geometry and metadata

**Key Functions:**
- `generate_stair_polygon(p1, p2, thickness)`: Generates 4-point polygon for stair
- `is_point_in_polygon(point, polygon)`: Ray-casting algorithm for point-in-polygon check
- `can_cross_elevation_directly(from_pos, to_pos, zones, stairs, config)`: **Adaptive sampling** with dynamic sample count (20-100) based on path length
- `find_nearest_stair(point, stairs)`: Returns nearest stair using polygon distance
- `get_elevation_at_position(point, zones, default_elevation=1.0)`: Returns elevation at position

### 2. Stair Registry (`engine/model/game_model.py`)

**StairRegistry Class:**
- Loads stairs and elevation zones from `map_polygons.txt`
- `load_stairs_from_file(polygon_file)`: Parses 44 stairs and 5 elevation zones
- `find_nearest_stair(point)`: **Uses spatial indexing for O(1) average query**
- `find_optimal_stair(from_pos, to_pos)`: **NEW** - Direction-aware selection that minimizes total path length
- `can_move_directly(from_pos, to_pos)`: Checks if path crosses elevation boundaries with adaptive sampling
- `get_elevation_at_position(point)`: Returns elevation (2.0, 1.0, or 0.0)
- `_build_stair_spatial_index()`: **NEW** - Builds spatial hash for efficient stair queries
- `_get_nearby_cells(point, radius)`: **NEW** - Returns candidate stairs using spatial index

### 3. Movement System (`engine/systems/movement_system.py`)

**MovementComponent Extensions:**
- `target_x`, `target_y`: Current movement target
- `final_target_x`, `final_target_y`: Final destination when using stair waypoint
- `on_stair`: Boolean flag for stair state
- `current_stair_id`: ID of current stair

**Key Methods:**
- `set_move_target(entity_id, target_x, target_y)`:
  - Checks if direct movement is allowed via `can_move_directly()`
  - **If path crosses elevation boundaries, finds optimal stair (not just nearest)**
  - Sets stair midpoint as intermediate target
  - Stores final target for post-stair movement

- `_update_entity_movement(entity_id)`:
  - Moves entity toward current target
  - When close to stair, transitions to final target
  - **Updates `on_stair` state using spatial index for efficiency**

- `set_stair_transition_distance(distance)`: **NEW** - Configurable threshold for stair-to-target transition

### 4. Configuration (`config/game_config.yaml`)

```yaml
movement:
  movement_speed_base: 300
  stair_thickness: 15  # game units
  stair_transition_distance: 50.0  # configurable distance threshold
  min_path_samples: 20  # minimum samples for adaptive path validation
  max_path_samples: 100  # maximum samples for adaptive path validation
  samples_per_unit: 0.01  # adaptive sampling density
```

## Path Validation Algorithm

The enhanced `can_cross_elevation_directly()` function:

1. **Adaptive Sampling**: Calculates sample count based on path length
   - Minimum: 20 samples
   - Maximum: 100 samples
   - Formula: `max(20, min(100, path_length * 0.01))`

2. For each sample point along the path, checks elevation via `get_elevation_at_position()`

3. **Early Exit Optimization**: If any sample point has different elevation than start:
   - Returns False immediately (direct movement blocked)
   - Entity must use stair as waypoint

4. If all sample points have same elevation:
   - Returns True (direct movement allowed)

## Movement Flow (Enhanced)

```
Entity at High Ground (2.0)
        ↓
set_move_target() called with target in Middle Ground (1.0)
        ↓
can_cross_elevation_directly() with adaptive sampling returns False
        ↓
find_optimal_stair() - selects stair minimizing total path:
  - Distance from entity to stair
  - Distance from stair to final target
        ↓
Set target = stair midpoint, final_target = original target
        ↓
Update loop: Move toward stair midpoint
        ↓
Entity reaches stair → Switch target to final_target
        ↓
Entity moves to final destination
```

## Files Modified/Created

| File | Description |
|------|-------------|
| `engine/systems/stair_geometry.py` | Adaptive sampling algorithm (MODIFIED) |
| `engine/model/game_model.py` | Spatial indexing + find_optimal_stair (MODIFIED) |
| `engine/systems/movement_system.py` | Configurable thresholds + spatial queries (MODIFIED) |
| `engine/ecs/components.py` | MovementComponent fields (MODIFIED) |
| `config/game_config.yaml` | New movement parameters (MODIFIED) |
| `tests/test_stair_waypoints.py` | 23 unit tests (NEW) |
| `tests/test_stair_integration.py` | 5 integration tests for stair waypoint behavior (NEW) |

## Test Results

- **138 tests passed** (all test suites)
- Tests cover: Vec2 operations, stair polygon generation, point-in-polygon, nearest/optimal stair, elevation detection, adaptive sampling, spatial indexing, and stair waypoint integration

## Bug Fix (2026-01-28)

### Issue
Entities were not using staircase waypoints when moving between different elevations due to a bug in the `find_optimal_stair()` method in `engine/model/game_model.py`. The method was incorrectly calling `distance_point_to_polygon(stair.midpoint, to_pos)` where `to_pos` is a `Vec2` target position, but the function expects a polygon as the second parameter.

### Fix
Changed the distance calculation from polygon distance to Euclidean distance:
```python
# Before (buggy):
dist_from_stair = distance_point_to_polygon(stair.midpoint, to_pos)

# After (fixed):
dist_from_stair = (stair.midpoint - to_pos).length()
```

### Location
- File: `engine/model/game_model.py`
- Line: 226
- Method: `find_optimal_stair()`

### Verification
Integration test confirms entities now correctly use stair waypoints:
- Entity at (50, 50) with elevation 2.0 (high ground)
- Target at (150, 150) with elevation 1.0 (middle ground)
- Entity uses stair waypoint S_20 (midpoint at 130.0, 167.5)
- Final target is stored for post-stair movement

## Performance Optimizations

### 1. Spatial Indexing
- **Before**: O(n) iteration through all stairs every tick
- **After**: O(1) average case using spatial hash
- Stairs are indexed by their midpoint position into grid cells
- Query returns only nearby stairs within specified radius

### 2. Adaptive Sampling
- **Before**: Fixed 20 samples regardless of path length
- **After**: Dynamic sampling (20-100) proportional to path length
- Short paths: 20 samples (efficient)
- Long paths: Up to 100 samples (more thorough)

### 3. Direction-Aware Selection
- **Before**: Selected nearest stair (may not be optimal direction)
- **After**: Selects stair minimizing total path length
- Considers both approach and departure distances

## Limitations and Future Work

- No pathfinding around obstacles during stair traversal
- Could extend SpatialHash for dynamic stair queries during gameplay
- Future: Consider elevation difference when selecting optimal stair
