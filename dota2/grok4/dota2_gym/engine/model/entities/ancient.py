# engine/model/entities/ancient.py
import numpy as np
from ..ecs.entity import Entity, Component


class AncientHealth(Component):
    def __init__(self, max_hp: float):
        self.current = max_hp
        self.maximum = max_hp


class Ancient(Entity):
    """Ancient entity – the throne, win condition target"""
    def __init__(self, model, team: int, position: np.ndarray):
        super().__init__(model)
        self.team = team

        hp = model.constants["towers"]["ancient_hp"]
        self.add_component("position", type("Pos", (), {"value": position.copy()}))
        self.add_component("health", AncientHealth(hp))

        # Ancient attacks nearby enemies (high damage)
        self.add_component("attack", type("Attack", (), {
            "damage": 150,
            "range": 900,
            "cooldown": 2.0,
            "next_attack_time": 0.0
        }))

    def serialize(self) -> dict:
        pos = self.get_component("position").value
        hp = self.get_component("health").current
        return {
            "id": self.id,
            "type": "ancient",
            "team": self.team,
            "position": pos.tolist(),
            "hp": hp
        }