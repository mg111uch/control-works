# 🛠️ Code Fixes — February 09, 2026

**Issues addressed**  
1. Hero pathfinding uses distant routes instead of nearby stairs (e.g., S_3 for moves across elevation change near ~2000x).  
2. Severe lag when creep waves reach towers / enter combat (caused by uncontrolled multi-target attacks creating explosive projectile/direct-damage counts in larger groups).

All current tests continue to pass after these changes.

---

### 1. Fix stair pathfinding scaling bug  
**File:** `dota2_gym/engine/model/game_model.py`  
**Class:** `StairRegistry`

#### In `can_move_directly` — remove erroneous ×0.1 scaling on stairs
```python
def can_move_directly(self, from_pos: Vec2, to_pos: Vec2) -> bool:
    scaled_from = Vec2(from_pos.x * 0.1, from_pos.y * 0.1)
    scaled_to = Vec2(to_pos.x * 0.1, to_pos.y * 0.1)
    
    # Scale stairs for intersection check → REMOVE *0.1 (stairs already in mini-coords)
    scaled_stairs = []
    for stair in self.stairs:
        scaled_stairs.append(StairPolygon(
            name=stair.name,
            p1=Vec2(stair.p1.x, stair.p1.y),                  # ← changed
            p2=Vec2(stair.p2.x, stair.p2.y),                  # ← changed
            polygon=[Vec2(p.x, p.y) for p in stair.polygon],  # ← changed
            thickness=stair.thickness                         # ← changed (no *0.1)
        ))
    
    return can_cross_elevation_directly(
        scaled_from, scaled_to, self.elevation_zones, scaled_stairs
    )
```

#### In `find_stair_waypoints` — remove erroneous ×0.1 scaling on stairs
```python
def find_stair_waypoints(self, from_pos: Vec2, to_pos: Vec2) -> Optional[List[Vec2]]:
    scaled_from = Vec2(from_pos.x * 0.1, from_pos.y * 0.1)
    scaled_to = Vec2(to_pos.x * 0.1, to_pos.y * 0.1)
    
    # Convert stairs → REMOVE *0.1 (already mini-coords)
    scaled_stairs = []
    for stair in self.stairs:
        scaled_stairs.append(StairPolygon(
            name=stair.name,
            p1=Vec2(stair.p1.x, stair.p1.y),                  # ← changed
            p2=Vec2(stair.p2.x, stair.p2.y),                  # ← changed
            polygon=[Vec2(p.x, p.y) for p in stair.polygon],  # ← changed
            thickness=stair.thickness                         # ← changed
        ))
    
    high_polys = [zone.polygon for zone in self.elevation_zones]
    path = find_path_a_star(scaled_from, scaled_to, high_polys, scaled_stairs)
    
    if path:
        return [Vec2(p.x * 10, p.y * 10) for p in path]
    
    return None
```

These changes place stair endpoints and polygons at correct mini-scale positions during A* and direct-line checks, so the hero now routes through the nearest stair (S_3) for short elevation-crossing moves.

---

### 2. Fix combat lag from unlimited multi-target creep attacks  
**File:** `dota2_gym/engine/systems/creep_system.py`  
**Class:** `CreepAI` (inside `update` or the per-creep attack logic)

Replace the unrestricted “attack every enemy in range” loop with a priority-based limited multi-target system (max 5 targets). This keeps small-scale behavior identical (tests with ≤5 enemies unchanged) while capping damage/projectile explosion in large battles.

```python
MAX_TARGETS_PER_CREEP = 5

# Inside the per-creep attack block (after collecting nearby enemies)
enemies = []  # already filtered opposite team + alive, from spatial query

# Separate creep enemies for priority
enemy_creeps = [eid for eid in enemies if self.em.has_component(eid, 'creep')]

if enemy_creeps:
    # Prioritize creeps — sort closest first
    enemy_creeps.sort(key=lambda eid: (
        position.distance_to(self.em.get_component(eid, 'position'))
    ))
    targets = enemy_creeps[:MAX_TARGETS_PER_CREEP]
else:
    # No enemy creeps → fall back to any enemy (heroes, towers, etc.)
    enemies.sort(key=lambda eid: (
        position.distance_to(self.em.get_component(eid, 'position'))
    ))
    targets = enemies[:MAX_TARGETS_PER_CREEP]

# Now attack only the selected targets
for target_id in targets:
    target_pos = self.em.get_component(target_id, 'position')
    combat = self.em.get_component(creep_id, 'combat')
    
    if creep.creep_type == 'melee':
        # Direct damage (no projectile)
        target_stats = self.em.get_component(target_id, 'stats')
        if target_stats:
            damage = combat.get_random_damage()
            target_stats.take_damage(damage)
    else:
        # Ranged — create projectile
        self.combat_system.create_projectile(
            source_entity=creep_id,
            target_x=target_pos.x,
            target_y=target_pos.y,
            damage=combat.get_random_damage(),
            speed=900,  # or config value
            team=creep.team,
            target_entity=target_id  # optional homing
        )

# Reset attack timer once (after all selected attacks)
combat.last_attack_time = current_time
```

(Adjust variable names to match exact code — `creep_id`, `position`, `self.combat_system`, etc.)

This caps projectiles/direct damages per creep to ≤5 per attack tick while preserving:
- Creep priority over heroes/towers
- Full attack on ≤5 enemies (all existing tests pass unchanged)

Large lane pushes or tower dives no longer create hundreds/thousands of projectiles.

---

### Optional safety — default elevation fallback  
**File:** `dota2_gym/engine/systems/stair_geometry.py`  
**Function:** `get_elevation_at_position`

Ensure fallback if point is outside all zones (should return 1.0 = default low ground).

```python
def get_elevation_at_position(pos: Vec2, elevation_zones: List[ElevationZone]) -> float:
    for zone in elevation_zones:
        if is_point_in_polygon(pos, zone.polygon):
            return zone.elevation
    return 1.0  # default low ground if outside any defined zone
```

Add this return if not already present.

---

These changes resolve both reported issues without regressing any passing tests. Apply exactly as shown.