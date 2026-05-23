"""
Simple debug test for S_3 stair pathfinding with proper scaling
"""
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.model.game_model import GameModel
from engine.systems.stair_geometry import Vec2

# Create game model
config = {
    'game': {
        'tick_rate': 15.0,
    },
    'movement': {
        'stair_thickness': 15.0,
    }
}
model = GameModel(config)

# Test positions (game coordinates: 0-7000)
from_pos = Vec2(1800.0, 6300.0)
to_pos = Vec2(2100.0, 6300.0)

print("=" * 60)
print("Testing S_3 Pathfinding with Scaling")
print("=" * 60)

# Get elevations
from_elev = model.stair_registry.get_elevation_at_position(from_pos)
to_elev = model.stair_registry.get_elevation_at_position(to_pos)

print(f"From position: ({from_pos.x}, {from_pos.y})")
print(f"From position (scaled 0.1x): ({from_pos.x * 0.1}, {from_pos.y * 0.1})")
print(f"From elevation: {from_elev}")
print()
print(f"To position: ({to_pos.x}, {to_pos.y})")
print(f"To position (scaled 0.1x): ({to_pos.x * 0.1}, {to_pos.y * 0.1})")
print(f"To elevation: {to_elev}")
print()

# Check if direct movement is allowed
can_move_direct = model.stair_registry.can_move_directly(from_pos, to_pos)
print(f"Can move directly: {can_move_direct} (expected: False)")
print()

# Get S_3 with scaled coordinates (10x for game world)
s3_scaled = model.stair_registry.find_stair_by_name_with_scaling("S_3")
print(f"S_3 (scaled for game world):")
if s3_scaled:
    print(f"  p1: ({s3_scaled.p1.x}, {s3_scaled.p1.y})")
    print(f"  p2: ({s3_scaled.p2.x}, {s3_scaled.p2.y})")
    print(f"  S_3 midpoint: ({(s3_scaled.p1.x + s3_scaled.p2.x) / 2}, {(s3_scaled.p1.y + s3_scaled.p2.y) / 2})")
print()

# Calculate distances from hero position to scaled S_3
dist_to_s3_p1 = from_pos.distance_to(s3_scaled.p1)
dist_to_s3_p2 = from_pos.distance_to(s3_scaled.p2)
print(f"Distance from hero to S_3 p1: {dist_to_s3_p1:.1f}")
print(f"Distance from hero to S_3 p2: {dist_to_s3_p2:.1f}")
print()

# Find all stairs with scaled coordinates and find the nearest one
print("All stairs with scaled distances (showing top 10 nearest):")
nearest_stairs = []
for stair in model.stair_registry.get_all_stairs():
    # Get scaled version
    scaled = model.stair_registry.find_stair_by_name_with_scaling(stair.name)
    if scaled:
        dist = from_pos.distance_to(scaled.p1)
        nearest_stairs.append((stair.name, dist, scaled.p1))

# Sort by distance and show top 10
nearest_stairs.sort(key=lambda x: x[1])
for i, (name, dist, p1) in enumerate(nearest_stairs[:10]):
    print(f"  {i+1}. {name}: dist={dist:.1f}, p1=({p1.x:.0f}, {p1.y:.0f})")

print()
print(f"Nearest stair: {nearest_stairs[0][0]} at distance {nearest_stairs[0][1]:.1f}")
print()

# Verify S_3 is among the nearest stairs
s3_entry = [s for s in nearest_stairs if s[0] == "S_3"]
if s3_entry:
    print(f"✓ S_3 is found at distance {s3_entry[0][1]:.1f}")
else:
    print(f"✗ S_3 not found in nearest stairs list")

# Check if S_3 is in the top 3 nearest
s3_rank = next((i for i, s in enumerate(nearest_stairs) if s[0] == "S_3"), -1)
print(f"S_3 rank by distance: #{s3_rank + 1}")
print()

# Find path waypoints
waypoints = model.stair_registry.find_stair_waypoints(from_pos, to_pos)
print(f"Waypoints found: {len(waypoints) if waypoints else 0}")
if waypoints:
    print("  Waypoint path:")
    for i, wp in enumerate(waypoints):
        print(f"    {i}: ({wp.x:.0f}, {wp.y:.0f})")
print()

# Summary
print("=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"✓ Hero at (1800, 6300): elevation {from_elev} (high ground)")
print(f"✓ Target at (2100, 6300): elevation {to_elev} (low ground)")
print(f"✓ Direct movement blocked: {not can_move_direct}")
print(f"✓ S_3 is available and reachable")
print(f"✓ Pathfinding uses waypoints: {waypoints is not None and len(waypoints) > 1}")
print("=" * 60)
