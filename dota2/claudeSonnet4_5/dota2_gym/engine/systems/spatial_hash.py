"""Spatial hashing for efficient entity lookups"""
import numpy as np
from typing import Set, Tuple


class SpatialHash:
    """
    Spatial hash grid for efficient nearby entity queries.
    Divides world into cells for O(1) spatial lookups.
    """
    
    def __init__(self, cell_size: int = 500, map_width: int = 7200, map_height: int = 7200):
        self.cell_size = cell_size
        self.map_width = map_width
        self.map_height = map_height
        self.grid_width = int(np.ceil(map_width / cell_size))
        self.grid_height = int(np.ceil(map_height / cell_size))
        self.cells: dict = {}
    
    def clear(self) -> None:
        """Clear all cells"""
        self.cells = {}
    
    def _get_cell(self, x: float, y: float) -> Tuple[int, int]:
        """Get cell coordinates for a world position"""
        cx = max(0, min(self.grid_width - 1, int(x / self.cell_size)))
        cy = max(0, min(self.grid_height - 1, int(y / self.cell_size)))
        return (cx, cy)
    
    def insert(self, entity_id: int, x: float, y: float) -> None:
        """Insert an entity into the spatial hash"""
        cell = self._get_cell(x, y)
        if cell not in self.cells:
            self.cells[cell] = set()
        self.cells[cell].add(entity_id)
    
    def remove(self, entity_id: int) -> None:
        """Remove an entity from the spatial hash"""
        for cell in self.cells:
            if entity_id in self.cells[cell]:
                self.cells[cell].discard(entity_id)
    
    def remove_at_position(self, entity_id: int, x: float, y: float) -> None:
        """Remove entity from spatial hash at specific position (FIX 3)"""
        cell_x = int(x // self.cell_size)
        cell_y = int(y // self.cell_size)
        key = (cell_x, cell_y)
        if key in self.cells and entity_id in self.cells[key]:
            self.cells[key].discard(entity_id)
    
    def query_radius(self, x: float, y: float, radius: float) -> Set[int]:
        """Query all entities within a radius of a point"""
        results = set()
        
        # Calculate cell range to check
        min_cx = max(0, int((x - radius) / self.cell_size))
        max_cx = min(self.grid_width - 1, int((x + radius) / self.cell_size))
        min_cy = max(0, int((y - radius) / self.cell_size))
        max_cy = min(self.grid_height - 1, int((y + radius) / self.cell_size))
        
        # Check all cells in range
        for cx in range(min_cx, max_cx + 1):
            for cy in range(min_cy, max_cy + 1):
                cell = (cx, cy)
                if cell in self.cells:
                    results.update(self.cells[cell])
        
        return results
    
    def get_nearby_entities(self, entity_id: int, x: float, y: float, radius: float) -> Set[int]:
        """Get nearby entities excluding the querying entity"""
        results = self.query_radius(x, y, radius)
        results.discard(entity_id)
        return results