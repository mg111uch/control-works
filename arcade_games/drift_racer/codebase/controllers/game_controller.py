"""
Game controller for Drift King 2D.
Main game loop controller that orchestrates models, views, and input.
"""

import sys
import os
import pygame
from typing import Optional, Tuple

from models.car import Car
from models.track import Track
from models.game_state import GameState
from controllers.input_controller import InputController
from views.track_renderer import TrackRenderer
from views.car_renderer import CarRenderer
from views.hud_renderer import HUDRenderer


class GameController:
    """
    Main game loop controller.
    
    Orchestrates the game by coordinating models, views, and input.
    """
    
    def __init__(self, track: Track, headless: bool = False, 
                 screen: Optional[pygame.Surface] = None):
        """
        Initialize game controller.
        
        Args:
            track: Track to play on
            headless: Whether to run without display
            screen: Optional pygame surface (created if None)
        """
        self.track = track
        self.headless = headless
        
        # Initialize pygame display if not headless
        if not headless:
            # Set window position before initializing pygame
            os.environ['SDL_VIDEO_WINDOW_POS'] = '0,0'
            pygame.init()
            if screen is None:
                self.screen = pygame.display.set_mode(
                    (track.screen_width, track.screen_height),
                    pygame.HWSURFACE | pygame.DOUBLEBUF
                )
                pygame.display.set_caption("Drift King 2D")
            else:
                self.screen = screen
            self.clock = pygame.time.Clock()
        
        # Initialize models
        start_x, start_y, start_angle = track.get_start_position()
        self.car = Car(start_x, start_y, start_angle)
        self.car.set_track(track)  # Enable ray casting
        self.game_state = GameState(track)
        
        # Initialize input controller
        self.input_controller = InputController()
        
        # Initialize renderers (only if not headless)
        if not headless:
            self.track_renderer = TrackRenderer(self.screen)
            self.car_renderer = CarRenderer()
            self.hud_renderer = HUDRenderer(self.screen)
    
    def reset(self) -> None:
        """Reset game to initial state."""
        start_x, start_y, start_angle = self.track.get_start_position()
        self.car = Car(start_x, start_y, start_angle)
        self.car.set_track(self.track)  # Enable ray casting
        self.game_state.reset()
        self._last_step_off_track_death = False  # Track off-track deaths
    
    def step(self, action: int) -> Tuple:
        """
        Take a single step in the game.
        
        Args:
            action: Action code (0-8)
            
        Returns:
            Tuple of (state, reward, done)
        """
        # Decode action
        (accelerate, turn_left, turn_right, 
         drift, brake) = self.input_controller.decode_action(action)
        
        # Update car
        self.car.update(accelerate, turn_left, turn_right, drift, brake)
        
        # Check if on track
        on_track = self.track.is_on_track(self.car.x, self.car.y)
        
        # Track if this step caused off-track death
        was_off_track = not on_track
        
        # Get forward progress and drift angle for reward calculation
        forward_progress = self.car.get_forward_progress()
        drift_angle = self.car.drift_angle
        
        # Update game state with new parameters
        reward = self.game_state.update(
            self.car.x, self.car.y, on_track, drift, self.car.speed,
            drift_angle=drift_angle, forward_progress=forward_progress
        )
        
        # Get state for AI
        state = self.car.get_state()
        
        # Track if episode ended due to off-track
        self._last_step_off_track_death = was_off_track and self.game_state.done
        
        return state, reward, self.game_state.done
    
    def run(self) -> None:
        """Run the main game loop."""
        if self.headless:
            raise ValueError("Cannot run() in headless mode")
        
        while True:
            self._handle_events()
            
            # Get action from input
            action = self.input_controller.get_action()
            
            # Take step
            state, reward, done = self.step(action)
            self.game_state.update_combo_flash()
            
            # Render
            self._render()
            
            # Check for game over
            if done:
                self._render_game_over()
            
            # Cap at 60 FPS
            self.clock.tick(60)
    
    def _handle_events(self) -> None:
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.reset()
    
    def _render(self) -> None:
        """Render the game."""
        if self.headless:
            return
        
        # Clear screen
        self.screen.fill(self.track.background_color)
        
        # Draw track
        self.track_renderer.render(self.track)
        
        # Draw car
        self.car_renderer.render(self.car, self.screen)
        
        # Draw HUD
        self.hud_renderer.render(
            self.game_state, 
            self.car.speed,
            self.game_state.total_laps
        )
        
        # Update display
        pygame.display.flip()
    
    def _render_game_over(self) -> None:
        """Render game over screen."""
        if self.headless:
            return
        
        final_text = pygame.font.SysFont(None, 36).render(
            "Game Over! Press R to restart", 
            True, (255, 0, 0)
        )
        tw, th = final_text.get_size()
        self.screen.blit(
            final_text, 
            (self.track.screen_width // 2 - tw // 2, 
             self.track.screen_height // 2)
        )
        pygame.display.flip()
    
    @property
    def score(self) -> float:
        """Get current score."""
        return self.game_state.score
    
    @property
    def speed(self) -> float:
        """Get current car speed."""
        return self.car.speed
    
    @property
    def laps_completed(self) -> int:
        """Get laps completed."""
        return self.game_state.laps_completed
    
    @property
    def ticks(self) -> int:
        """Get game ticks."""
        return self.game_state.ticks


class GameEnv:
    """
    Game environment for neural network training.
    
    This class provides a simplified interface for AI training,
    compatible with the original drift_king_2d.py interface.
    """
    
    def __init__(self, headless: bool = False, track: Optional[Track] = None):
        """
        Initialize game environment.
        
        Args:
            headless: Whether to run without display
            track: Optional track (loads default if None)
        """
        self.headless = headless
        
        # Load default track if none provided
        if track is None:
            from controllers.track_loader import TrackLoader
            loader = TrackLoader()
            track = loader.load_default_track()
        
        self.track = track
        
        # Initialize controller
        self.controller = GameController(track, headless=headless)
    
    def reset(self):
        """Reset the environment to initial state."""
        self.controller.reset()
        return self.controller.car.get_state()
    
    def step(self, action: int):
        """
        Take a step in the environment.
        
        Args:
            action: Action code (0-8)
            
        Returns:
            Tuple of (state, reward, done)
        """
        return self.controller.step(action)
    
    def render(self):
        """Render the environment."""
        if not self.headless:
            self.controller._render()
    
    @property
    def score(self):
        """Get current score."""
        return self.controller.score
    
    @property
    def speed(self):
        """Get current speed."""
        return self.controller.speed
    
    @property
    def laps_completed(self):
        """Get laps completed."""
        return self.controller.laps_completed
    
    @property
    def ticks(self):
        """Get game ticks."""
        return self.controller.ticks
    
    @property
    def combo_multiplier(self):
        """Get current combo multiplier."""
        return self.controller.game_state.combo_multiplier
    
    @property
    def combo_text(self):
        """Get combo text."""
        return self.controller.game_state.combo_text
    
    @property
    def combo_flash_timer(self):
        """Get combo flash timer."""
        return self.controller.game_state.combo_flash_timer
    
    @property
    def game_time(self):
        """Get elapsed game time."""
        return self.controller.game_state.game_time
    
    def update_combo_flash(self):
        """Update combo flash timer."""
        self.controller.game_state.update_combo_flash()
    
    @property
    def off_track_death(self):
        """Get whether last episode ended due to off-track death."""
        return self.controller._last_step_off_track_death
    
    @property
    def car(self):
        """Get the car object (for rendering)."""
        return self.controller.car
