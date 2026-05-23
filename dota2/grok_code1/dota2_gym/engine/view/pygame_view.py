# engine/view/pygame_view.py
import pygame
import numpy as np
from .renderer_interface import RendererInterface


class PygameView(RendererInterface):
    """Renderer – draws everything using simple shapes. Fully replaceable."""
    def __init__(self, screen, model):
        super().__init__(width=1280, height=720)
        self.screen = screen
        self.model = model
        self.camera_target = self.camera_pos.copy()

        # Colors
        self.colors = {
            0: (0, 255, 0),      # Radiant green
            1: (255, 0, 0),      # Dire red
            "entity": (255, 255, 255),
            "target": (255, 0, 255)
        }

    def init(self):
        pass

    def handle_events(self):
        return True

    def get_surface(self):
        return self.screen

    def flip(self):
        pygame.display.flip()

    def close(self):
        pygame.quit()

    def render(self):
        self.screen.fill((30, 30, 30))  # dark background

        # For demo, don't follow camera
        # self.camera_pos[:] = self.camera_target

        # Render entities
        for ent in self.model.entities.all():
            pos_comp = ent.get_component("position")
            if pos_comp:
                pos = pos_comp.value
                sx, sy = self.world_to_screen(pos)
                pygame.draw.circle(self.screen, self.colors["entity"], (sx, sy), 20)

                # If has move_target, draw target
                target_comp = ent.get_component("move_target")
                if target_comp:
                    tx, ty = self.world_to_screen(target_comp.value)
                    pygame.draw.circle(self.screen, self.colors["target"], (tx, ty), 10, 2)
                    pygame.draw.line(self.screen, (255, 255, 255), (sx, sy), (tx, ty), 2)

        # HUD
        font = pygame.font.SysFont(None, 24)
        time_text = font.render(f"Time: {self.model.game_time:.0f}s", True, (255,255,255))
        self.screen.blit(time_text, (10, 10))