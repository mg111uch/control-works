"""
Inventory UI rendering for Dota2 view - abilities, items, gold, courier.
"""
import pygame
from typing import Tuple


class UIInventoryRenderer:
    """Renderer for inventory UI - abilities, items, gold, courier"""
    
    def __init__(self, screen, game_model, font, font_small, font_tiny, item_abbrev):
        self.screen = screen
        self.game_model = game_model
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Fonts
        self.font = font
        self.font_small = font_small
        self.font_tiny = font_tiny
        
        # Item abbreviations
        self.item_abbrev = item_abbrev
    
    def _get_item_bonus_stats(self, inventory):
        """Calculate bonus stats from items"""
        bonus = {
            'strength': 0, 'agility': 0, 'intelligence': 0,
            'damage': 0, 'attack_speed': 0, 'movement_speed': 0,
            'armor': 0, 'hp_regen': 0.0, 'mana_regen': 0.0
        }
        
        if not inventory:
            return bonus
        
        for item in inventory.items:
            if item:
                bonus['strength'] += item.strength
                bonus['agility'] += item.agility
                bonus['intelligence'] += item.intelligence
                bonus['damage'] += item.damage
                bonus['attack_speed'] += item.attack_speed
                bonus['movement_speed'] += item.movement_speed
                bonus['armor'] += item.armor
                bonus['hp_regen'] += item.hp_regen
                bonus['mana_regen'] += item.mana_regen
        
        return bonus
    
    def render_hero_stats(self):
        """Render hero stats display between mana bar and abilities panel"""
        if 0 not in self.game_model.player_heroes:
            return
        
        hero_id = self.game_model.player_heroes[0]
        em = self.game_model.entity_manager
        
        hero = em.get_component(hero_id, 'hero')
        stats = em.get_component(hero_id, 'stats')
        inventory = em.get_component(hero_id, 'inventory')
        combat = em.get_component(hero_id, 'combat')
        movement = em.get_component(hero_id, 'movement')
        
        if not hero or not stats:
            return
        
        # Calculate item bonuses
        item_bonus = self._get_item_bonus_stats(inventory)
        
        # Stats box positioning relative to mana bar and skills box
        # Mana bar bottom: port_y + 75, stats box top 5px below = port_y + 80
        # Skills box top: height - 95, stats box bottom 5px above = height - 100
        port_y = self.height - 230
        stats_box_y = port_y + 80  # 5px below mana bar bottom
        stats_box_height = 50  # (height - 100) - (port_y + 80) = 50
        
        # Stats box dimensions (same width as HP/Mana bars)
        port_x = 20
        port_width = 140
        stats_box_x = port_x + port_width + 10  # Aligned with HP/Mana bars
        stats_box_width = 195
        
        # Draw stats box background
        pygame.draw.rect(self.screen, (40, 40, 50), (stats_box_x, stats_box_y, stats_box_width, stats_box_height))
        pygame.draw.rect(self.screen, (100, 100, 120), (stats_box_x, stats_box_y, stats_box_width, stats_box_height), 2)
        
        # Position stats inside the box
        col1_x = stats_box_x + 10  # First column
        col2_x = stats_box_x + 100  # Second column
        row1_y = stats_box_y + 5
        row2_y = stats_box_y + 18
        row3_y = stats_box_y + 31
        
        # Colors
        COLOR_STR = (200, 100, 100)  # Red for strength
        COLOR_AGI = (100, 200, 100)  # Green for agility
        COLOR_INT = (100, 150, 255)  # Blue for intelligence
        COLOR_DMG = (200, 200, 200)  # White for damage
        COLOR_ARMOR = (200, 180, 100)  # Gold for armor
        COLOR_MS = (255, 215, 0)  # Gold for movement speed
        
        # Row 1: STR (col1) | DMG (col2)
        base_str = int(hero.strength)
        bonus_str = int(item_bonus['strength'])
        total_str = base_str + bonus_str
        
        str_text = f"STR: {total_str}"
        if bonus_str > 0:
            str_text += f" (+{bonus_str})"
        
        str_surface = self.font_small.render(str_text, True, COLOR_STR)
        self.screen.blit(str_surface, (col1_x, row1_y))
        
        base_damage = int((combat.damage_min + combat.damage_max) / 2) if combat else 0
        bonus_damage = int(item_bonus['damage'])
        total_damage = base_damage + bonus_damage
        
        dmg_text = f"DMG: {total_damage}"
        if bonus_damage > 0:
            dmg_text += f" (+{bonus_damage})"
        
        dmg_surface = self.font_small.render(dmg_text, True, COLOR_DMG)
        self.screen.blit(dmg_surface, (col2_x, row1_y))
        
        # Row 2: AGI (col1) | ARM (col2)
        base_agi = int(hero.agility)
        bonus_agi = int(item_bonus['agility'])
        total_agi = base_agi + bonus_agi
        
        agi_text = f"AGI: {total_agi}"
        if bonus_agi > 0:
            agi_text += f" (+{bonus_agi})"
        
        agi_surface = self.font_small.render(agi_text, True, COLOR_AGI)
        self.screen.blit(agi_surface, (col1_x, row2_y))
        
        base_armor = int(stats.armor)
        bonus_armor = int(item_bonus['armor'])
        total_armor = base_armor + bonus_armor
        
        armor_text = f"ARM: {total_armor}"
        if bonus_armor > 0:
            armor_text += f" (+{bonus_armor})"
        
        armor_surface = self.font_small.render(armor_text, True, COLOR_ARMOR)
        self.screen.blit(armor_surface, (col2_x, row2_y))
        
        # Row 3: INT (col1) | MS (col2)
        base_int = int(hero.intelligence)
        bonus_int = int(item_bonus['intelligence'])
        total_int = base_int + bonus_int
        
        int_text = f"INT: {total_int}"
        if bonus_int > 0:
            int_text += f" (+{bonus_int})"
        
        int_surface = self.font_small.render(int_text, True, COLOR_INT)
        self.screen.blit(int_surface, (col1_x, row3_y))
        
        base_ms = int(movement.move_speed) if movement else 0
        bonus_ms = int(item_bonus['movement_speed'])
        total_ms = base_ms + bonus_ms
        
        ms_text = f"MS: {total_ms}"
        if bonus_ms > 0:
            ms_text += f" (+{bonus_ms})"
        
        ms_surface = self.font_small.render(ms_text, True, COLOR_MS)
        self.screen.blit(ms_surface, (col2_x, row3_y))
    
    def render_abilities_panel(self):
        """Render abilities with cooldowns"""
        if 0 not in self.game_model.player_heroes:
            return
        
        hero_id = self.game_model.player_heroes[0]
        em = self.game_model.entity_manager
        abilities = em.get_component(hero_id, 'ability')
        
        if not abilities:
            return
        
        ability_x = 20 + 140 + 10
        ability_y = self.height - 95
        ability_size = 45
        spacing = 50
        
        ability_data = [
            ('Q', abilities.q_cooldown, abilities.q_ready),
            ('W', abilities.w_cooldown, abilities.w_ready),
            ('E', abilities.e_cooldown, abilities.e_ready),
            ('R', abilities.r_cooldown, abilities.r_ready)
        ]
        
        for i, (key, cooldown, ready) in enumerate(ability_data):
            x = ability_x + i * spacing
            y = ability_y
            
            color = (50, 200, 50) if ready else (100, 100, 100)
            pygame.draw.rect(self.screen, color, (x, y, ability_size, ability_size))
            pygame.draw.rect(self.screen, (200, 200, 200), (x, y, ability_size, ability_size), 2)
            
            key_text = self.font.render(key, True, (255, 255, 255))
            key_rect = key_text.get_rect(center=(x + ability_size // 2, y + ability_size // 2))
            self.screen.blit(key_text, key_rect)
            
            if not ready:
                cd_text = self.font_small.render(f"{cooldown:.1f}", True, (255, 200, 200))
                cd_rect = cd_text.get_rect(center=(x + ability_size // 2, y + ability_size + 12))
                self.screen.blit(cd_text, cd_rect)
    
    def render_items_panel(self):
        """Render items inventory"""
        if 0 not in self.game_model.player_heroes:
            return
        
        hero_id = self.game_model.player_heroes[0]
        em = self.game_model.entity_manager
        inventory = em.get_component(hero_id, 'inventory')
        
        if not inventory:
            return
        
        item_x = 20 + 140 + 10 + 220
        item_y = self.height - 95 - 50
        item_size = 45
        spacing = 50
        
        for i in range(6):
            x = item_x + (i % 3) * spacing
            y = item_y + (i // 3) * spacing
            
            pygame.draw.rect(self.screen, (60, 60, 70), (x, y, item_size, item_size))
            pygame.draw.rect(self.screen, (150, 150, 150), (x, y, item_size, item_size), 2)
            
            if i < len(inventory.items) and inventory.items[i]:
                item = inventory.items[i]
                
                abbrev = self.item_abbrev.get(item.item_id, '??')
                item_text = self.font_small.render(abbrev, True, (255, 255, 100))
                item_rect = item_text.get_rect(center=(x + item_size // 2, y + item_size // 2))
                self.screen.blit(item_text, item_rect)
                
                if item.has_active and item.current_cooldown > 0:
                    cd_text = self.font_tiny.render(f"{item.current_cooldown:.1f}", True, (255, 200, 200))
                    self.screen.blit(cd_text, (x + 2, y + 2))
    
    def render_gold_and_courier(self, minimap):
        """Render gold and courier button"""
        if 0 not in self.game_model.player_heroes:
            return

        hero_id = self.game_model.player_heroes[0]
        em = self.game_model.entity_manager
        inventory = em.get_component(hero_id, 'inventory')

        if not inventory:
            return

        # Position beside items (right side of items boxes)
        item_x = 20 + 140 + 10 + 220  # Same as in render_items_panel
        gold_x = item_x + 3 * 50 + 45 + 10  # Beside rightmost item
        gold_y = self.height - 95 - 50 + 25  # Align with middle of items

        gold_text = self.font.render(f"Gold: {inventory.gold}", True, (255, 215, 0))
        self.screen.blit(gold_text, (gold_x, gold_y))

        courier_x = gold_x
        courier_y = gold_y + 30
        pygame.draw.rect(self.screen, (80, 80, 100), (courier_x, courier_y, 80, 30))
        pygame.draw.rect(self.screen, (200, 200, 200), (courier_x, courier_y, 80, 30), 2)

        courier_text = self.font_small.render("F3 Courier", True, (255, 255, 255))
        self.screen.blit(courier_text, (courier_x + 5, courier_y + 7))
