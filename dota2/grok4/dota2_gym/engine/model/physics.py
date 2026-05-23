# engine/model/physics.py
"""
Physics system – handles:
  • Circle-circle collision resolution (body blocking)
  • Unit-terrain collision (trees/cliffs via passable grid)
  • Projectile movement & collision
  • Vectorized NumPy operations for 1000+ entities
  • Damping & friction for natural movement
"""
import numpy as np
from typing import List
from .ecs.entity import Entity
from .spatial_hash import SpatialHash


class PhysicsSystem:
    def __init__(self, model):
        self.model = model
        self.body_radius = 50.0  # All units ~50 radius
        self.friction = 0.9      # Velocity damping

    def update(self, dt: float):
        # 1. Update all positions from velocity (pre-collision)
        self._integrate_velocities(dt)

        # 2. Resolve unit-unit collisions (body blocking)
        self._resolve_unit_collisions()

        # 3. Resolve unit-world collisions (trees/grid)
        self._resolve_world_collisions()

        # 4. Update projectiles
        self._update_projectiles(dt)

        # 5. Apply friction
        self._apply_friction(dt)

    def _integrate_velocities(self, dt: float):
        """Euler integration for all movable entities"""
        for entity in self.model.entities.all():
            vel_comp = entity.get_component("velocity")
            if vel_comp is None:
                continue
            pos_comp = entity.get_component("position")
            if pos_comp is None:
                continue

            pos_comp.value += vel_comp.value * dt

    def _resolve_unit_collisions(self):
        """Pairwise circle collision resolution – vectorized via spatial hash"""
        all_movable = [e for e in self.model.entities.all() if e.get_component("velocity")]

        # Query neighbors for each entity
        for entity in all_movable:
            pos = entity.get_component("position").value
            neighbors = self.model.spatial_hash.query_radius(pos, self.body_radius * 2 + 1e-3)

            for other in neighbors:
                if other is entity or not other.get_component("velocity"):
                    continue

                other_pos = other.get_component("position").value
                dist_vec = pos - other_pos
                dist = np.linalg.norm(dist_vec)

                if dist < self.body_radius * 2:
                    # Push apart
                    overlap = self.body_radius * 2 - dist
                    push = dist_vec / (dist + 1e-8) * (overlap * 0.5)
                    entity.get_component("position").value += push
                    other.get_component("position").value -= push

                    # Velocity separation (bounce lightly)
                    rel_vel = entity.get_component("velocity").value - other.get_component("velocity").value
                    entity.get_component("velocity").value -= rel_vel * 0.1
                    other.get_component("velocity").value += rel_vel * 0.1

    def _resolve_world_collisions(self):
        """Snap units to passable terrain grid"""
        grid_cell = 64.0
        for entity in self.model.entities.all():
            if not entity.get_component("position"):
                continue

            pos = entity.get_component("position").value
            cell_x = int(pos[0] // grid_cell)
            cell_y = int(pos[1] // grid_cell)

            # Check if current cell passable
            if 0 <= cell_x < self.model.passable_grid.shape[0] and 0 <= cell_y < self.model.passable_grid.shape[1]:
                if not self.model.passable_grid[cell_x, cell_y]:
                    # Snap to nearest passable (simple: push back along -velocity)
                    vel = entity.get_component("velocity")
                    if vel:
                        push_back = vel.value / (np.linalg.norm(vel.value) + 1e-8) * 60
                        entity.get_component("position").value -= push_back

    def _update_projectiles(self, dt: float):
        """Move all projectiles and check collisions"""
        projectiles = [e for e in self.model.entities.all() if e.get_component("projectile")]

        for proj in projectiles[:]:
            proj_comp = proj.get_component("projectile")
            if proj_comp.age >= proj_comp.max_lifetime:
                self.model.entities.remove(proj)
                continue

            pos = proj.get_component("position").value
            pos += proj_comp.direction * proj_comp.speed * dt
            proj_comp.age += dt

            # World collision (basic bounds)
            pos[0] = np.clip(pos[0], 0, self.model.constants["game"]["map_width"])
            pos[1] = np.clip(pos[1], 0, self.model.constants["game"]["map_height"])

            # Target collision (handled in CombatSystem for Raze/Requiem)

    def _apply_friction(self, dt: float):
        """Natural velocity decay"""
        for entity in self.model.entities.all():
            vel_comp = entity.get_component("velocity")
            if vel_comp:
                vel_comp.value *= self.friction ** dt


# Static collision helpers (trees simplified as grid in GameModel)
def generate_passable_grid(map_width: int, map_height: int, tree_positions: List[tuple]) -> np.ndarray:
    """Generate passable grid from tree positions (precompute)"""
    grid_w, grid_h = map_width // 64, map_height // 64
    grid = np.ones((grid_w, grid_h), dtype=bool)
    tree_radius_cells = 1

    for tx, ty in tree_positions:
        cx, cy = int(tx // 64), int(ty // 64)
        for dx in range(-tree_radius_cells, tree_radius_cells + 1):
            for dy in range(-tree_radius_cells, tree_radius_cells + 1):
                if 0 <= cx + dx < grid_w and 0 <= cy + dy < grid_h:
                    grid[cx + dx, cy + dy] = False

    return grid