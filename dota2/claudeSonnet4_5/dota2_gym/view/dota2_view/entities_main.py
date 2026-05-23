"""
Main entity rendering for Dota2 view - towers, creeps, heroes.
"""
import pygame
import numpy as np
from typing import Tuple, Optional, Dict


class EntityMainRenderer:
    """Renderer for main game entities - towers, creeps, heroes"""
    
    def __init__(self, screen, font_tiny, font_small):
        self.screen = screen
        self.font_tiny = font_tiny
        self.font_small = font_small
        
        # Colors
        self.COLOR_RADIANT = (50, 200, 50)
        self.COLOR_DIRE = (200, 50, 50)
        self.COLOR_HP_BAR = (50, 255, 50)
        self.COLOR_HP_BG = (100, 0, 0)
        
        # Tower assets - supports tier-specific assets
        self.tower_assets: Dict[str, Optional[pygame.Surface]] = {
            'radiant': None,
            'dire': None
        }
        self.tower_size = 60

        self.hero_assets: Dict[str, Optional[pygame.Surface]] = {}
        self.creep_assets: Dict[str, Optional[pygame.Surface]] = {
            'radiant_melee': None,
            'radiant_ranged': None,
            'dire_melee': None,
            'dire_ranged': None
        }
        self.hero_size = 120
        self.creep_size = 80
    
    def load_tower_asset(self, asset_type: str, asset_path: str) -> bool:
        """Load tower asset for a specific type. Returns True if successful, False otherwise."""
        try:
            self.tower_assets[asset_type] = pygame.image.load(asset_path)
            return True
        except Exception:
            self.tower_assets[asset_type] = None
            return False

    def load_hero_asset(self, hero_id: str, asset_path: str) -> bool:
        """Load hero asset. Returns True if successful, False otherwise."""
        try:
            self.hero_assets[hero_id] = pygame.image.load(asset_path)
            return True
        except Exception:
            self.hero_assets[hero_id] = None
            return False

    def load_creep_asset(self, team: int, creep_type: str, asset_path: str) -> bool:
        """Load creep asset for a team and type. Returns True if successful, False otherwise."""
        team_key = 'radiant' if team == 0 else 'dire'
        asset_key = f'{team_key}_{creep_type}'
        try:
            self.creep_assets[asset_key] = pygame.image.load(asset_path)
            return True
        except Exception:
            self.creep_assets[asset_key] = None
            return False
    
    def _get_tower_asset(self, team: int, tier: int):
        """Get the appropriate tower asset for the team."""
        team_key = 'radiant' if team == 0 else 'dire'
        return self.tower_assets.get(team_key)
    
    def render_towers(self, em, world_to_screen, screen_width, screen_height):
        """Render all towers"""
        towers = em.get_entities_with_component('tower')
        
        for tower_id in towers:
            position = em.get_component(tower_id, 'position')
            tower = em.get_component(tower_id, 'tower')
            stats = em.get_component(tower_id, 'stats')
            
            if not position or not tower or not stats:
                continue
            
            screen_x, screen_y = world_to_screen(position.x, position.y)
            
            if not (-100 < screen_x < screen_width + 100 and -100 < screen_y < screen_height + 100):
                continue
            
            asset = self._get_tower_asset(tower.team, tower.tier)
            
            asset_top = screen_y
            asset_height = 0
            
            if asset is not None:
                original_width, original_height = asset.get_size()
                scale_factor = 180.0 / max(original_width, original_height)
                new_width = int(original_width * scale_factor)
                new_height = int(original_height * scale_factor)
                scaled_asset = pygame.transform.scale(asset, (new_width, new_height))
                self.screen.blit(scaled_asset, (screen_x - new_width // 2, screen_y - new_height // 2))
                asset_top = screen_y - new_height // 2
                asset_height = new_height
            else:
                color = self.COLOR_RADIANT if tower.team == 0 else self.COLOR_DIRE
                pygame.draw.rect(self.screen, color, (screen_x - 30, screen_y - 30, 60, 60))
                pygame.draw.rect(self.screen, (255, 255, 255), (screen_x - 30, screen_y - 30, 60, 60), 2)
                asset_top = screen_y - 30
                asset_height = 60
            
            tier_text = self.font_small.render(f"T{tower.tier}", True, (255, 255, 255))
            self.screen.blit(tier_text, (screen_x - tier_text.get_width() // 2, asset_top - 28))
            
            self._render_hp_bar(screen_x, asset_top - 8, stats.current_hp, stats.max_hp, width=90)
    
    def render_creeps(self, em, world_to_screen, screen_width, screen_height):
        """Render all creeps"""
        creeps = em.get_entities_with_component('creep')
        
        for creep_id in creeps:
            position = em.get_component(creep_id, 'position')
            creep = em.get_component(creep_id, 'creep')
            stats = em.get_component(creep_id, 'stats')
            
            if not position or not creep or not stats:
                continue
            
            screen_x, screen_y = world_to_screen(position.x, position.y)
            
            if not (-50 < screen_x < screen_width + 50 and -50 < screen_y < screen_height + 50):
                continue
            
            team_key = 'radiant' if creep.team == 0 else 'dire'
            asset_key = f'{team_key}_{creep.creep_type}'
            creep_asset = self.creep_assets.get(asset_key)
            
            if creep_asset is not None:
                original_width, original_height = creep_asset.get_size()
                scale_factor = self.creep_size / max(original_width, original_height)
                new_width = int(original_width * scale_factor)
                new_height = int(original_height * scale_factor)
                scaled_asset = pygame.transform.scale(creep_asset, (new_width, new_height))
                self.screen.blit(scaled_asset, (screen_x - new_width // 2, screen_y - new_height // 2))
            else:
                team_color = self.COLOR_RADIANT if creep.team == 0 else self.COLOR_DIRE
                
                if creep.creep_type == 'melee':
                    color = team_color
                    radius = 18
                else:
                    color = (team_color[0] // 2, team_color[1] // 2, team_color[2] // 2)
                    radius = 15
                
                pygame.draw.circle(self.screen, color, (screen_x, screen_y), radius)
                pygame.draw.circle(self.screen, (255, 255, 255), (screen_x, screen_y), radius, 1)
            
            self._render_hp_bar(screen_x, screen_y - 25, stats.current_hp, stats.max_hp, width=40)
    
    def render_heroes(self, em, world_to_screen, screen_width, screen_height):
        """Render all heroes with direction arrows"""
        heroes = em.get_entities_with_component('hero')
        
        for hero_id in heroes:
            position = em.get_component(hero_id, 'position')
            hero = em.get_component(hero_id, 'hero')
            stats = em.get_component(hero_id, 'stats')
            collision = em.get_component(hero_id, 'collision')
            selection = em.get_component(hero_id, 'selection')
            
            if not position or not hero or not stats:
                continue
            
            screen_x, screen_y = world_to_screen(position.x, position.y)
            
            if not (-100 < screen_x < screen_width + 100 and -100 < screen_y < screen_height + 100):
                continue
            
            hero_asset = self.hero_assets.get(hero.hero_id)
            radius = int(collision.radius) if collision else 24
            color = self.COLOR_RADIANT if hero.team == 0 else self.COLOR_DIRE
            
            asset_top = screen_y
            
            if hero_asset is not None:
                original_width, original_height = hero_asset.get_size()
                scale_factor = self.hero_size / max(original_width, original_height)
                new_width = int(original_width * scale_factor)
                new_height = int(original_height * scale_factor)
                scaled_asset = pygame.transform.scale(hero_asset, (new_width, new_height))
                self.screen.blit(scaled_asset, (screen_x - new_width // 2, screen_y - new_height // 2))
                asset_top = screen_y - new_height // 2
            else:
                pygame.draw.circle(self.screen, color, (screen_x, screen_y), radius)
                pygame.draw.circle(self.screen, (255, 255, 255), (screen_x, screen_y), radius, 2)
                asset_top = screen_y - radius
            
            angle = hero.facing_angle
            arrow_len = radius + 10
            arrow_x = screen_x + int(np.cos(angle) * arrow_len)
            arrow_y = screen_y + int(np.sin(angle) * arrow_len)
            pygame.draw.line(self.screen, (255, 255, 255), (screen_x, screen_y), (arrow_x, arrow_y), 3)
            
            if selection and selection.selected:
                pygame.draw.circle(self.screen, (255, 255, 0), (screen_x, screen_y), radius + 5, 2)
            
            movement = em.get_component(hero_id, 'movement')
            if movement and movement.is_moving and movement.target_x is not None:
                target_x, target_y = world_to_screen(movement.target_x, movement.target_y)
                pygame.draw.circle(self.screen, color, (target_x, target_y), 5)
                pygame.draw.line(self.screen, color, (screen_x, screen_y), (target_x, target_y), 1)
            
            combat = em.get_component(hero_id, 'combat')
            if combat and selection and selection.selected:
                range_radius = int(combat.attack_range)
                pygame.draw.circle(self.screen, (*color[:3], 50), (screen_x, screen_y), range_radius, 1)
            
            self._render_hp_bar(screen_x, asset_top - 15, stats.current_hp, stats.max_hp)
            
            if hero.hero_id == 'shadow_fiend' and hero.souls > 0:
                soul_text = self.font_small.render(f"Souls: {hero.souls}", True, (255, 255, 100))
                self.screen.blit(soul_text, (screen_x - 30, asset_top - 32))
    
    def _render_hp_bar(self, x: int, y: int, current_hp: float, max_hp: float, width: int = 60):
        """Render HP bar"""
        bar_height = 6
        
        bg_rect = pygame.Rect(x - width // 2, y, width, bar_height)
        pygame.draw.rect(self.screen, self.COLOR_HP_BG, bg_rect)
        
        hp_ratio = max(0.0, min(1.0, current_hp / max_hp))
        hp_width = int(width * hp_ratio)
        hp_rect = pygame.Rect(x - width // 2, y, hp_width, bar_height)
        pygame.draw.rect(self.screen, self.COLOR_HP_BAR, hp_rect)
        
        pygame.draw.rect(self.screen, (200, 200, 200), bg_rect, 1)
