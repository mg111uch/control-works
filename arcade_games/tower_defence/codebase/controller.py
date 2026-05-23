"""
Game Controller
MVC Controller - Main game logic
"""

import time
import constants
from ecs.base import EntityManager
from ecs.systems import EnemySystem, TowerSystem, BulletSystem, WaveSystem
from ecs.components import PositionComponent, TowerComponent
from view import GameView, snap_to_grid, is_on_path


class GameController:
    """Controller for the game - manages all game logic"""
    
    def __init__(self, screen, pygame_module):
        self.screen = screen
        self.pygame = pygame_module
        
        # Create fonts
        self.font = pygame_module.font.SysFont(None, 36)
        self.small_font = pygame_module.font.SysFont(None, 24)
        
        # Create view
        self.view = GameView(screen, self.font, self.small_font)
        
        # Create ECS systems
        self.entity_manager = EntityManager()
        self.enemy_system = EnemySystem(constants.SCREEN_WIDTH)
        self.tower_system = TowerSystem()
        self.bullet_system = BulletSystem(constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT)
        self.wave_system = WaveSystem(constants.PATH_Y)
        
        # Connect systems
        self.enemy_system.set_entity_manager(self.entity_manager)
        self.tower_system.set_entity_manager(self.entity_manager)
        self.tower_system.set_bullet_system(self.bullet_system)
        self.bullet_system.set_enemy_system(self.enemy_system)
        self.wave_system.set_entity_manager(self.entity_manager)
        self.wave_system.set_enemy_system(self.enemy_system)
        
        # Game state
        self.score = 0
        self.money = constants.STARTING_MONEY
        self.selected_tower = 'artillery'
        self.running = True
        
        # Clock for frame timing
        self.clock = pygame_module.time.Clock()
    
    def handle_events(self):
        """Handle input events"""
        for event in self.pygame.event.get():
            if event.type == self.pygame.QUIT:
                self.running = False
            
            if event.type == self.pygame.KEYDOWN:
                if event.key == self.pygame.K_1:
                    self.selected_tower = 'artillery'
                elif event.key == self.pygame.K_2:
                    self.selected_tower = 'cannon'
                elif event.key == self.pygame.K_3:
                    self.selected_tower = 'laser'
            
            if event.type == self.pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.handle_mouse_click(event.pos)
    
    def handle_mouse_click(self, pos):
        """Handle mouse click"""
        mouse_x, mouse_y = pos
        
        # Check if clicking on an existing tower
        clicked_tower = self.tower_system.get_tower_at_position(mouse_x, mouse_y)
        
        if clicked_tower:
            # Select this tower
            self.tower_system.select_tower(clicked_tower)
        else:
            # Try to place a new tower
            grid_x, grid_y = snap_to_grid(mouse_x, mouse_y)
            
            # Check if tower can be placed
            tower_config = constants.TOWER_TYPES[self.selected_tower]
            if self.money >= tower_config['cost'] and not is_on_path(grid_y):
                # Check if no tower exists at position
                if self.tower_system.can_place_tower(grid_x, grid_y, self.tower_system.entities):
                    self.place_tower(grid_x, grid_y)
    
    def place_tower(self, x, y):
        """Place a tower at the given position"""
        # Create tower entity
        tower_entity = self.entity_manager.create_entity()
        
        # Add position component
        tower_entity.add_component(PositionComponent(x, y))
        
        # Add tower component
        tower_config = constants.TOWER_TYPES[self.selected_tower]
        tower_entity.add_component(TowerComponent(self.selected_tower, tower_config))
        
        # Add to tower system
        self.tower_system.add_entity(tower_entity)
        
        # Deduct money
        self.money -= tower_config['cost']
    
    def update(self, dt):
        """Update game state"""
        # Update wave system
        self.wave_system.update(dt)
        
        # Check for wave completion and award bonus
        if self.wave_system.check_wave_complete():
            self.money += constants.WAVE_BONUS
        
        # Get currently alive enemies before update
        alive_enemies_before = set(e.id for e in self.enemy_system.get_all_enemy_entities())
        
        # Update enemy system
        self.enemy_system.update(dt)
        
        # Update tower system (shooting)
        enemy_entities = self.enemy_system.get_all_enemy_entities()
        self.tower_system.update(dt, enemy_entities)
        
        # Update bullet system
        self.bullet_system.update(dt)
        
        # Get alive enemies after update
        alive_enemies_after = set(e.id for e in self.enemy_system.get_all_enemy_entities())
        
        # Calculate newly killed enemies (were alive before, now dead)
        newly_killed = alive_enemies_before - alive_enemies_after
        
        # Award score/money for each newly killed enemy
        for _ in range(len(newly_killed)):
            self.score += 10
            self.money += constants.KILL_REWARD
            self.wave_system.enemy_killed()
        
        # Clean up dead entities
        self.entity_manager.clear_dead_entities()
    
    def render(self):
        """Render the game"""
        # Clear screen
        self.view.clear()
        
        # Draw background elements
        self.view.draw_grid()
        self.view.draw_path()
        
        # Render systems
        self.enemy_system.render(self.screen, self.pygame)
        self.tower_system.render(self.screen, self.pygame)
        self.bullet_system.render(self.screen, self.pygame)
        
        # Draw UI
        wave_info = self.wave_system.get_wave_info()
        self.view.draw_score(self.score)
        self.view.draw_money(self.money)
        self.view.draw_tower_selector(self.selected_tower, self.money)
        self.view.draw_wave_info(
            wave_info['wave'],
            wave_info['enemies_per_wave'],
            wave_info['enemies_killed']
        )
        
        # Flip display
        self.pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        while self.running:
            # Handle events
            self.handle_events()
            
            # Update (60 FPS)
            dt = 1/60
            self.update(dt)
            
            # Render
            self.render()
            
            # Cap frame rate
            self.clock.tick(60)
        
        self.pygame.quit()
