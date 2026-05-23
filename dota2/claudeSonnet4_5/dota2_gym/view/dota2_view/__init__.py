"""
Dota2 View Module
Modularized view system for Dota2-style rendering.

Modules:
- camera: Camera and coordinate conversion
- entities: Entity rendering (towers, creeps, heroes, projectiles)
- ui: UI rendering (minimap, portrait, abilities, items, stats)
- menus: Shop and pause menu rendering
- dota2_view: Main Dota2View class
"""

from .dota2_view import Dota2View

__all__ = ['Dota2View']
