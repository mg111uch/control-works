"""
Menu renderer for track selection screen.
"""

import pygame
from typing import List, Dict, Optional


class MenuRenderer:
    """Renderer for the pre-game menu screen."""
    
    def __init__(self, screen: pygame.Surface):
        """
        Initialize menu renderer.
        
        Args:
            screen: Pygame surface to render on
        """
        self.screen = screen
        self.font_title = pygame.font.SysFont(None, 48)
        self.font_option = pygame.font.SysFont(None, 32)
        self.font_info = pygame.font.SysFont(None, 24)
        
        # Colors
        self.COLOR_TITLE = (255, 255, 255)
        self.COLOR_OPTION = (200, 200, 200)
        self.COLOR_SELECTED = (255, 215, 0)  # Gold
        self.COLOR_BACKGROUND = (30, 30, 30)
        self.COLOR_BORDER = (100, 100, 100)
    
    def render(self, tracks: List[Dict], selected_index: int,
               screen_width: int = 800, screen_height: int = 600) -> None:
        """
        Render the menu screen.
        
        Args:
            tracks: List of track info dictionaries
            selected_index: Currently selected track index
            screen_width: Screen width
            screen_height: Screen height
        """
        # Fill background
        self.screen.fill(self.COLOR_BACKGROUND)
        
        # Draw title
        title_text = self.font_title.render("Drift King 2D", True, self.COLOR_TITLE)
        title_rect = title_text.get_rect(center=(screen_width // 2, 80))
        self.screen.blit(title_text, title_rect)
        
        # Draw subtitle
        subtitle_text = self.font_option.render("Select a Track", True, self.COLOR_OPTION)
        subtitle_rect = subtitle_text.get_rect(center=(screen_width // 2, 130))
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # Draw track options
        start_y = 200
        spacing = 50
        
        for i, track in enumerate(tracks):
            y_pos = start_y + i * spacing
            
            # Highlight selected track
            if i == selected_index:
                color = self.COLOR_SELECTED
                # Draw selection indicator
                indicator = self.font_option.render(">", True, color)
                self.screen.blit(indicator, (screen_width // 2 - 150, y_pos))
            else:
                color = self.COLOR_OPTION
            
            # Track name
            name_text = self.font_option.render(track['name'], True, color)
            name_rect = name_text.get_rect(center=(screen_width // 2, y_pos))
            self.screen.blit(name_text, name_rect)
            
            # Difficulty badge
            difficulty = track.get('difficulty', 'unknown')
            diff_color = self._get_difficulty_color(difficulty)
            diff_text = self.font_info.render(f"({difficulty})", True, diff_color)
            diff_rect = diff_text.get_rect(midleft=(name_rect.right + 20, y_pos))
            self.screen.blit(diff_text, diff_rect)
        
        # Draw instructions
        instructions = [
            "Use UP/DOWN arrows to select track",
            "Press ENTER to start",
            "Press ESC to quit"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.font_info.render(instruction, True, (150, 150, 150))
            text_rect = text.get_rect(center=(screen_width // 2, screen_height - 80 + i * 25))
            self.screen.blit(text, text_rect)
        
        # Draw border
        pygame.draw.rect(
            self.screen, 
            self.COLOR_BORDER,
            (50, 50, screen_width - 100, screen_height - 100),
            2
        )
        
        # Update display
        pygame.display.flip()
    
    def _get_difficulty_color(self, difficulty: str):
        """Get color for difficulty badge."""
        colors = {
            'easy': (100, 255, 100),      # Green
            'medium': (255, 255, 100),    # Yellow
            'hard': (255, 100, 100),      # Red
            'expert': (255, 100, 255),    # Magenta
        }
        return colors.get(difficulty.lower(), (200, 200, 200))
