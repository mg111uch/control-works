# engine/controller/human_controller.py
import pygame
import numpy as np
from ..model.ecs.entity import Component


class MoveTarget(Component):
    def __init__(self, x, y):
        self.value = np.array([x, y], dtype=np.float32)


class HumanController:
    def __init__(self, model, player_id, view=None):
        self.model = model
        self.player_id = player_id
        self.view = view
        self.current_input = {
            "move_target": None,
            "attack_move": False,
            "cast_raze": None,
            "cast_requiem": False,
            "use_item": None,
            "stop": False
        }

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:  # Right click
            # Set move target for hero
            hero = self.find_hero()
            if hero:
                world_pos = self.screen_to_world(event.pos)
                hero.add_component("move_target", MoveTarget(world_pos[0], world_pos[1]))

    def screen_to_world(self, screen_pos):
        if self.view:
            return self.view.screen_to_world(screen_pos[0], screen_pos[1])
        else:
            # Fallback
            return np.array([screen_pos[0] * 100, screen_pos[1] * 100], dtype=np.float32)

    def find_hero(self):
        # Find hero by player_id
        for entity in self.model.entities.all():
            if hasattr(entity, 'player_id') and entity.player_id == self.player_id:
                return entity
        return None