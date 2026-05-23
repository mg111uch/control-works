# engine/view/pygame_view.py
import pygame
import numpy as np
from pygame import surfarray
from .renderer_interface import RendererInterface


class PygameView(RendererInterface):
    """Renderer – draws everything using simple shapes. Fully replaceable."""
    def __init__(self, screen, model):
        super().__init__(width=1280, height=720)
        self.screen = screen
        self.model = model
        self.camera_target = self.camera_pos.copy()
        self.minimap_surface = pygame.Surface((200, 200))

        # Colors
        self.colors = {
            0: (0, 255, 0),      # Radiant green
            1: (255, 0, 0),      # Dire red
            "creep": (150, 150, 150),
            "tower": (200, 200, 200),
            "projectile": (255, 200, 0),
            "rune": (255, 255, 0),
            "fog": (0, 0, 0, 180)
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

    def world_to_screen(self, world_pos):
        rel = world_pos - self.camera_pos
        scale = 0.08
        x = 640 + rel[0] * scale
        y = 360 + rel[1] * scale
        return int(x), int(y)

    def render(self):
        self.screen.fill((30, 30, 30))  # dark ground

        self.keys = pygame.key.get_pressed()

        # Camera follow player 0 (for now)
        hero0 = next((e for e in self.model.entities.all() if getattr(e, "player_id", -1) == 0), None)
        if hero0 and hero0.get_component("position"):
            target = hero0.get_component("position").value
            self.camera_target = target
            self.camera_pos += (self.camera_target - self.camera_pos) * 0.1

        # Render entities
        for ent in self.model.entities.all():
            if not hasattr(ent, "get_component") or not ent.get_component("position"):
                continue
            pos = ent.get_component("position").value
            sx, sy = self.world_to_screen(pos)

            if "hero" in str(type(ent)).lower():
                color = self.colors[ent.team]
                pygame.draw.circle(self.screen, color, (sx, sy), 20)
                # Attack range
                range_val = ent.get_attack_range()
                pygame.draw.circle(self.screen, (*color, 80), (sx, sy), int(range_val * 0.08), 1)
            elif "creep" in str(type(ent)):
                pygame.draw.circle(self.screen, self.colors["creep"], (sx, sy), 12)
            elif "tower" in str(type(ent)):
                pygame.draw.rect(self.screen, self.colors["tower"], (sx-25, sy-25, 50, 50))
            elif "projectile" in str(type(ent)):
                pygame.draw.circle(self.screen, self.colors["projectile"], (sx, sy), 8)

        # HUD
        font = pygame.font.SysFont(None, 24)
        time_text = font.render(f"Time: {self.model.game_time:.0f}s", True, (255,255,255))
        self.screen.blit(time_text, (10, 10))

        if self.model.winner is not None:
            win_text = font.render(f"PLAYER {self.model.winner} WINS!", True, (255,255,0))
            self.screen.blit(win_text, (500, 300))

        # Minimap
        self.minimap_surface.fill((20,20,20))
        for ent in self.model.entities.all():
            if not hasattr(ent, "get_component"): continue
            pos = ent.get_component("position").value if ent.get_component("position") else None
            if pos is None: continue
            mx = int(pos[0] / 16000 * 200)
            my = int(pos[1] / 14400 * 200)
            color = (0,255,0) if getattr(ent, "team", -1) == 0 else (255,0,0)
            if "hero" in str(type(ent)):
                pygame.draw.circle(self.minimap_surface, color, (mx,my), 4)
        self.screen.blit(self.minimap_surface, (1070, 520))

        # Simple shop toggle (F1)
        if self.keys[pygame.K_F1]:
            self.model.systems["item"].shop_open = not self.model.systems["item"].shop_open

        if self.model.systems["item"].shop_open:
            # Draw item list
            for i, (name, item) in enumerate(self.model.systems["item"].items_db.items()):
                text = font.render(f"{name} - {item.cost}g", True, (255,255,255))
                self.screen.blit(text, (10, 100 + i*30))

        if self.model.winner is not None:
            font = pygame.font.SysFont(None, 48)
            win_text = font.render(f"Player {self.model.winner} WINS!", True, (255, 255, 0))
            self.screen.blit(win_text, (400, 200))

            # Scoreboard
            sb = self.model.scoreboard
            y = 300
            for pid, stats in sb.items():
                text = font.render(f"P{pid}: {stats['kills']}/{stats['deaths']}/{stats['assists']} CS:{stats['cs']} G:{stats['gold']}", True, (255,255,255))
                self.screen.blit(text, (400, y))
                y += 40

        # Fog overlay
        for pid in [0]:  # Player 0 view
            fog = self.model.fog_of_war[pid]
            fog_surf = pygame.surfarray.make_surface((fog * 255).astype(np.uint8).T)
            fog_surf.set_alpha(180)
            fog_surf = pygame.transform.scale(fog_surf, (1280, 720))
            self.screen.blit(fog_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)