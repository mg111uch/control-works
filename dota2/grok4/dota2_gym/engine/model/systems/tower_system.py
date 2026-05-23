# engine/model/systems/tower_system.py
"""
TowerSystem – Handles tower auto-attacks & damage
Features:
  • Auto-target closest enemy in 700 range
  • Projectile attacks (dodgable)
  • Prioritize creeps > heroes
  • Damage application via CombatSystem
  • Death triggers win condition check
  • No aggro (always attacks if enemy in range)
"""

import numpy as np
from ..entities.tower import Tower
from ..projectiles.tower_projectile import TowerProjectile  # See below


class TowerSystem:
    def __init__(self, model):
        self.model = model

    def update(self, dt: float):
        towers = self.model.entities.of_type(Tower)
        for tower in towers:
            self._update_tower_attack(tower, dt)

    def _update_tower_attack(self, tower: Tower, dt: float):
        attack_comp = tower.get_component("attack")
        if self.model.game_time < attack_comp.next_attack_time:
            return

        pos = tower.get_component("position").value
        range_sq = attack_comp.range ** 2

        # Find closest enemy
        enemies = []
        candidates = self.model.spatial_hash.query_radius(pos, attack_comp.range + 50)

        for ent in candidates:
            if not hasattr(ent, "team") or ent.team == tower.team:
                continue
            ent_pos = ent.get_component("position").value if ent.get_component("position") else None
            if ent_pos is None:
                continue
            dist_sq = np.sum((ent_pos - pos) ** 2)
            if dist_sq > range_sq:
                continue

            # Priority: creeps > heroes > projectiles/runes
            priority = 0
            if hasattr(ent, "creep_type"):
                priority = 2
            elif hasattr(ent, "player_id"):
                priority = 1

            enemies.append((dist_sq, -priority, ent))

        if not enemies:
            return

        # Closest + highest priority
        enemies.sort()
        target = enemies[0][2]

        # Launch projectile
        from ..projectiles.tower_projectile import TowerProjectile
        proj = TowerProjectile(self.model, pos.copy(), target, tower, attack_comp.damage)
        self.model.entities.add(proj)

        # Cooldown
        attack_comp.next_attack_time = self.model.game_time + attack_comp.cooldown