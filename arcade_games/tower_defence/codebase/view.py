"""
View Module
MVC View - Handles all rendering
"""

import constants


class GameView:
    """View class for rendering the game"""
    
    def __init__(self, screen, font, small_font):
        self.screen = screen
        self.font = font
        self.small_font = small_font
    
    def clear(self):
        """Clear the screen"""
        self.screen.fill(constants.WHITE)
    
    def draw_grid(self):
        """Draw the grid"""
        import pygame
        for x in range(0, constants.SCREEN_WIDTH, constants.CELL_SIZE):
            pygame.draw.line(self.screen, constants.GRAY, (x, 0), (x, constants.SCREEN_HEIGHT), 1)
        for y in range(0, constants.SCREEN_HEIGHT, constants.CELL_SIZE):
            pygame.draw.line(self.screen, constants.GRAY, (0, y), (constants.SCREEN_WIDTH, y), 1)
    
    def draw_path(self):
        """Draw the enemy path"""
        import pygame
        pygame.draw.line(self.screen, constants.GRAY, (0, constants.PATH_Y), (constants.SCREEN_WIDTH, constants.PATH_Y), 5)
    
    def draw_score(self, score):
        """Draw the score"""
        text = self.font.render(f"Score: {score}", True, constants.BLACK)
        self.screen.blit(text, (10, 10))
    
    def draw_money(self, money):
        """Draw the money"""
        text = self.font.render(f"Money: ${money}", True, constants.BLACK)
        self.screen.blit(text, (10, 45))
    
    def draw_tower_selector(self, selected_type, money):
        """Draw tower selection UI"""
        y_offset = constants.SCREEN_HEIGHT - 60
        
        types = ['artillery', 'cannon', 'laser']
        for i, t in enumerate(types):
            config = constants.TOWER_TYPES[t]
            x = 10 + i * 120
            
            # Highlight selected tower
            if t == selected_type:
                import pygame
                pygame.draw.rect(self.screen, constants.YELLOW, (x - 5, y_offset - 5, 110, 55), 2)
            
            # Check if affordable
            color = constants.BLACK if money >= config['cost'] else constants.GRAY
            
            name = self.small_font.render(f"{config['name'][:8]}", True, color)
            cost = self.small_font.render(f"${config['cost']}", True, color)
            cooldown = self.small_font.render(f"CD: {config['cooldown']}s", True, color)
            
            self.screen.blit(name, (x, y_offset))
            self.screen.blit(cost, (x, y_offset + 18))
            self.screen.blit(cooldown, (x, y_offset + 36))
        
        # Instructions
        instr = self.small_font.render("Press 1,2,3 to select tower", True, constants.BLACK)
        self.screen.blit(instr, (constants.SCREEN_WIDTH - 200, constants.SCREEN_HEIGHT - 25))
    
    def draw_wave_info(self, wave, enemies_in_wave, enemies_killed):
        """Draw wave information"""
        text = self.font.render(f"Wave: {wave}", True, constants.BLACK)
        self.screen.blit(text, (constants.SCREEN_WIDTH - 120, 10))
        subtext = self.small_font.render(f"Enemies: {enemies_killed}/{enemies_in_wave}", True, constants.BLACK)
        self.screen.blit(subtext, (constants.SCREEN_WIDTH - 120, 35))


def snap_to_grid(x, y):
    """Snap coordinates to nearest grid cell center"""
    grid_x = (x // constants.CELL_SIZE) * constants.CELL_SIZE + constants.CELL_SIZE // 2
    grid_y = (y // constants.CELL_SIZE) * constants.CELL_SIZE + constants.CELL_SIZE // 2
    return grid_x, grid_y


def is_on_path(y):
    """Check if a grid cell is on the enemy path"""
    path_top = constants.PATH_Y - 15
    path_bottom = constants.PATH_Y + 15
    return path_top <= y <= path_bottom
