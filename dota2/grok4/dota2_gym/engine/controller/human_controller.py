# engine/controller/human_controller.py
import pygame
import numpy as np
from typing import Dict, Any, Optional


class HumanController:
    """
    Handles all human input (keyboard + mouse) and translates it into game actions.
    Works with classic Dota-style controls:
      - Right-click → move / attack-move
      - Q / W / E → Shadow Raze (short / medium / long)
      - R → Requiem of Souls
      - 1–6 → Use items
      - Edge panning + middle-mouse drag
    """
    def __init__(self, model, player_id: int = 0):
        self.model = model
        self.player_id = player_id
        self.hero = None

        # Current input state (updated every frame)
        self.current_input: Dict[str, Any] = {
            "move_target": None,       # world position (np.array)
            "attack_move": False,
            "cast_raze": None,         # "short", "medium", "long" or None
            "cast_requiem": False,
            "use_item": None,          # 0–5 or None
            "stop": False
        }

        # Camera control
        self.camera_speed = 800.0
        self.dragging = False
        self.last_mouse_pos = None

        # Key mapping
        self.keys = {
            pygame.K_q: "raze_short",
            pygame.K_w: "raze_medium",
            pygame.K_e: "raze_long",
            pygame.K_r: "requiem",
            pygame.K_1: "item_0",
            pygame.K_2: "item_1",
            pygame.K_3: "item_2",
            pygame.K_4: "item_3",
            pygame.K_5: "item_4",
            pygame.K_6: "item_5",
            pygame.K_s: "stop",
            pygame.K_SPACE: "stop",
        }

    def find_hero(self):
        """Cache reference to controlled hero"""
        if self.hero is None:
            for ent in self.model.entities.all():
                if getattr(ent, "player_id", -1) == self.player_id and hasattr(ent, "cast_raze"):
                    self.hero = ent
                    break

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3:  # Right click
                mx, my = event.pos
                world_x, world_y = self.screen_to_world(mx, my)
                self.current_input["move_target"] = np.array([world_x, world_y])
                self.current_input["attack_move"] = pygame.key.get_mods() & pygame.KMOD_SHIFT

            elif event.button == 2:  # Middle mouse drag
                self.dragging = True
                self.last_mouse_pos = pygame.mouse.get_pos()

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 2:
                self.dragging = False
                self.last_mouse_pos = None

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging and self.last_mouse_pos:
                dx, dy = event.pos[0] - self.last_mouse_pos[0], event.pos[1] - self.last_mouse_pos[1]
                # Move camera opposite to drag
                from engine.view.pygame_view import PygameView
                view = None
                for obj in pygame.display.get_surface()._view_ref:
                    if isinstance(obj, PygameView):
                        view = obj
                        break
                if view:
                    view.camera_pos[0] -= dx / 0.08
                    view.camera_pos[1] -= dy / 0.08
                self.last_mouse_pos = event.pos

        elif event.type == pygame.KEYDOWN:
            action = self.keys.get(event.key)
            if action:
                if action.startswith("raze_"):
                    self.current_input["cast_raze"] = action[5:]  # short/medium/long
                elif action == "requiem":
                    self.current_input["cast_requiem"] = True
                elif action.startswith("item_"):
                    slot = int(action[5:])
                    self.current_input["use_item"] = slot
                elif action == "stop":
                    self.current_input["stop"] = True

        elif event.type == pygame.KEYUP:
            # Reset one-time actions
            if event.key in (pygame.K_q, pygame.K_w, pygame.K_e):
                self.current_input["cast_raze"] = None
            if event.key == pygame.K_r:
                self.current_input["cast_requiem"] = False
            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6):
                self.current_input["use_item"] = None
            if event.key in (pygame.K_s, pygame.K_SPACE):
                self.current_input["stop"] = False

    def screen_to_world(self, screen_x: int, screen_y: int) -> tuple:
        """Convert screen pixel to world coordinate using current camera"""
        from engine.view.pygame_view import PygameView
        view = None
        for obj in pygame.display.get_surface()._view_ref:
            if isinstance(obj, PygameView):
                view = obj
                break
        if not view:
            return screen_x, screen_y

        rel_x = (screen_x - 640) / 0.08
        rel_y = (screen_y - 360) / 0.08
        world_x = view.camera_pos[0] + rel_x
        world_y = view.camera_pos[1] + rel_y
        return world_x, world_y

    def update(self, dt: float):
        """Called every tick – edge panning + send input to hero"""
        self.find_hero()
        if not self.hero:
            return

        # Edge panning
        mx, my = pygame.mouse.get_pos()
        pan_speed = self.camera_speed * dt
        from engine.view.pygame_view import PygameView
        view = None
        for obj in pygame.display.get_surface()._view_ref:
            if isinstance(obj, PygameView):
                view = obj
                break
        if view:
            if mx < 50: view.camera_pos[0] -= pan_speed
            if mx > 1230: view.camera_pos[0] += pan_speed
            if my < 50: view.camera_pos[1] -= pan_speed
            if my > 670: view.camera_pos[1] += pan_speed

        # Process commands
        if self.current_input["move_target"] is not None:
            direction = self.current_input["move_target"] - self.hero.get_component("position").value
            if np.linalg.norm(direction) > 10:
                direction = direction / np.linalg.norm(direction)
            else:
                direction = np.zeros(2)
            self.hero.get_component("velocity").value = direction * self.hero.get_move_speed()

        if self.current_input["cast_raze"]:
            # self.hero.cast_raze(self.current_input["cast_raze"])
            self.model.systems["ability"].handle_ability_input(self.hero, f"raze_{self.current_input['cast_raze']}")

        if self.current_input["cast_requiem"]:
            # self.hero.cast_requiem()
            self.model.systems["ability"].handle_ability_input(self.hero, "requiem")

        if self.current_input["use_item"] is not None:
            inv = self.hero.get_component("inventory")
            if inv and 0 <= self.current_input["use_item"] < 6:
                item = inv.slots[self.current_input["use_item"]]
                if item:
                    # Placeholder – will be expanded in ItemSystem
                    pass

        if self.current_input["stop"]:
            self.hero.get_component("velocity").value = np.zeros(2)