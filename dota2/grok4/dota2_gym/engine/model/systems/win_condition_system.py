# engine/model/systems/win_condition_system.py
"""
WinConditionSystem – 1v1 Fast Mode
Rules:
  • First tower destroyed → enemy wins
  • Ancient destroyed → enemy wins
  • Post-game scoreboard (K/D/A, CS, gold)
  • Game fully stops (no more updates)
  • Buyback resets death but not towers/ancients
"""

from typing import Dict, Any
from ..ecs.entity import Entity

class WinConditionSystem:
    def __init__(self, model):
        self.model = model

    def update(self, dt: float):
        if self.model.winner is not None:
            return  # Game over

        # Check towers
        towers = [e for e in self.model.entities.all() if hasattr(e, "tier")]
        for tower in towers:
            health = tower.get_component("health")
            if health and health.current <= 0:
                enemy_team = 1 - tower.team
                self.model.winner = enemy_team
                self._trigger_post_game(enemy_team, "tower_destroyed")
                return

        # Check ancients
        ancients = [e for e in self.model.entities.all() if hasattr(e, "team") and "ancient" in str(type(e))]
        for ancient in ancients:
            health = ancient.get_component("health")
            if health and health.current <= 0:
                enemy_team = 1 - ancient.team
                self.model.winner = enemy_team
                self._trigger_post_game(enemy_team, "ancient_destroyed")
                return

    def _trigger_post_game(self, winner: int, reason: str):
        """Set game state + compute scoreboard"""
        self.model.game_time_paused = self.model.game_time  # Freeze time

        # Compute stats for scoreboard
        heroes = [e for e in self.model.entities.all() if hasattr(e, "player_id")]
        scoreboard = {}
        for hero in heroes:
            stats = {
                "player_id": hero.player_id,
                "kills": getattr(hero, "kills", 0),
                "deaths": getattr(hero, "deaths", 0),
                "assists": getattr(hero, "assists", 0),
                "cs": getattr(hero, "cs", 0),  # last hits + denies
                "gold": hero.get_component("inventory").gold if hero.get_component("inventory") else 0,
                "level": hero.level
            }
            scoreboard[hero.player_id] = stats

        self.model.scoreboard = scoreboard
        self.model.win_reason = reason
        print(f"*** GAME OVER *** Player {winner} wins by {reason}!")

    def can_buyback(self, hero: Entity) -> bool:
        """Buyback check (called from death handler)"""
        if hero.get_component("health").current > 0:
            return False

        # Standard Dota formula
        level = hero.level
        networth = hero.get_component("inventory").gold
        cost = (100 + level * level * 1.5 + networth / 13)

        inv = hero.get_component("inventory")
        if inv.gold < cost:
            return False

        # Cooldown (5 min base, scales down)
        cd_time = max(300 - level * 15, 90)
        last_buyback = getattr(hero, "last_buyback_time", 0)
        if self.model.game_time - last_buyback < cd_time:
            return False

        return True

    def perform_buyback(self, hero: Entity):
        inv = hero.get_component("inventory")
        level = hero.level
        networth = inv.gold
        cost = 100 + level * level * 1.5 + networth / 13
        inv.gold -= cost

        hero.last_buyback_time = self.model.game_time
        hero.get_component("health").current = hero.get_component("health").maximum
        hero.get_component("mana").current = hero.get_component("mana").maximum
        hero.get_component("position").value = self.model.fountain_pos[hero.team]  # Respawn at fountain