"""
HUD renderer for Drift King 2D.
Renders heads-up display (score, speed, combo, time, laps) to pygame surface.
"""

import pygame
from models.game_state import GameState


class HUDRenderer:
    """Renders HUD elements to pygame surface."""
    
    def __init__(self, screen: pygame.Surface):
        """
        Initialize HUD renderer.
        
        Args:
            screen: Pygame surface to render to
        """
        self.screen = screen
        self.font = pygame.font.SysFont(None, 36)
        self.font_small = pygame.font.SysFont(None, 24)
        self.combo_font = pygame.font.SysFont(None, 72)
    
    def render(self, game_state: GameState, speed: float, 
              total_laps: int = 10) -> None:
        """
        Render entire HUD.
        
        Args:
            game_state: Current game state
            speed: Current car speed
            total_laps: Total laps required to complete
        """
        self._render_score(game_state.score)
        self._render_speed(speed)
        self._render_combo(game_state.combo_multiplier)
        self._render_time_laps(game_state.game_time, 
                              game_state.laps_completed, 
                              total_laps)
    
    def _render_score(self, score: float) -> None:
        """Render score display."""
        score_text = self.font.render(f"Score: {int(score)}", True, (0, 0, 0))
        self.screen.blit(score_text, (10, 10))
    
    def _render_speed(self, speed: float) -> None:
        """Render speedometer display."""
        from utils.constants import YELLOW
        speed_text = self.font.render(f"Speed: {int(speed * 10)} km/h", 
                                     True, YELLOW)
        self.screen.blit(speed_text, (10, 40))
    
    def _render_combo(self, multiplier: int) -> None:
        """Render combo multiplier display."""
        from utils.constants import YELLOW
        combo_text = self.font.render(f"Combo: x{multiplier}", 
                                     True, YELLOW)
        self.screen.blit(combo_text, (10, 70))
    
    def _render_time_laps(self, game_time: float, laps: int, 
                          total_laps: int) -> None:
        """Render time and laps display."""
        from utils.constants import BLACK
        time_text = self.font_small.render(f"Time: {game_time:.1f}s", 
                                          True, BLACK)
        laps_text = self.font_small.render(f"Laps: {laps}/{total_laps}", 
                                          True, BLACK)
        self.screen.blit(time_text, (10, 100))
        self.screen.blit(laps_text, (10, 125))
    
    def _render_combo_flash(self, combo_text: str, flash_timer: int) -> None:
        """Render flashing combo display when multiplier increases."""
        if flash_timer > 0 and combo_text:
            from utils.constants import SCREEN_WIDTH, SCREEN_HEIGHT
            flash_alpha = 255 if (flash_timer // 6) % 2 == 0 else 128
            flash_color = (255, 255 - flash_alpha // 2, 0)
            combo_flash = self.combo_font.render(combo_text, True, flash_color)
            tw, th = combo_flash.get_size()
            self.screen.blit(
                combo_flash, 
                (SCREEN_WIDTH // 2 - tw // 2, SCREEN_HEIGHT // 2 - th // 2)
            )
    
    def render_game_over(self, final_score: float) -> None:
        """
        Render game over screen.
        
        Args:
            final_score: Final game score
        """
        from utils.constants import RED, SCREEN_WIDTH, SCREEN_HEIGHT
        final_text = self.font.render(
            "Game Over! Press R to restart", 
            True, RED
        )
        self.screen.blit(
            final_text, 
            (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2)
        )


def draw_score(score: float, game_time: float = 0, laps: int = 0) -> None:
    """
    Legacy function for compatibility.
    
    Args:
        score: Current score
        game_time: Elapsed game time
        laps: Laps completed
    """
    pass  # Legacy function - no longer needed with new HUD
