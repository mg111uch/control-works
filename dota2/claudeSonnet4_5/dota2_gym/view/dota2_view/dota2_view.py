"""
Complete Dota2-Style View System
Modularized implementation.
"""
import pygame
import os
from typing import Tuple, Optional, Dict

from .camera import Camera, Minimap
from .entities_main import EntityMainRenderer
from .entities_projectiles import ProjectileRenderer, SelectionBox
from .ui_main import UIMainRenderer
from .ui_inventory import UIInventoryRenderer
from .menus import MenuRenderer, ShopPanel
from .draw_game_world import generate_world_map


class Dota2View:
    """Complete Dota2-style rendering system"""
    
    def __init__(self, screen, game_model):
        self.screen = screen
        self.game_model = game_model
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Config
        self.config = game_model.config
        self.map_width = self.config['game']['map_width']
        self.map_height = self.config['game']['map_height']
        self.fow_enabled = self.config['fog_of_war']['enabled']
        self.vision_radius = self.config['fog_of_war']['vision_radius']
        
        # UI State
        self.paused = False
        
        # Base assets
        self.base_assets: Dict[str, Optional[pygame.Surface]] = {
            'radiant': None,
            'dire': None
        }
        
        # Initialize subsystems
        self.camera = Camera(screen, self.config, self.map_width, self.map_height)
        # Center camera on radiant base
        self.camera.camera_x = self.game_model.radiant_base[0] - self.camera.width // 2
        self.camera.camera_y = self.game_model.radiant_base[1] - self.camera.height // 2
        # Clamp camera position
        self.camera.camera_x = max(0, min(self.map_width - self.camera.width, self.camera.camera_x))
        self.camera.camera_y = max(0, min(self.map_height - self.camera.height, self.camera.camera_y))
        self.minimap = Minimap(screen, self.map_width, self.map_height)
        self.entity_renderer = EntityMainRenderer(screen, pygame.font.Font(None, 14), pygame.font.Font(None, 18))
        self.projectile_renderer = ProjectileRenderer(screen)
        self.selection_box = SelectionBox()
        self.ui_main = UIMainRenderer(screen, game_model, pygame.font.Font(None, 32), pygame.font.Font(None, 14))
        self.font_small = pygame.font.Font(None, 24)
        self.font = pygame.font.Font(None, 24)
        self.ui_inventory = UIInventoryRenderer(
            screen, game_model,
            pygame.font.Font(None, 24), pygame.font.Font(None, 18),
            pygame.font.Font(None, 14),
            self._get_item_abbrev()
        )
        self.menu_renderer = MenuRenderer(
            screen, game_model,
            pygame.font.Font(None, 24), pygame.font.Font(None, 18),
            pygame.font.Font(None, 32), pygame.font.Font(None, 14)
        )
        self.shop_panel = ShopPanel()
        
        # Load minimap asset
        self._load_minimap_asset()
        
        # Load tower assets
        self._load_tower_assets()
        
        # Load base assets
        self._load_base_assets()
        
        # Load creep assets
        self._load_creep_assets()
        
        # Load hero assets
        self._load_hero_assets()
        
        # Load hero portrait asset
        self._load_hero_portrait_asset()
        
        # Base size
        self.base_size = 400
        self.base_hp = 2000
        self.base_max_hp = 2000
        
        # Colors
        self.COLOR_BG = (30, 40, 50)
        self.COLOR_GRID = (60, 75, 90)
        self.COLOR_RADIANT = (50, 200, 50)
        self.COLOR_DIRE = (200, 50, 50)

        # Pre-render the world map
        self.world_surface = pygame.Surface((self.map_width, self.map_height))
        generate_world_map(self.world_surface)
        
        # Pre-create fog of war surface for reuse
        self._fog_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
    
    def _get_item_abbrev(self):
        """Get item abbreviations"""
        return {
            'wraith_band': 'WB', 'null_talisman': 'NT', 'bracer': 'BR',
            'magic_wand': 'MW', 'boots': 'BT', 'treads': 'PT',
            'bottle': 'BO', 'mekansm': 'MK', 'blink': 'BL',
            'bkb': 'BK', 'shadow_blade': 'SB', 'euls': 'EU',
            'force_staff': 'FS', 'hex': 'HX', 'dagon': 'DG',
            'rapier': 'RP'
        }
    
    def _load_minimap_asset(self):
        """Load minimap asset from config if available"""
        if 'assets' in self.config and 'minimap' in self.config['assets']:
            minimap_path = self.config['assets']['minimap']
            if minimap_path:
                self.ui_main.load_minimap_asset(minimap_path)
    
    def _load_tower_assets(self):
        """Load tower assets if available - supports tier-specific assets"""
        if 'assets' in self.config:
            assets = self.config['assets']
            self.entity_renderer.load_tower_asset('radiant_t1', assets.get('radiant_t1', ''))
            self.entity_renderer.load_tower_asset('radiant_t2', assets.get('radiant_t2', ''))
            self.entity_renderer.load_tower_asset('radiant', assets.get('radiant_tower', ''))
            self.entity_renderer.load_tower_asset('dire', assets.get('dire_tower', ''))
    
    def _load_base_assets(self):
        """Load base assets if available"""
        if 'assets' in self.config:
            assets = self.config['assets']
            if 'radiant_base' in assets:
                self._load_base_asset('radiant', assets['radiant_base'])
            if 'dire_base' in assets:
                self._load_base_asset('dire', assets['dire_base'])
    
    def _load_base_asset(self, team_type: str, asset_path: str) -> bool:
        """Load a single base asset. Returns True if successful."""
        try:
            self.base_assets[team_type] = pygame.image.load(asset_path)
            return True
        except Exception:
            self.base_assets[team_type] = None
            return False
    
    def _load_creep_assets(self):
        """Load creep assets if available"""
        if 'assets' in self.config:
            assets = self.config['assets']
            self.entity_renderer.load_creep_asset(0, 'melee', assets.get('radiant_meele', ''))
            self.entity_renderer.load_creep_asset(0, 'ranged', assets.get('radiant_ranged', ''))
            self.entity_renderer.load_creep_asset(1, 'melee', assets.get('dire_meele', ''))
            self.entity_renderer.load_creep_asset(1, 'ranged', assets.get('dire_ranged', ''))
    
    def _load_hero_assets(self):
        """Load hero assets if available"""
        if 'assets' in self.config:
            assets = self.config['assets']
            if 'shadow_fiend' in assets:
                self.entity_renderer.load_hero_asset('shadow_fiend', assets['shadow_fiend'])
    
    def _load_hero_portrait_asset(self):
        """Load hero portrait asset from config if available"""
        if 'assets' in self.config and 'hero_potrait' in self.config['assets']:
            portrait_path = self.config['assets']['hero_potrait']
            if portrait_path:
                self.ui_main.load_hero_portrait_asset(portrait_path)
    
    def _is_ui_click(self, pos: Tuple[int, int]) -> bool:
        """Check if click is on UI element"""
        x, y = pos
        
        # Portrait area
        if 20 <= x <= 160 and self.height - 230 <= y <= self.height - 43:
            return True
        
        # Abilities area
        if 240 <= x <= 540 and self.height - 180 <= y <= self.height - 20:
            return True
        
        # Items area
        if 560 <= x <= 860 and self.height - 180 <= y <= self.height - 20:
            return True
        
        # Minimap
        if self.minimap.is_in_minimap(x, y):
            return True
        
        # Shop panel
        if self.shop_panel.is_open() and 300 <= x <= 900 and 100 <= y <= 500:
            return True
        
        return False
    
    def handle_event(self, event):
        """Handle all input events"""
        # Camera drag
        self.camera.handle_mouse_drag(event)
        
        # Box selection
        start, end = self.selection_box.handle_selection(event, self.screen, self._is_ui_click)
        if start and end:
            self.selection_box.select_units_in_box(
                self.game_model.entity_manager, start, end,
                self.camera.screen_to_world
            )
    
    def render(self, dt: float):
        """Render the entire game state"""
        # Update camera edge panning
        mouse_pos = pygame.mouse.get_pos()
        self.camera.update_edge_panning(mouse_pos[0], mouse_pos[1], dt)

        # Background - render world map
        self.screen.blit(self.world_surface, (0, 0), (self.camera.camera_x, self.camera.camera_y, self.width, self.height))
        
        # Bases
        self._render_bases()
        
        # Entities
        world_to_screen = self.camera.world_to_screen
        em = self.game_model.entity_manager
        
        self.entity_renderer.render_towers(em, world_to_screen, self.width, self.height)
        self.entity_renderer.render_creeps(em, world_to_screen, self.width, self.height)
        self.entity_renderer.render_heroes(em, world_to_screen, self.width, self.height)
        self.projectile_renderer.render(em, world_to_screen, self.width, self.height)
        
        # Selection box
        self.selection_box.render(self.screen)
        
        # Fog of War
        if self.fow_enabled:
            self._render_fog_of_war()
        
        # UI
        self.ui_main.render_minimap(self.minimap, self.camera)
        self.ui_main.render_hero_portrait()
        self.ui_inventory.render_hero_stats()
        self.ui_inventory.render_abilities_panel()
        self.ui_inventory.render_items_panel()
        self.ui_main.render_stats_panel()
        self.ui_inventory.render_gold_and_courier(self.minimap)

        # Shop hint text
        shop_text = self.font.render("F2: Shop", True, (255, 255, 255))
        self.screen.blit(shop_text, (20, 20))
        
        # Render ground elevation
        self._render_ground_elevation()
        
        # Render gold popups
        self._render_gold_popups()
        
        # Game start time
        self._render_game_time()

        # Shop
        if self.shop_panel.is_open():
            self.menu_renderer.render_shop()
        
        # Pause menu
        if self.paused:
            self.menu_renderer.render_pause_menu()
    
    def _render_game_time(self):
        """Render game elapsed time or pregame countdown at top middle"""
        if self.game_model.in_pregame:
            remaining = max(0, self.game_model.pregame_countdown - self.game_model.pregame_elapsed)
            time_str = f"PRE-GAME: {remaining:.1f}s"
            color = (255, 200, 100)  # Orange tint for countdown
        else:
            total_seconds = int(self.game_model.game_time)
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            color = (255, 255, 255)
        
        time_text = self.font.render(time_str, True, color)
        text_rect = time_text.get_rect(center=(self.width // 2, 30))
        self.screen.blit(time_text, text_rect)
    
    def _render_ground_elevation(self):
        """Render ground elevation text for player hero"""
        # Get player hero position
        if 0 not in self.game_model.player_heroes:
            return
        
        hero_id = self.game_model.player_heroes[0]
        position = self.game_model.entity_manager.get_component(hero_id, 'position')
        movement = self.game_model.entity_manager.get_component(hero_id, 'movement')
        
        if not position:
            return
        
        # Get elevation from stair registry (no scaling needed - get_elevation_at_position handles it)
        elevation = self.game_model.stair_registry.get_elevation_at_position(position)
        
        # Render position and elevation
        pos_text = f"Pos: ({int(position.x)}, {int(position.y)})"
        elev_label = f"Elevation: {elevation:.1f}"
        
        pos_surface = self.font_small.render(pos_text, True, (200, 200, 200))
        elev_surface = self.font_small.render(elev_label, True, (100, 200, 255))
        
        # Position in top-left corner
        y_offset = 40
        self.screen.blit(pos_surface, (10, y_offset))
        self.screen.blit(elev_surface, (10, y_offset + 25))
        
        # Render waypoint path status if moving with waypoints
        y_offset += 55
        # Check if movement component is valid and hero is moving
        try:
            is_moving = movement and movement.is_moving
            has_waypoints = False
            has_direct_target = False
            
            if is_moving:
                # Check if waypoint_queue is a valid list
                try:
                    has_waypoints = movement.waypoint_queue and len(movement.waypoint_queue) > 0
                except (TypeError, AttributeError):
                    has_waypoints = False
                
                # Check if we have direct target
                try:
                    has_direct_target = (movement.target_x is not None and movement.target_y is not None and
                                       isinstance(movement.target_x, (int, float)) and
                                       isinstance(movement.target_y, (int, float)))
                except (TypeError, AttributeError):
                    has_direct_target = False
            
            if has_waypoints:
                # Moving with waypoints
                num_waypoints = len(movement.waypoint_queue)
                try:
                    final_x = int(movement.final_target_x) if movement.final_target_x is not None else None
                    final_y = int(movement.final_target_y) if movement.final_target_y is not None else None
                    if final_x is not None and final_y is not None:
                        path_text = f"Path: {num_waypoints} waypoint(s) to ({final_x}, {final_y})"
                    else:
                        path_text = f"Path: {num_waypoints} waypoint(s)"
                except (TypeError, AttributeError):
                    path_text = f"Path: {num_waypoints} waypoint(s)"
                path_surface = self.font_small.render(path_text, True, (100, 255, 100))
                self.screen.blit(path_surface, (10, y_offset))
            elif has_direct_target:
                # Direct movement
                try:
                    path_text = f"Moving to ({int(movement.target_x)}, {int(movement.target_y)})"
                except (TypeError, AttributeError):
                    path_text = "Moving..."
                path_surface = self.font_small.render(path_text, True, (100, 255, 100))
                self.screen.blit(path_surface, (10, y_offset))
        except Exception:
            # If anything goes wrong, just skip the path display
            pass
    
    def _render_gold_popups(self):
        """Render gold popup text at last hit locations"""
        for popup in self.game_model.gold_popups:
            world_x, world_y = popup['x'], popup['y']
            screen_x, screen_y = self.camera.world_to_screen(world_x, world_y)
            
            # Fade out based on remaining time
            alpha = int(255 * (popup['time'] / 1.0))
            alpha = max(0, min(255, alpha))
            
            # Render gold text
            gold_text = f"+{popup['gold']}g"
            text_surface = self.font_small.render(gold_text, True, (255, 215, 0))  # Gold color
            
            # Move text upward over time
            y_offset = int((1.0 - popup['time']) * 30)
            
            self.screen.blit(text_surface, (screen_x - text_surface.get_width() // 2, screen_y - 30 - y_offset))
    
    def _render_grid(self):
        """Render background grid"""
        grid_size = 500
        
        start_x = int(self.camera.camera_x / grid_size) * grid_size
        for x in range(int(start_x), int(start_x + self.width + grid_size), grid_size):
            screen_x, _ = self.camera.world_to_screen(x, 0)
            if 0 <= screen_x <= self.width:
                pygame.draw.line(self.screen, self.COLOR_GRID, (screen_x, 0), (screen_x, self.height), 1)
        
        start_y = int(self.camera.camera_y / grid_size) * grid_size
        for y in range(int(start_y), int(start_y + self.height + grid_size), grid_size):
            _, screen_y = self.camera.world_to_screen(0, y)
            if 0 <= screen_y <= self.height:
                pygame.draw.line(self.screen, self.COLOR_GRID, (0, screen_y), (self.width, screen_y), 1)
    
    def _render_bases(self):
        """Render team bases"""
        hp_bar_width = 120
        
        # Radiant base
        radiant_x, radiant_y = self.camera.world_to_screen(
            self.game_model.radiant_base[0], self.game_model.radiant_base[1])
        
        radiant_asset_top = radiant_y
        
        if self.base_assets['radiant'] is not None:
            original_width, original_height = self.base_assets['radiant'].get_size()
            scale_factor = self.base_size / max(original_width, original_height)
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
            scaled_asset = pygame.transform.scale(self.base_assets['radiant'], (new_width, new_height))
            self.screen.blit(scaled_asset, (radiant_x - new_width // 2, radiant_y - new_height // 2))
            radiant_asset_top = radiant_y - new_height // 2
        else:
            pygame.draw.rect(self.screen, self.COLOR_RADIANT,
                            (radiant_x - 100, radiant_y - 100, 200, 200), 3)
            radiant_asset_top = radiant_y - 100
        
        self._render_hp_bar(radiant_x, radiant_asset_top - 15, self.base_hp, self.base_max_hp, hp_bar_width, self.COLOR_RADIANT)

        # Dire base
        dire_x, dire_y = self.camera.world_to_screen(
            self.game_model.dire_base[0], self.game_model.dire_base[1])
        
        dire_asset_top = dire_y
        
        if self.base_assets['dire'] is not None:
            original_width, original_height = self.base_assets['dire'].get_size()
            scale_factor = self.base_size / max(original_width, original_height)
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
            scaled_asset = pygame.transform.scale(self.base_assets['dire'], (new_width, new_height))
            self.screen.blit(scaled_asset, (dire_x - new_width // 2, dire_y - new_height // 2))
            dire_asset_top = dire_y - new_height // 2
        else:
            pygame.draw.rect(self.screen, self.COLOR_DIRE,
                            (dire_x - 100, dire_y - 100, 200, 200), 3)
            dire_asset_top = dire_y - 100
        
        self._render_hp_bar(dire_x, dire_asset_top - 15, self.base_hp, self.base_max_hp, hp_bar_width, self.COLOR_DIRE)

    def _render_hp_bar(self, x: int, y: int, current_hp: float, max_hp: float, width: int = 60, color=None):
        """Render HP bar"""
        bar_height = 8
        bg_color = (100, 0, 0)
        hp_color = (50, 255, 50)
        
        if color is not None:
            bg_color = (color[0] // 2, 0, 0)
            hp_color = (color[0], color[1], color[2] // 2)
        
        bg_rect = pygame.Rect(x - width // 2, y, width, bar_height)
        pygame.draw.rect(self.screen, bg_color, bg_rect)
        
        hp_ratio = max(0.0, min(1.0, current_hp / max_hp))
        hp_width = int(width * hp_ratio)
        hp_rect = pygame.Rect(x - width // 2, y, hp_width, bar_height)
        pygame.draw.rect(self.screen, hp_color, hp_rect)
        
        pygame.draw.rect(self.screen, (200, 200, 200), bg_rect, 1)
    
    def _render_fog_of_war(self):
        """Render fog of war"""
        # Reuse pre-created fog surface
        self._fog_surface.fill((0, 0, 0, 180))
        
        if 0 in self.game_model.player_heroes:
            hero_id = self.game_model.player_heroes[0]
            position = self.game_model.entity_manager.get_component(hero_id, 'position')
            
            if position:
                screen_x, screen_y = self.camera.world_to_screen(position.x, position.y)
                pygame.draw.circle(self._fog_surface, (0, 0, 0, 0), 
                                 (screen_x, screen_y), int(self.vision_radius))
        
        self.screen.blit(self._fog_surface, (0, 0))
    
    def handle_pause_menu_click(self, pos: Tuple[int, int]) -> str:
        """Handle click on pause menu"""
        return self.menu_renderer.handle_pause_menu_click(pos)
    
    def toggle_shop(self):
        """Toggle shop panel"""
        self.shop_panel.toggle()
    
    def toggle_pause(self):
        """Toggle pause state"""
        self.paused = not self.paused
    
    def deliver_courier(self):
        """Deliver items via courier (F3)"""
        print("[Courier] Delivering items to hero!")

    def handle_mouse_drag(self, event):
        """Handle camera dragging"""
        self.camera.handle_mouse_drag(event)

    def handle_box_selection(self, event):
        """Handle box selection for unit selection"""
        start, end = self.selection_box.handle_selection(event, self.screen, self._is_ui_click)
        if start and end:
            self.selection_box.select_units_in_box(
                self.game_model.entity_manager, start, end,
                self.camera.screen_to_world
            )

    def is_in_minimap(self, x, y):
        """Check if point is in minimap"""
        return self.minimap.is_in_minimap(x, y)

    def minimap_to_world(self, mini_x, mini_y):
        """Convert minimap coordinates to world coordinates"""
        return self.minimap.minimap_to_world(mini_x, mini_y)

    def screen_to_world(self, screen_x, screen_y):
        """Convert screen coordinates to world coordinates"""
        return self.camera.screen_to_world(screen_x, screen_y)

    
    @property
    def camera_x(self):
        return self.camera.camera_x
    
    @camera_x.setter
    def camera_x(self, value):
        self.camera.camera_x = value
    
    @property
    def camera_y(self):
        return self.camera.camera_y
    
    @camera_y.setter
    def camera_y(self, value):
        self.camera.camera_y = value
    
    @property
    def resume_button_rect(self):
        return self.menu_renderer.resume_button_rect
    
    @property
    def quit_button_rect(self):
        return self.menu_renderer.quit_button_rect

