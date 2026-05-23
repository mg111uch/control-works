"""
Main UI rendering for Dota2 view - minimap, portrait, stats.
"""
import pygame
from typing import Tuple, Optional


class UIMainRenderer:
    """Renderer for main UI elements - minimap, portrait, stats"""
    
    def __init__(self, screen, game_model, font_small, font_tiny):
        self.screen = screen
        self.game_model = game_model
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Fonts
        self.font_small = font_small
        self.font_tiny = font_tiny
        
        # Colors
        self.COLOR_RADIANT = (50, 200, 50)
        self.COLOR_DIRE = (200, 50, 50)
        self.COLOR_HP_BAR = (50, 255, 50)
        self.COLOR_HP_BG = (100, 0, 0)
        self.COLOR_MANA_BAR = (50, 150, 255)
        self.COLOR_MANA_BG = (0, 50, 100)
        
        # Minimap asset
        self.minimap_asset: Optional[pygame.Surface] = None
        
        # Hero portrait asset
        self.hero_portrait_asset: Optional[pygame.Surface] = None
    
    def load_minimap_asset(self, asset_path: str) -> bool:
        """Load minimap asset from file path. Returns True if successful, False otherwise."""
        try:
            self.minimap_asset = pygame.image.load(asset_path)
            return True
        except (pygame.error, FileNotFoundError):
            self.minimap_asset = None
            return False
    
    def load_hero_portrait_asset(self, asset_path: str) -> bool:
        """Load hero portrait asset from file path. Returns True if successful, False otherwise."""
        try:
            self.hero_portrait_asset = pygame.image.load(asset_path)
            return True
        except (pygame.error, FileNotFoundError):
            self.hero_portrait_asset = None
            return False
    
    def render_minimap(self, minimap, camera):
        """Render minimap with entities"""
        if self.minimap_asset is not None:
            minimap_surface = pygame.transform.scale(self.minimap_asset, (minimap.minimap_size, minimap.minimap_size))
        else:
            minimap_surface = pygame.Surface((minimap.minimap_size, minimap.minimap_size), pygame.SRCALPHA)
            minimap_surface.fill((20, 25, 30, 200))

        em = self.game_model.entity_manager
        for entity_id in em.get_all_entities():
            position = em.get_component(entity_id, 'position')
            hero = em.get_component(entity_id, 'hero')
            tower = em.get_component(entity_id, 'tower')
            creep = em.get_component(entity_id, 'creep')

            if not position:
                continue

            mini_x, mini_y = minimap.world_to_minimap(position.x, position.y)

            rel_x = mini_x - minimap.minimap_x
            rel_y = mini_y - minimap.minimap_y

            if 0 <= rel_x <= minimap.minimap_size and 0 <= rel_y <= minimap.minimap_size:
                if hero:
                    color = self.COLOR_RADIANT if hero.team == 0 else self.COLOR_DIRE
                    pygame.draw.circle(minimap_surface, color, (rel_x, rel_y), 4)
                elif tower:
                    color = self.COLOR_RADIANT if tower.team == 0 else self.COLOR_DIRE
                    pygame.draw.rect(minimap_surface, color, (rel_x - 3, rel_y - 3, 6, 6))
                elif creep:
                    color = self.COLOR_RADIANT if creep.team == 0 else self.COLOR_DIRE
                    pygame.draw.circle(minimap_surface, color, (rel_x, rel_y), 3)

        self.screen.blit(minimap_surface, (minimap.minimap_x, minimap.minimap_y))
        
        radiant_base_x, radiant_base_y = minimap.world_to_minimap(self.game_model.radiant_base[0], self.game_model.radiant_base[1])
        dire_base_x, dire_base_y = minimap.world_to_minimap(self.game_model.dire_base[0], self.game_model.dire_base[1])
        
        pygame.draw.circle(self.screen, self.COLOR_RADIANT, (radiant_base_x, radiant_base_y), 6)
        pygame.draw.circle(self.screen, (255, 255, 255), (radiant_base_x, radiant_base_y), 6, 1)
        
        pygame.draw.circle(self.screen, self.COLOR_DIRE, (dire_base_x, dire_base_y), 6)
        pygame.draw.circle(self.screen, (255, 255, 255), (dire_base_x, dire_base_y), 6, 1)
        
        viewport_rect = minimap.get_viewport_rect(camera.camera_x, camera.camera_y, camera.width, camera.height)
        pygame.draw.rect(self.screen, (255, 255, 0), viewport_rect, 2)

        pygame.draw.rect(self.screen, (100, 150, 200),
                        (minimap.minimap_x, minimap.minimap_y, minimap.minimap_size, minimap.minimap_size), 2)
    
    def render_hero_portrait(self):
        """Render hero portrait with HP/mana"""
        if 0 not in self.game_model.player_heroes:
            return
        
        hero_id = self.game_model.player_heroes[0]
        em = self.game_model.entity_manager
        
        hero = em.get_component(hero_id, 'hero')
        stats = em.get_component(hero_id, 'stats')
        
        if not hero or not stats:
            return
        
        port_x, port_y = 20, self.height - 230
        port_width = 140
        port_height = 187  # 3:4 ratio (140 * 4/3)
        
        if self.hero_portrait_asset is not None:
            scaled_portrait = pygame.transform.scale(self.hero_portrait_asset, (port_width, port_height))
            self.screen.blit(scaled_portrait, (port_x, port_y))
        else:
            pygame.draw.rect(self.screen, (40, 40, 50), (port_x, port_y, port_width, port_height))
        color = self.COLOR_RADIANT if hero.team == 0 else self.COLOR_DIRE
        pygame.draw.rect(self.screen, color, (port_x, port_y, port_width, port_height), 3)
        
        name_text = self.font_small.render("Shadow Fiend", True, (255, 255, 255))
        self.screen.blit(name_text, (port_x + 5, port_y - 25))  # Above portrait
        
        level_x = port_x + port_width - 15
        level_y = port_y + port_height - 15
        pygame.draw.circle(self.screen, (50, 50, 100), (level_x, level_y), 12)
        pygame.draw.circle(self.screen, (255, 255, 255), (level_x, level_y), 12, 1)
        level_text = self.font_tiny.render(str(hero.level), True, (255, 255, 255))
        level_rect = level_text.get_rect(center=(level_x, level_y))
        self.screen.blit(level_text, level_rect)
        
        hp_x = port_x + port_width + 10
        hp_y = port_y  # Match top edge with portrait
        hp_width = 195  # Match right edge of R skill box (170 + 195 = 365)
        hp_height = 35  # Increased thickness

        pygame.draw.rect(self.screen, self.COLOR_HP_BG, (hp_x, hp_y, hp_width, hp_height))
        hp_ratio = stats.current_hp / stats.max_hp
        pygame.draw.rect(self.screen, self.COLOR_HP_BAR, (hp_x, hp_y, int(hp_width * hp_ratio), hp_height))
        pygame.draw.rect(self.screen, (200, 200, 200), (hp_x, hp_y, hp_width, hp_height), 2)

        hp_text = self.font_small.render(f"{int(stats.current_hp)}/{int(stats.max_hp)}", True, (255, 255, 255))
        self.screen.blit(hp_text, (hp_x + 5, hp_y + 8))  # Adjusted y for thicker bar

        mana_y = hp_y + 40  # Closer spacing
        pygame.draw.rect(self.screen, self.COLOR_MANA_BG, (hp_x, mana_y, hp_width, hp_height))
        mana_ratio = stats.current_mana / stats.max_mana
        pygame.draw.rect(self.screen, self.COLOR_MANA_BAR, (hp_x, mana_y, int(hp_width * mana_ratio), hp_height))
        pygame.draw.rect(self.screen, (200, 200, 200), (hp_x, mana_y, hp_width, hp_height), 2)

        mana_text = self.font_small.render(f"{int(stats.current_mana)}/{int(stats.max_mana)}", True, (255, 255, 255))
        self.screen.blit(mana_text, (hp_x + 5, mana_y + 8))  # Adjusted y for thicker bar
    
    def render_stats_panel(self):
        """Render K/D/A and CS"""
        if 0 not in self.game_model.player_heroes:
            return
        
        hero_id = self.game_model.player_heroes[0]
        em = self.game_model.entity_manager
        hero = em.get_component(hero_id, 'hero')
        
        if not hero:
            return
        
        stats_x = self.width - 150
        stats_y = 10
        
        stats_texts = [
            f"K/D/A: {hero.kills}/{hero.deaths}/{hero.assists}",
            f"CS: {hero.last_hits}/{hero.denies}"
        ]
        
        for i, text in enumerate(stats_texts):
            surface = self.font_small.render(text, True, (255, 255, 255))
            self.screen.blit(surface, (stats_x, stats_y + i * 25))
