# engine/model/systems/vision_system.py
"""
VisionSystem – Fog of War implementation
Features:
  • 1800 unit circular vision radius per hero
  • NumPy vectorized grid rasterization (224x200 cells)
  • Updated every tick
  • No high/low ground (simple circle)
  • Visible entities query for RL obs
  • Black fog overlay in PygameView
  • Shared vision between allies (creeps/towers add minor vision)
"""

import numpy as np
from typing import List, Dict
from ..ecs.entity import Entity
from ..spatial_hash import SpatialHash


class VisionSystem:
    def __init__(self, model):
        self.model = model
        self.vision_radius = model.constants["game"]["vision_radius"]  # 1800
        self.grid_cell_size = 72.0  # 16000/224 ≈ 71.4
        self.grid_shape = (200, 224)  # height x width (14400/72=200, 16000/72=222)
        self.vision_grid_res = 32  # Sub-grid for circle rasterization

        # Precompute circle mask for vectorized vision
        self._precompute_circle_mask()

    def _precompute_circle_mask(self):
        """Generate circle kernel for fast rasterization"""
        r = self.vision_radius / self.grid_cell_size
        size = int(2 * r) + 1
        y, x = np.ogrid[-r:r+1, -r:r+1]
        mask = x**2 + y**2 <= r**2
        self.circle_mask = mask.astype(np.float32)

    def update(self, dt: float):
        """Compute fresh vision grids for both players"""
        heroes = [e for e in self.model.entities.all() if hasattr(e, "player_id")]

        for hero in heroes:
            player_id = hero.player_id
            pos = hero.get_component("position").value

            # Base hero vision
            grid = self._rasterize_vision_circle(pos)

            # Add minor vision from nearby friendly creeps/towers (200 radius)
            allies = self.model.spatial_hash.query_radius(pos, 2000)
            for ally in allies:
                if getattr(ally, "team", -1) == hero.team:
                    ally_pos = ally.get_component("position").value
                    ally_grid = self._rasterize_vision_circle(ally_pos, radius=300)
                    grid = np.maximum(grid, ally_grid)

            self.model.fog_of_war[player_id] = grid

    def _rasterize_vision_circle(self, center: np.ndarray, radius: float = None) -> np.ndarray:
        """Vectorized circle → grid projection"""
        if radius is None:
            radius = self.vision_radius

        grid_h, grid_w = self.grid_shape
        grid = np.zeros((grid_h, grid_w), dtype=np.float32)

        # Center cell
        cx = int(center[0] / self.grid_cell_size)
        cy = int(center[1] / self.grid_cell_size)

        # Offset for mask
        mask_r = self.circle_mask.shape[0] // 2
        sy = max(0, cy - mask_r)
        ey = min(grid_h, cy + mask_r + 1)
        sx = max(0, cx - mask_r)
        ex = min(grid_w, cx + mask_r + 1)

        if sx < ex and sy < ey:
            mask_slice_y = slice(max(0, sy - cy + mask_r), min(self.circle_mask.shape[0], ey - cy + mask_r))
            mask_slice_x = slice(max(0, sx - cx + mask_r), min(self.circle_mask.shape[1], ex - cx + mask_r))
            grid[sy:ey, sx:ex] = np.maximum(
                grid[sy:ey, sx:ex],
                self.circle_mask[mask_slice_y, mask_slice_x]
            )

        return grid

    def get_visible_entities(self, player_id: int, max_radius: float = None) -> List[Entity]:
        """Filter entities visible to player (for RL obs)"""
        if max_radius is None:
            max_radius = self.vision_radius * 1.5  # Extra buffer

        hero = next((e for e in self.model.entities.all() if getattr(e, "player_id", -1) == player_id), None)
        if not hero:
            return []

        pos = hero.get_component("position").value
        candidates = self.model.spatial_hash.query_radius(pos, max_radius)

        visible = []
        fog_grid = self.model.fog_of_war[player_id]
        cell_size = self.grid_cell_size

        for ent in candidates:
            if not ent.get_component("position"):
                continue
            ent_pos = ent.get_component("position").value

            # Check if in fog-revealed cell
            ex = int(ent_pos[0] / cell_size)
            ey = int(ent_pos[1] / cell_size)
            if 0 <= ex < fog_grid.shape[1] and 0 <= ey < fog_grid.shape[0]:
                if fog_grid[ey, ex] > 0.1:  # Visible threshold
                    visible.append(ent)

        return visible

    def is_position_visible(self, pos: np.ndarray, player_id: int) -> bool:
        """Quick cell check"""
        fog_grid = self.model.fog_of_war[player_id]
        cell_size = self.grid_cell_size
        ex = int(pos[0] / cell_size)
        ey = int(pos[1] / cell_size)
        return (0 <= ex < fog_grid.shape[1] and 0 <= ey < fog_grid.shape[0] and fog_grid[ey, ex] > 0.1)