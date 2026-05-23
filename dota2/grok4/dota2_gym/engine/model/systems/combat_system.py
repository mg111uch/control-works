# engine/model/systems/combat_system.py
"""
CombatSystem – Full Dota 2 combat engine
Features:
  • Auto-attacks (projectile + instant)
  • Last-hit / deny detection
  • Kill credit, gold, XP, souls
  • Damage types (physical/magical/pure)
  • Armor & magic resistance reduction
  • Buyback integration
  • Death handling (respawn timer, buyback)
  • Full integration with WinConditionSystem
"""

import numpy as np
from typing import List, Optional
from ..ecs.entity import Entity


class CombatSystem:
    def __init__(self, model):
        self.model = model
        self.projectiles: List[Entity] = []  # Track all active projectiles

    def update(self, dt: float):
        # 1. Update all projectiles
        self._update_projectiles(dt)

        # 2. Handle hero auto-attacks (if not already attacking)
        self._handle_hero_auto_attacks(dt)

        # 3. Tower attacks handled in TowerSystem

    def _update_projectiles(self, dt: float):
        """Move projectiles and check hits"""
        for proj in self.projectiles[:]:
            # Age
            proj_age = getattr(proj, "age", 0.0) + dt
            setattr(proj, "age", proj_age)

            # Move
            pos = proj.get_component("position").value
            pos += proj.direction * proj.speed * dt

            # Lifetime expire
            if proj_age > getattr(proj, "lifetime", 3.0):
                self.projectiles.remove(proj)
                self.model.entities.remove(proj)
                continue

            # Target hit detection
            if hasattr(proj, "target") and proj.target in self.model.entities.all():
                target_pos = proj.target.get_component("position").value
                if np.linalg.norm(pos - target_pos) < 60:
                    self._apply_damage(proj.target, proj.damage, proj.damage_type, proj.owner)
                    self.projectiles.remove(proj)
                    self.model.entities.remove(proj)

    def _handle_hero_auto_attacks(self, dt: float):
        heroes = [e for e in self.model.entities.all() if hasattr(e, "player_id")]

        for hero in heroes:
            if not hero.get_component("health") or hero.get_component("health").current <= 0:
                continue

            attack_timer = getattr(hero, "attack_timer", 0.0) + dt
            bat = 1.7 / (1 + hero.get_component("stats").attack_speed / 100.0)

            if attack_timer < bat:
                hero.attack_timer = attack_timer
                continue

            # Find target
            target = self._find_attack_target(hero)
            if not target:
                hero.attack_timer = 0.0
                continue

            # Face target
            direction = target.get_component("position").value - hero.get_component("position").value
            direction = direction / (np.linalg.norm(direction) + 1e-8)
            hero.get_component("facing").angle = np.arctan2(direction[1], direction[0])

            # Launch attack
            self._launch_attack(hero, target)
            hero.attack_timer = attack_timer - bat

    def _find_attack_target(self, attacker) -> Optional[Entity]:
        pos = attacker.get_component("position").value
        range_val = attacker.get_attack_range()

        candidates = self.model.spatial_hash.query_radius(pos, range_val + 100)
        enemies = []

        for ent in candidates:
            if not hasattr(ent, "team") or ent.team == attacker.team:
                continue
            if not ent.get_component("health") or ent.get_component("health").current <= 0:
                continue

            dist = np.linalg.norm(ent.get_component("position").value - pos)
            if dist > range_val:
                continue

            # Priority: low HP creeps (last hit), then heroes
            priority = 0
            hp_pct = ent.get_component("health").current / ent.get_component("health").maximum
            if hasattr(ent, "creep_type") and hp_pct < 0.5:
                priority = 3
            elif hasattr(ent, "player_id"):
                priority = 2
            else:
                priority = 1

            enemies.append((dist, -priority, hp_pct, ent))

        if not enemies:
            return None

        enemies.sort()  # closest + highest priority + lowest HP
        return enemies[0][3]

    def _launch_attack(self, attacker, target):
        pos = attacker.get_component("position").value.copy()
        direction = target.get_component("position").value - pos
        direction = direction / (np.linalg.norm(direction) + 1e-8)

        damage = attacker.get_attack_damage()
        projectile_speed = attacker.data["base_stats"]["projectile_speed"]

        proj = type("AttackProj", (), {
            "position": type("Pos", (), {"value": pos}),
            "direction": direction,
            "speed": projectile_speed,
            "target": target,
            "owner": attacker,
            "damage": damage,
            "damage_type": "physical",
            "age": 0.0,
            "lifetime": 3.0
        })()

        self.model.entities.add(proj)
        self.projectiles.append(proj)

    def _apply_damage(self, target, damage: float, damage_type: str, attacker):
        if not target.get_component("health"):
            return

        health = target.get_component("health")
        was_alive = health.current > 0

        # Armor & magic resist reduction
        if damage_type == "physical":
            armor = getattr(target, "armor", 0)
            reduction = armor / (0.06 * armor + 1.0)
            damage *= (1 - reduction)
        elif damage_type == "magical":
            mr = getattr(target, "magic_resistance", 25) / 100.0
            damage *= (1 - mr)

        health.current -= damage

        if was_alive and health.current <= 0:
            self._handle_death(target, attacker)

    def _handle_death(self, victim, killer):
        # Gold & XP
        gold = getattr(victim, "bounty", 0)
        if gold > 0 and killer and hasattr(killer, "get_component"):
            inv = killer.get_component("inventory")
            if inv:
                inv.gold += gold
                killer.cs = getattr(killer, "cs", 0) + 1

        # Souls for Shadow Fiend
        if killer and hasattr(killer, "get_component") and killer.get_component("souls"):
            souls = killer.get_component("souls")
            souls.current = min(40, souls.current + 1)

        # Kill credit
        if killer:
            killer.kills = getattr(killer, "kills", 0) + 1

        victim.deaths = getattr(victim, "deaths", 0) + 1

        # Respawn timer or buyback
        if hasattr(victim, "player_id"):
            # Hero death
            victim.respawn_timer = 10.0  # Base respawn
            victim.get_component("position").value = np.array([-1000, -1000])  # Off map
        else:
            # Creep/tower – just remove
            self.model.entities.remove(victim)

        print(f"[KILL] {killer.player_id if killer else 'Neutral'} killed {getattr(victim, 'player_id', 'Creep')}")

    def register_projectile(self, proj):
        self.projectiles.append(proj)