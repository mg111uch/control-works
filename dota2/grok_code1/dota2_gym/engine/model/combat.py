# engine/model/combat.py
"""
Combat system – handles:
  • Auto-attacks (projectile-based)
  • Last-hits / denies
  • Damage application
  • Kill credit & gold/XP
  • Necromastery soul collection
  • Tower targeting logic (even if no aggro, towers still attack)
"""
import numpy as np
from typing import List, Optional
from .ecs.entity import Entity


class CombatSystem:
    def __init__(self, model):
        self.model = model
        self.projectiles: List[Entity] = []  # Will be replaced with ECS later

    def update(self, dt: float):
        heroes = [e for e in self.model.entities.all()
                  if hasattr(e, "player_id") and hasattr(e, "get_attack_damage")]

        for hero in heroes:
            self._update_hero_attack(hero, dt)

        # Update existing attack projectiles
        for proj in self.projectiles[:]:
            proj_age = getattr(proj, "age", 0) + dt
            setattr(proj, "age", proj_age)

            # Travel
            pos = proj.position.value
            pos += proj.direction * proj.speed * dt

            # Check impact
            if np.linalg.norm(pos - proj.target_pos) < 30:
                self._apply_attack_damage(proj)
                self.projectiles.remove(proj)

    def _update_hero_attack(self, hero, dt: float):
        attack_timer = getattr(hero, "attack_timer", 0.0) + dt
        bat = hero.data["base_stats"]["base_attack_time"] / (1 + hero.get_component("stats").attack_speed / 100)

        if attack_timer < bat:
            hero.attack_timer = attack_timer
            return

        # Find target (closest enemy in range)
        hero_pos = hero.get_component("position").value
        attack_range = hero.get_attack_range()
        enemies = []

        for ent in self.model.spatial_hash.query_radius(hero_pos, attack_range + 100):
            if not hasattr(ent, "team") or ent.team == hero.team:
                continue
            if not ent.get_component("health"):
                continue
            if ent.get_component("health").current <= 0:
                continue

            # Prioritize creeps for last hits, then heroes
            dist = np.linalg.norm(ent.get_component("position").value - hero_pos)
            priority = 0
            if "creep" in str(type(ent)):
                priority = 1
            elif "hero" in str(type(ent)):
                priority = 2
            enemies.append((dist, priority, ent))

        if not enemies:
            hero.attack_timer = 0.0
            return

        # Sort: closest + priority
        enemies.sort(key=lambda x: (x[0], -x[1]))
        target = enemies[0][2]

        # Face target
        direction = target.get_component("position").value - hero_pos
        direction = direction / (np.linalg.norm(direction) + 1e-8)
        hero.get_component("facing").angle = np.arctan2(direction[1], direction[0])

        # Launch projectile
        self._launch_attack_projectile(hero, target)

        hero.attack_timer = attack_timer - bat

    def _launch_attack_projectile(self, attacker, target):
        pos = attacker.get_component("position").value.copy()
        direction = target.get_component("position").value - pos
        direction = direction / (np.linalg.norm(direction) + 1e-8)

        proj = type("AttackProjectile", (), {
            "position": type("Pos", (), {"value": pos}),
            "direction": direction,
            "speed": attacker.data["base_stats"]["projectile_speed"],
            "target": target,
            "target_pos": target.get_component("position").value.copy(),
            "owner": attacker,
            "age": 0.0,
            "damage": attacker.get_attack_damage(),
            "is_hero_attack": True
        })()

        self.projectiles.append(proj)

    def _apply_attack_damage(self, projectile):
        target = projectile.target
        if not target.get_component("health") or target.get_component("health").current <= 0:
            return

        damage = projectile.damage
        target_hp = target.get_component("health")
        was_alive = target_hp.current > 0

        target_hp.current -= damage

        if was_alive and target_hp.current <= 0:
            self._handle_kill(projectile.owner, target)

    def _handle_kill(self, killer, victim):
        # Gold & XP
        gold = getattr(victim, "bounty", 0)
        if gold > 0 and hasattr(killer, "get_component"):
            inv = killer.get_component("inventory")
            if inv:
                inv.gold += gold

        # Souls for Shadow Fiend
        if hasattr(killer, "get_component") and killer.get_component("souls") is not None:
            souls = killer.get_component("souls")
            souls.current = min(40, souls.current + 1)

        # Deny detection (same team kill)
        if hasattr(victim, "team") and victim.team == killer.team:
            # Deny bonus (reduced gold to enemy)
            pass

        # Remove dead unit
        self.model.entities.remove(victim)