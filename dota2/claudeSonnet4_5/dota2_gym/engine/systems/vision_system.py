import numpy as np

class VisionSystem:
    """Fog of War vision system using NumPy grid"""
    
    def __init__(self, map_width: int, map_height: int, grid_size: int = 64):
        self.map_width = map_width
        self.map_height = map_height
        self.grid_size = grid_size
        
        # Vision grid (0 = hidden, 1 = visible)
        self.grid_width = map_width // grid_size
        self.grid_height = map_height // grid_size
        self.vision_grid = np.zeros((self.grid_height, self.grid_width), dtype=np.float32)
    
    def clear_vision(self):
        """Clear vision grid"""
        self.vision_grid.fill(0)
    
    def update_vision(self, entity_manager):
        """Update vision for all entities with changed positions"""
        get = entity_manager.get_component
        
        # Clear vision grid
        self.vision_grid.fill(0)
        
        # Get all entities with position component
        positions = entity_manager.get_entities_with_component('position')
        
        for entity_id in positions:
            position = get(entity_id, 'position')
            if position and position.changed:
                # Add vision for this entity
                self.add_vision(position.x, position.y, 800)  # Default vision radius
                position.changed = False  # Reset changed flag
    
    def add_vision(self, x: float, y: float, radius: float):
        """Add vision circle at position"""
        grid_x = int(x / self.grid_size)
        grid_y = int(y / self.grid_size)
        grid_radius = int(radius / self.grid_size)
        
        # Add vision in radius
        for gy in range(max(0, grid_y - grid_radius), 
                       min(self.grid_height, grid_y + grid_radius + 1)):
            for gx in range(max(0, grid_x - grid_radius),
                           min(self.grid_width, grid_x + grid_radius + 1)):
                dx = gx - grid_x
                dy = gy - grid_y
                dist = np.sqrt(dx*dx + dy*dy)
                
                if dist <= grid_radius:
                    self.vision_grid[gy, gx] = 1
    
    def is_visible(self, x: float, y: float) -> bool:
        """Check if position is visible"""
        grid_x = int(x / self.grid_size)
        grid_y = int(y / self.grid_size)
        
        if 0 <= grid_x < self.grid_width and 0 <= grid_y < self.grid_height:
            return self.vision_grid[grid_y, grid_x] > 0
        return False
