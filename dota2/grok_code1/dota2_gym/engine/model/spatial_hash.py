# engine/model/spatial_hash.py
import numpy as np
from typing import List, Dict, Set, Tuple
from .ecs.entity import Entity


class SpatialHash:
    """
    Fast O(1) spatial queries using grid hashing.
    Critical for vision, collision, projectile targeting.
    """
    def __init__(self, cell_size: float = 800.0):
        self.cell_size = cell_size
        self.cells: Dict[Tuple[int, int], Set[Entity]] = {}

    def _get_cell(self, x: float, y: float) -> Tuple[int, int]:
        return (int(x // self.cell_size), int(y // self.cell_size))

    def insert(self, entity: Entity):
        pos_comp = entity.get_component("position")
        if not pos_comp:
            return
        pos = pos_comp.value
        cell = self._get_cell(pos[0], pos[1])
        if cell not in self.cells:
            self.cells[cell] = set()
        self.cells[cell].add(entity)

    def clear(self):
        self.cells.clear()

    def query_radius(self, center: np.ndarray, radius: float) -> List[Entity]:
        """Return all entities within radius (inclusive)"""
        result: Set[Entity] = set()
        cx, cy = center[0], center[1]
        cell_min_x = int((cx - radius) // self.cell_size)
        cell_min_y = int((cy - radius) // self.cell_size)
        cell_max_x = int((cx + radius) // self.cell_size) + 1
        cell_max_y = int((cy + radius) // self.cell_size) + 1

        for ix in range(cell_min_x, cell_max_x):
            for iy in range(cell_min_y, cell_max_y):
                cell = (ix, iy)
                if cell in self.cells:
                    for ent in self.cells[cell]:
                        pos_comp = ent.get_component("position")
                        if pos_comp:
                            dist = np.linalg.norm(pos_comp.value - center)
                            if dist <= radius + 1e-3:
                                result.add(ent)
        return list(result)

    def query_rectangle(self, min_pos: np.ndarray, max_pos: np.ndarray) -> List[Entity]:
        # Optional helper – not used heavily yet
        pass