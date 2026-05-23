"""
Menu rendering for Dota2 view - shop and pause menu.
"""
import pygame
from typing import Tuple, Optional, Dict


class MenuRenderer:
    """Renderer for game menus (shop, pause)"""
    
    def __init__(self, screen, game_model, font, font_small, font_large, font_tiny):
        self.screen = screen
        self.game_model = game_model
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Fonts
        self.font = font
        self.font_small = font_small
        self.font_large = font_large
        self.font_tiny = font_tiny
        
        # Button rects for click detection
        self.resume_button_rect = None
        self.quit_button_rect = None
        
        # Shop item rects for click detection
        self.shop_item_rects: Dict[int, pygame.Rect] = {}
        self.shop_items_list = []
    
    def render_shop(self):
        """Render shop panel"""
        # Shop background
        shop_x, shop_y = 300, 100
        shop_w, shop_h = 600, 400
        
        pygame.draw.rect(self.screen, (30, 30, 40), (shop_x, shop_y, shop_w, shop_h))
        pygame.draw.rect(self.screen, (100, 150, 200), (shop_x, shop_y, shop_w, shop_h), 3)
        
        # Title
        title = self.font_large.render("SHOP (F2 to close)", True, (255, 255, 255))
        self.screen.blit(title, (shop_x + 20, shop_y + 10))
        
        # Items grid
        self.shop_item_rects.clear()
        self.shop_items_list = []
        
        try:
            from engine.systems.item_system import ItemShop
            shop = ItemShop()
            
            items_list = list(shop.items.values())[:16]  # First 16 items
            self.shop_items_list = items_list
            
            for i, item in enumerate(items_list):
                col = i % 4
                row = i // 4
                
                item_x = shop_x + 20 + col * 140
                item_y = shop_y + 60 + row * 80
                
                # Item box
                item_rect = pygame.Rect(item_x, item_y, 130, 70)
                pygame.draw.rect(self.screen, (50, 50, 60), item_rect)
                pygame.draw.rect(self.screen, (150, 150, 150), item_rect, 2)
                
                # Store rect for click detection
                self.shop_item_rects[i] = item_rect
                
                # Item name - doubled size (using font_small instead of font_tiny)
                name_text = self.font_small.render(item.name, True, (255, 255, 255))
                self.screen.blit(name_text, (item_x + 5, item_y + 5))
                
                # Item cost - doubled size
                cost_text = self.font_small.render(f"{item.cost}g", True, (255, 215, 0))
                self.screen.blit(cost_text, (item_x + 5, item_y + 28))
                
                # Item stats - doubled size
                if item.strength > 0:
                    stat_text = self.font_small.render(f"+{item.strength} STR", True, (200, 100, 100))
                    self.screen.blit(stat_text, (item_x + 5, item_y + 48))
                elif item.agility > 0:
                    stat_text = self.font_small.render(f"+{item.agility} AGI", True, (100, 200, 100))
                    self.screen.blit(stat_text, (item_x + 5, item_y + 48))
                elif item.intelligence > 0:
                    stat_text = self.font_small.render(f"+{item.intelligence} INT", True, (100, 150, 255))
                    self.screen.blit(stat_text, (item_x + 5, item_y + 48))
                elif item.damage > 0:
                    stat_text = self.font_small.render(f"+{item.damage} DMG", True, (200, 200, 200))
                    self.screen.blit(stat_text, (item_x + 5, item_y + 48))
        except ImportError:
            help_text = self.font.render("Shop system not yet implemented", True, (200, 200, 200))
            self.screen.blit(help_text, (shop_x + 150, shop_y + 200))
    
    def handle_shop_click(self, pos: Tuple[int, int]) -> Optional[str]:
        """Handle click on shop item, return item_id if purchased, None otherwise"""
        for i, rect in self.shop_item_rects.items():
            if rect.collidepoint(pos):
                if i < len(self.shop_items_list):
                    item = self.shop_items_list[i]
                    return self._purchase_item(item.item_id)
        return None
    
    def _purchase_item(self, item_id: str) -> Optional[str]:
        """Attempt to purchase an item for the player hero"""
        if 0 not in self.game_model.player_heroes:
            return None
        
        hero_id = self.game_model.player_heroes[0]
        em = self.game_model.entity_manager
        
        inventory = em.get_component(hero_id, 'inventory')
        if not inventory:
            # Add inventory component if missing
            from engine.systems.item_system import InventoryComponent
            inventory = InventoryComponent()
            em.add_component(hero_id, 'inventory', inventory)
        
        from engine.systems.item_system import ItemShop
        shop = ItemShop()
        success = shop.buy_item(item_id, inventory)
        
        if success:
            return item_id
        return None
    
    def render_pause_menu(self):
        """Render pause menu overlay"""
        # Dark overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Pause menu box
        menu_w, menu_h = 400, 300
        menu_x = (self.width - menu_w) // 2
        menu_y = (self.height - menu_h) // 2
        
        pygame.draw.rect(self.screen, (40, 40, 50), (menu_x, menu_y, menu_w, menu_h))
        pygame.draw.rect(self.screen, (100, 150, 200), (menu_x, menu_y, menu_w, menu_h), 3)
        
        # Title
        title = self.font_large.render("GAME PAUSED", True, (255, 255, 255))
        title_rect = title.get_rect(center=(menu_x + menu_w // 2, menu_y + 40))
        self.screen.blit(title, title_rect)
        
        # Game stats
        if 0 in self.game_model.player_heroes:
            hero_id = self.game_model.player_heroes[0]
            em = self.game_model.entity_manager
            hero = em.get_component(hero_id, 'hero')
            
            if hero:
                stats_y = menu_y + 100
                stats = [
                    f"Time: {self.game_model.game_time:.1f}s",
                    f"K/D/A: {hero.kills}/{hero.deaths}/{hero.assists}",
                    f"Last Hits: {hero.last_hits}",
                    f"Denies: {hero.denies}"
                ]
                
                for i, text in enumerate(stats):
                    surface = self.font_small.render(text, True, (200, 200, 200))
                    rect = surface.get_rect(center=(menu_x + menu_w // 2, stats_y + i * 25))
                    self.screen.blit(surface, rect)
        
        # Buttons
        button_y = menu_y + menu_h - 80
        
        # Resume button
        resume_rect = pygame.Rect(menu_x + 50, button_y, 130, 40)
        pygame.draw.rect(self.screen, (50, 150, 50), resume_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), resume_rect, 2)
        resume_text = self.font.render("Resume", True, (255, 255, 255))
        resume_text_rect = resume_text.get_rect(center=resume_rect.center)
        self.screen.blit(resume_text, resume_text_rect)
        
        # Quit button
        quit_rect = pygame.Rect(menu_x + 220, button_y, 130, 40)
        pygame.draw.rect(self.screen, (150, 50, 50), quit_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), quit_rect, 2)
        quit_text = self.font.render("Quit", True, (255, 255, 255))
        quit_text_rect = quit_text.get_rect(center=quit_rect.center)
        self.screen.blit(quit_text, quit_text_rect)
        
        # Store rects for click detection
        self.resume_button_rect = resume_rect
        self.quit_button_rect = quit_rect
    
    def handle_pause_menu_click(self, pos: Tuple[int, int]) -> Optional[str]:
        """Handle click on pause menu, return 'resume', 'quit', or None"""
        if self.resume_button_rect and self.resume_button_rect.collidepoint(pos):
            return 'resume'
        
        if self.quit_button_rect and self.quit_button_rect.collidepoint(pos):
            return 'quit'
        
        return None


class ShopPanel:
    """Shop panel state management"""
    
    def __init__(self):
        self.shop_open = False
    
    def toggle(self):
        """Toggle shop panel"""
        self.shop_open = not self.shop_open
    
    def is_open(self) -> bool:
        """Check if shop is open"""
        return self.shop_open
