# engine/controller/ai_controller.py
import numpy as np
import random
from typing import Dict, Any, Optional


class RandomAIController:
    """
    Simple random AI controller for Shadow Fiend.
    Used as opponent in training or demo mode.
    Acts every ~1–3 seconds with random valid actions.
    """
    def __init__(self, model, player_id: int = 1):
        self.model = model
        self.player_id = player_id
        self.hero: Optional[Any] = None
        self.action_timer = 0.0
        self.next_action_delay = random.uniform(0.8, 2.5)

        # Current input state (same format as HumanController)
        self.current_input: Dict[str, Any] = {
            "move_target": None,
            "attack_move": False,
            "cast_raze": None,
            "cast_requiem": False,
            "use_item": None,
            "stop": False
        }

    def find_hero(self):
        if self.hero is None:
            for ent in self.model.entities.all():
                if getattr(ent, "player_id", -1) == self.player_id and hasattr(ent, "cast_raze"):
                    self.hero = ent
                    break

    def update(self, dt: float):
        self.find_hero()
        if not self.hero:
            return

        self.action_timer += dt
        if self.action_timer < self.next_action_delay:
            return

        self.action_timer = 0.0
        self.next_action_delay = random.uniform(0.6, 2.2)

        # Reset previous input
        self.current_input = {k: None for k in self.current_input}
        self.current_input["attack_move"] = False
        self.current_input["cast_requiem"] = False
        self.current_input["stop"] = False

        action_type = random.choices(
            ["move", "raze", "requiem", "item", "stop"],
            weights=[50, 25, 5, 15, 5], k=1
        )[0]

        hero_pos = self.hero.get_component("position").value

        if action_type == "move":
            # Random point around hero
            angle = random.uniform(0, 2 * np.pi)
            distance = random.uniform(200, 1200)
            target = hero_pos + np.array([np.cos(angle), np.sin(angle)]) * distance
            target[0] = np.clip(target[0], 500, 15500)
            target[1] = np.clip(target[1], 500, 13900)
            self.current_input["move_target"] = target
            self.current_input["attack_move"] = random.random() < 0.4

        elif action_type == "raze":
            if all(self.hero.cooldowns[k] == 0 for k in ["raze_short", "raze_medium", "raze_long"]):
                raze_type = random.choice(["short", "medium", "long"])
                self.current_input["cast_raze"] = raze_type

        elif action_type == "requiem" and self.hero.cooldowns["requiem"] <= 0:
            if self.hero.get_component("mana").current >= 150:
                self.current_input["cast_requiem"] = True

        elif action_type == "item":
            inv = self.hero.get_component("inventory")
            usable_items = [i for i, item in enumerate(inv.slots) if item]
            if usable_items:
                slot = random.choice(usable_items)
                self.current_input["use_item"] = slot

        elif action_type == "stop":
            self.current_input["stop"] = True

    def get_current_input(self) -> Dict[str, Any]:
        """Used by systems that read controller input"""
        return self.current_input.copy()