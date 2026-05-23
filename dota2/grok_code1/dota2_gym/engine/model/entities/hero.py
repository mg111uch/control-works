# engine/model/entities/hero.py
import numpy as np
from typing import Dict, List, Optional, TYPE_CHECKING
from ..ecs.entity import Entity, Component

if TYPE_CHECKING:
    from ..game_model import GameModel


class Position(Component):
    def __init__(self, x: float, y: float):
        super().__init__(value=np.array([x, y], dtype=np.float32))


class Velocity(Component):
    def __init__(self):
        super().__init__(value=np.zeros(2, dtype=np.float32))


class Facing(Component):
    def __init__(self, angle: float = 0.0):
        super().__init__(angle=angle)  # radians, 0 = right


class Health(Component):
    def __init__(self, max_hp: float):
        super().__init__(current=max_hp, maximum=max_hp)


class Mana(Component):
    def __init__(self, max_mana: float):
        super().__init__(current=max_mana, maximum=max_mana)


class Stats(Component):
    """Flat bonuses from items / level"""
    def __init__(self):
        super().__init__(
            strength=0.0,
            agility=0.0,
            intelligence=0.0,
            attack_damage=0.0,
            attack_speed=0.0,
            armor=0.0,
            move_speed_bonus=0.0
        )


class Inventory(Component):
    def __init__(self):
        super().__init__(slots=[None] * 6, gold=600)


class Souls(Component):
    """Necromastery"""
    def __init__(self):
        super().__init__(current=0, max=40)


class Hero(Entity):
    def __init__(self, model: "GameModel", player_id: int, team: int, position, data: dict):
        super().__init__(model)
        self.player_id = player_id
        self.team = team  # 0 = radiant, 1 = dire

        # Base from config
        base = data["base_stats"]
        self.level = 1
        self.exp = 0

        # Components
        self.add_component("position", Position(position[0], position[1]))
        self.add_component("velocity", Velocity())
        self.add_component("facing", Facing(0.0))
        self.add_component("health", Health(self._calc_max_hp(base)))
        self.add_component("mana", Mana(self._calc_max_mana(base)))
        self.add_component("stats", Stats())
        self.add_component("inventory", Inventory())
        self.add_component("souls", Souls())

        # Ability cooldowns
        self.cooldowns = {
            "raze_short": 0.0,
            "raze_medium": 0.0,
            "raze_long": 0.0,
            "requiem": 0.0
        }

        self.data = data
        self.model = model

        self.kills = 0
        self.deaths = 0
        self.assists = 0
        self.cs = 0  # Increment on last hit/deny

    def _calc_max_hp(self, base) -> float:
        return 200 + base["strength"] * 22 + self.level * 100

    def _calc_max_mana(self, base) -> float:
        return 75 + base["intelligence"] * 12 + self.level * 50

    def get_move_speed(self) -> float:
        base = self.data["base_stats"]["move_speed"]
        bonus = self.get_component("stats").move_speed_bonus
        return base + bonus

    def get_attack_damage(self) -> float:
        base_min = self.data["base_stats"]["damage_min"]
        base_max = self.data["base_stats"]["damage_max"]
        souls = self.get_component("souls").current
        bonus = self.get_component("stats").attack_damage
        soul_bonus = souls * self.model.constants["hero"]["soul_damage_per_soul"]
        return (base_min + base_max) / 2 + bonus + soul_bonus

    def get_attack_range(self) -> float:
        base = self.data["base_stats"]["attack_range"]
        souls = self.get_component("souls").current
        bonus = souls * self.model.constants["hero"]["soul_attack_range_bonus"]
        return base + bonus

    def cast_raze(self, which: str):
        """which = short / medium / long"""
        cd_key = f"raze_{which}"
        if self.cooldowns[cd_key] > 0:
            return False

        mana_comp = self.get_component("mana")
        if mana_comp.current < 90:
            return False

        # Placeholder for projectile
        mana_comp.current -= 90
        self.cooldowns[cd_key] = 10.0
        return True

    def cast_requiem(self):
        if self.cooldowns["requiem"] > 0:
            return False
        mana = self.get_component("mana").current
        if mana < 150:
            return False

        # Placeholder
        self.get_component("mana").current -= 150
        self.cooldowns["requiem"] = 120.0
        self.get_component("souls").current = 0
        return True

    def update_cooldowns(self, dt: float):
        for k in self.cooldowns:
            if self.cooldowns[k] > 0:
                self.cooldowns[k] = max(0, self.cooldowns[k] - dt)

    def serialize(self) -> dict:
        pos = self.get_component("position").value
        return {
            "id": self.id,
            "type": "hero",
            "player_id": self.player_id,
            "team": self.team,
            "position": pos.tolist(),
            "hp": self.get_component("health").current,
            "mana": self.get_component("mana").current,
            "level": self.level,
            "souls": self.get_component("souls").current,
            "gold": self.get_component("inventory").gold,
            "facing": self.get_component("facing").angle,
            "cooldowns": self.cooldowns.copy()
        }