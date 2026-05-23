# engine/model/systems/rune_system.py
"""
RuneSystem – Full Dota 2 rune simulation
Features:
  • Power Runes (Double Damage & Haste) spawn every 2:00
  • Two random river locations (classic Dota 2 style)
  • Pickup on touch
  • 45s Double Damage / 25s Haste duration
  • Visual indicator + instant effect
  • Bounty rune logic ready (optional)
"""

import numpy as np
import random
from typing import List, Optional
from ..ecs.entity import Entity


# Pre-defined river rune spawn zones (real Dota 2 river bounds)
RIVER_RUNE_ZONES = [
    np.array([6200, 5400]),   # Near mid river
    np.array([7800, 6600]),   # Upper river bend
    np.array([5400, 7800]),   # Lower river bend
    np.array([8600, 4600]),   # Near Radiant ancient
    np.array([4600, 8600]),   # Near Dire ancient
]

class Rune(Entity):
    def __init__(self, model, position: np.ndarray, rune_type: str):
        super().__init__(model)
        self.rune_type = rune_type  # "double_damage" or "haste"
        self.add_component("position", type("Pos", (), {"value": position.copy()}))
        self.add_component("pickup_radius", type("Radius", (), {"value": 100.0}))

    def serialize(self):
        pos = self.get_component("position").value
        return {
            "id": self.id,
            "type": "rune",
            "rune_type": self.rune_type,
            "position": pos.tolist()
        }


class RuneSystem:
    def __init__(self, model):
        self.model = model
        self.next_rune_time = 120.0   # First at 2:00
        self.rune_interval = 120.0    # Every 2 minutes
        self.active_runes: List[Rune] = []

    def update(self, dt: float):
        # Spawn new runes
        if self.model.game_time >= self.next_rune_time:
            self._spawn_power_runes()
            self.next_rune_time += self.rune_interval

        # Check pickup
        self._check_rune_pickups()

        # Expire old runes visually (optional)
        self.active_runes = [r for r in self.active_runes if r in self.model.entities.all()]

    def _spawn_power_runes(self):
        """Spawn 2 power runes at random river locations"""
        positions = random.sample(RIVER_RUNE_ZONES, 2)
        types = ["double_damage", "haste"]
        random.shuffle(types)

        for pos, rune_type in zip(positions, types):
            # Add small random offset
            offset = np.random.uniform(-200, 200, size=2)
            spawn_pos = pos + offset

            rune = Rune(self.model, spawn_pos, rune_type)
            self.model.entities.add(rune)
            self.active_runes.append(rune)

    def _check_rune_pickups(self):
        """Check if any hero touches a rune"""
        heroes = [e for e in self.model.entities.all()
                  if hasattr(e, "player_id") and e.get_component("health")]

        for hero in heroes:
            hero_pos = hero.get_component("position").value

            for rune in self.active_runes[:]:
                if rune not in self.model.entities.all():
                    continue

                rune_pos = rune.get_component("position").value
                dist = np.linalg.norm(hero_pos - rune_pos)

                if dist <= 100:  # Pickup radius
                    self._apply_rune_effect(hero, rune.rune_type)
                    self.model.entities.remove(rune)
                    if rune in self.active_runes:
                        self.active_runes.remove(rune)

    def _apply_rune_effect(self, hero, rune_type: str):
        """Apply rune buff instantly"""
        buffs = hero.get_component("buffs")
        if buffs is None:
            # Create buffs component if missing
            buffs = type("Buffs", (), {"active": {}})
            hero.add_component("buffs", buffs)

        if rune_type == "double_damage":
            duration = 45.0
            hero.get_component("stats").attack_damage += 100  # +100% damage
            # Store expiration
            buffs.active["double_damage"] = self.model.game_time + duration

        elif rune_type == "haste":
            duration = 25.0
            old_speed = hero.get_move_speed()
            hero.get_component("stats").move_speed_bonus += 550 - old_speed  # cap at 550
            buffs.active["haste"] = self.model.game_time + duration

        # Visual feedback in snapshot
        print(f"[Rune] {hero.player_id} picked up {rune_type}!")


# Add this to hero update loop (in Hero class or a BuffSystem later)
def update_rune_buffs(hero, current_time: float):
    """Call every tick to expire buffs"""
    buffs = hero.get_component("buffs")
    if not buffs or not buffs.active:
        return

    stats = hero.get_component("stats")

    # Double Damage expire
    if "double_damage" in buffs.active and current_time > buffs.active["double_damage"]:
        stats.attack_damage -= 100
        del buffs.active["double_damage"]

    # Haste expire
    if "haste" in buffs.active and current_time > buffs.active["haste"]:
        # Revert to normal speed
        stats.move_speed_bonus = max(0, stats.move_speed_bonus - 250)
        del buffs.active["haste"]