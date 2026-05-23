# engine/view/renderer_interface.py
"""
RendererInterface – Abstract base class for all rendering backends
Purpose:
  • Decouple GameModel from any specific graphics library (Pygame, WebGL, Matplotlib, etc.)
  • Enable headless training, unit testing, video recording, web deployment
  • Define exact contract that every View must implement
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Any
import numpy as np


class RendererInterface(ABC):
    """
    All renderers (PygameView, WebView, etc.) must inherit from this.
    GameModel only talks to this interface.
    """

    def __init__(self, width: int = 1280, height: int = 720):
        self.width = width
        self.height = height
        self.camera_pos = np.array([8000.0, 7200.0], dtype=np.float32)  # World center
        self.camera_zoom = 1.0
        self.is_headless = False

    # ------------------------------------------------------------------
    # Required abstract methods – must be implemented by child class
    # ------------------------------------------------------------------

    @abstractmethod
    def init(self) -> None:
        """Initialize window/surface/context (called once)"""
        pass

    @abstractmethod
    def render(self) -> None:
        """Draw one frame – called every tick when visible"""
        pass

    @abstractmethod
    def handle_events(self) -> bool:
        """
        Process input events.
        Return False if quit requested.
        """
        pass

    @abstractmethod
    def get_surface(self) -> Any:
        """Return the raw drawing surface (Pygame Surface, Cairo context, etc.)"""
        pass

    @abstractmethod
    def flip(self) -> None:
        """Present the frame (swap buffers)"""
        pass

    @abstractmethod
    def close(self) -> None:
        """Clean shutdown"""
        pass

    # ------------------------------------------------------------------
    # Helper methods – shared logic, can be overridden
    # ------------------------------------------------------------------

    def world_to_screen(self, world_pos: np.ndarray) -> Tuple[int, int]:
        """Convert world coordinates → screen pixels (shared by all renderers)"""
        rel = world_pos - self.camera_pos
        scale = 0.08 * self.camera_zoom  # Base scale + zoom
        x = self.width // 2 + rel[0] * scale
        y = self.height // 2 + rel[1] * scale
        return int(x), int(y)

    def screen_to_world(self, screen_x: int, screen_y: int) -> np.ndarray:
        """Inverse of world_to_screen – used for mouse clicks"""
        scale = 0.08 * self.camera_zoom
        rel_x = (screen_x - self.width // 2) / scale
        rel_y = (screen_y - self.height // 2) / scale
        return self.camera_pos + np.array([rel_x, rel_y], dtype=np.float32)

    def set_camera(self, pos: np.ndarray, zoom: float = 1.0) -> None:
        """Smooth camera follow (used by controllers)"""
        self.camera_pos[:] = pos
        self.camera_zoom = zoom

    def draw_circle(self, world_pos: np.ndarray, radius: float, color: Tuple[int, int, int], alpha: int = 255, fill: bool = False):
        """Convenience – implemented in child classes if needed"""
        pass

    def draw_line(self, start: np.ndarray, end: np.ndarray, color: Tuple[int, int, int], width: int = 2):
        pass

    def draw_text(self, text: str, world_pos: np.ndarray, color: Tuple[int, int, int], size: int = 24):
        pass

    def draw_minimap(self, entities: list, player_id: int = 0):
        """Standard minimap in bottom-right"""
        pass

    def draw_fog_of_war(self, fog_grid: np.ndarray):
        """Black overlay where fog exists"""
        pass

    # ------------------------------------------------------------------
    # Optional lifecycle hooks
    # ------------------------------------------------------------------

    def on_game_start(self, model) -> None:
        """Called when new game begins"""
        self.model = model

    def on_game_end(self, winner: int) -> None:
        """Post-game screen"""
        pass

    def on_resize(self, width: int, height: int) -> None:
        """Window resized"""
        self.width = width
        self.height = height