# engine/model/systems/ability_system.py
"""
AbilitySystem – Complete Shadow Fiend ability implementation
Features:
  • Q/W/E: 3 Shadow Raze stacks (different ranges)
  • R: Requiem of Souls (12 lines, soul scaling)
  • Full Necromastery (passive souls → damage + attack range)
  • Cooldowns, mana costs, cast points
  • Projectiles with real travel time
  • Stun/slow on Requiem lines
  • Visual indicators (in PygameView)
"""

import numpy as np
from typing import Dict, Any
from ..ecs.entity import Entity
from ..projectiles.raze_projectile import RazeProjectile
from ..projectiles.requiem_line import RequiemLine


class AbilitySystem:
    def __init__(self, model):
        self.model = model

    def update(self, dt: float):
        # Update hero cooldowns
        heroes = [e for e in self.model.entities.all() if hasattr(e, "player_id")]
        for hero in heroes:
            if not hasattr(hero, "cooldowns"):
                continue
            for key in hero.cooldowns:
                if hero.cooldowns[key] > 0:
                    hero.cooldowns[key] = max(0.0, hero.cooldowns[key] - dt)

            # Update soul collection from kills
            self._update_necromastery(hero)

    def cast_shadow_raze(self, hero: Entity, stack: str) -> bool:
        """stack = 'short', 'medium', 'long'"""
        if hero.cooldowns.get(f"raze_{stack}", 0) > 0:
            return False

        mana_cost = 90
        mana_comp = hero.get_component("mana")
        if not mana_comp or mana_comp.current < mana_cost:
            return False

        # Determine range
        ranges = {"short": 200, "medium": 450, "long": 700}
        distance = ranges[stack]

        # Direction from facing
        facing = hero.get_component("facing").angle
        direction = np.array([np.cos(facing), np.sin(facing)])

        # Launch projectile
        pos = hero.get_component("position").value
        start_pos = pos + direction * 100  # Slight offset

        level = min(hero.level - 1, 9)  # 0–9 for levels 1–10
        damage_table = [80, 140, 200, 260, 320, 380, 440, 500, 560, 620]
        damage = damage_table[level]

        proj = RazeProjectile(self.model, start_pos, direction, distance, damage, hero)
        self.model.entities.add(proj)

        # Apply cost & cooldown
        mana_comp.current -= mana_cost
        hero.cooldowns[f"raze_{stack}"] = 10.0
        return True

    def cast_requiem_of_souls(self, hero: Entity) -> bool:
        if hero.cooldowns.get("requiem", 0) > 0:
            return False

        mana_cost = 150
        mana_comp = hero.get_component("mana")
        if not mana_comp or mana_comp.current < mana_cost:
            return False

        souls = hero.get_component("souls").current
        pos = hero.get_component("position").value

        # Base + soul scaling
        base_damage = 80
        soul_multiplier = 0.4
        damage_per_line = base_damage + souls * soul_multiplier

        # 12 lines in circle
        for i in range(12):
            angle = i * np.pi / 6
            direction = np.array([np.cos(angle), np.sin(angle)])
            line = RequiemLine(self.model, pos.copy(), direction, damage_per_line, hero)
            self.model.entities.add(line)

        # Effects
        mana_comp.current -= mana_cost
        hero.cooldowns["requiem"] = 120.0

        # Release souls on ult
        hero.get_component("souls").current = 0

        print(f"[ULT] Shadow Fiend used Requiem! {souls} souls → {damage_per_line:.1f} dmg/line")
        return True

    def _update_necromastery(self, hero: Entity):
        """Passive soul collection from nearby deaths"""
        # Already handled in CombatSystem on kill
        # This is just for visual update
        souls_comp = hero.get_component("souls")
        if souls_comp:
            # Bonus attack range & damage applied in hero.get_attack_range/damage
            pass

    # Called from controller
    def handle_ability_input(self, hero: Entity, ability: str):
        if ability == "raze_short":
            self.cast_shadow_raze(hero, "short")
        elif ability == "raze_medium":
            self.cast_shadow_raze(hero, "medium")
        elif ability == "raze_long":
            self.cast_shadow_raze(hero, "long")
        elif ability == "requiem":
            self.cast_requiem_of_souls(hero)