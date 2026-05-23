# engine/model/entities/tower.py
import numpy as np
from ..ecs.entity import Entity, Component


class TowerHealth(Component):
    def __init__(self, max_hp: float):
        self.current = max_hp
        self.maximum = max_hp


class TowerAttack(Component):
    def __init__(self, damage: float, range: float, cooldown: float):
        self.damage = damage
        self.range = range
        self.cooldown = cooldown
        self.next_attack_time = 0.0


class Tower(Entity):
    """Tower entity – T1/T2/T3 with health & auto-attack"""
    def __init__(self, model, team: int, tier: int, position: np.ndarray):
        super().__init__(model)
        self.team = team
        self.tier = tier

        # Stats from constants
        hp = model.constants["towers"][f"tier{tier}_hp"]
        self.add_component("position", type("Pos", (), {"value": position.copy()}))
        self.add_component("health", TowerHealth(hp))
        self.add_component("attack", TowerAttack(
            model.constants["towers"]["damage"],
            model.constants["towers"]["attack_range"],
            model.constants["towers"]["attack_cooldown"]
        ))

    def serialize(self) -> dict:
        pos = self.get_component("position").value
        hp = self.get_component("health").current
        return {
            "id": self.id,
            "type": "tower",
            "team": self.team,
            "tier": self.tier,
            "position": pos.tolist(),
            "hp": hp
        }