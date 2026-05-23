# engine/model/game_model.py
import json
import time
import random
from typing import Dict, List, Optional, Any
import numpy as np
import yaml

from .ecs.entity import EntityManager
from .systems.creep_spawn_system import CreepSpawnSystem
from .systems.item_system import ItemSystem
from .systems.movement_system import MovementSystem
from .systems.rune_system import RuneSystem
from .systems.tower_system import TowerSystem
from .systems.win_condition_system import WinConditionSystem
from .systems.combat_system import CombatSystem
from .systems.ability_system import AbilitySystem
from .systems.vision_system import VisionSystem

from .spatial_hash import SpatialHash
with open('./config/constants.json', 'r') as file:
    CONSTANTS = json.load(file)


class GameModel:
    """Authoritative game simulation – 100% renderer/network agnostic."""
    
    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        self.constants = CONSTANTS
        self.tick_rate = self.constants["game"]["tps"]
        self.dt = 1.0 / self.tick_rate
        self.current_tick = 0
        self.game_time = 0.0
        self.winner: Optional[int] = None  # 0 or 1 or None

        # ECS core
        self.entities = EntityManager()
        self.spatial_hash = SpatialHash(cell_size=800)

        # Systems (Neural MMO 2 style)
        self.systems = {
            "creep_spawn": CreepSpawnSystem(self),
            "rune": RuneSystem(self),
            "movement": MovementSystem(self),
            "combat": CombatSystem(self),
            "tower": TowerSystem(self),    # Tower-specific attacks
            "ability": AbilitySystem(self),
            "item": ItemSystem(self),
            "vision": VisionSystem(self),
            "win": WinConditionSystem(self),
        }

        # Controllers (human, AI, network)
        self.controllers: Dict[int, Any] = {}

        # Fog of War grids (one per player)
        self.fog_of_war = {
            0: np.ones((224, 200), dtype=bool),  # 16000x14400 / 72px grid
            1: np.ones((224, 200), dtype=bool)
        }

        self._load_map_bounds()
        self._spawn_heroes()
        self._spawn_towers_and_ancient()

        self.fountain_pos = {
            0: np.array([13000, 13000]),
            1: np.array([3000, 3000])
        }
        self.systems["win"] = WinConditionSystem(self)

    def _load_map_bounds(self):
        """Hard-coded Dota 2 map impassable areas (trees, cliffs). Simplified."""
        w, h = 16000, 14400
        self.passable_grid = np.ones((w // 64, h // 64), dtype=bool)  # 64px cells
        # TODO: load real map mask from file or generate

    def _spawn_heroes(self):
        """Spawn Radiant (0) and Dire (1) Shadow Fiend"""
        from .entities.hero import Hero
        with open("config/heroes/shadow_fiend.yaml") as f:
            hero_data = yaml.safe_load(f)

        radiant_pos = np.array([12000.0, 12000.0])
        dire_pos = np.array([4000.0, 4000.0])

        hero0 = Hero(self, player_id=0, team=0, position=radiant_pos, data=hero_data)
        hero1 = Hero(self, player_id=1, team=1, position=dire_pos, data=hero_data)

        self.entities.add(hero0)
        self.entities.add(hero1)

    def _spawn_towers_and_ancient(self):
        """Spawn all towers + ancients (simplified positions)"""
        from .entities.tower import Tower
        from .entities.ancient import Ancient

        # Very simplified — real map has 11 towers per side
        positions = [
            # Radiant towers
            [11000, 11000], [9000, 9000], [7000, 7000],
            # Dire towers
            [5000, 5000], [7000, 7000], [9000, 9000],
        ]
        for i, pos in enumerate(positions[:3]):
            t = Tower(self, team=0, tier=i+1, position=np.array(pos, dtype=float))
            self.entities.add(t)
        for i, pos in enumerate(positions[3:]):
            t = Tower(self, team=1, tier=i+1, position=np.array(pos, dtype=float))
            self.entities.add(t)

        # Ancients
        ancient_radiant = Ancient(self, team=0, position=np.array([13000, 13000], dtype=float))
        ancient_dire = Ancient(self, team=1, position=np.array([3000, 3000], dtype=float))
        self.entities.add(ancient_radiant)
        self.entities.add(ancient_dire)

    def register_controller(self, player_id: int, controller):
        self.controllers[player_id] = controller

    def update(self, dt: float):
        """Fixed timestep update – called 15 times per second (or faster in headless)"""
        if self.winner is not None:
            return

        self.current_tick += 1
        self.game_time += dt

        # Order matters
        self.systems["creep_spawn"].update(dt)
        self.systems["rune"].update(dt)
        self.systems["movement"].update(dt)
        self.systems["ability"].update(dt)
        self.systems["combat"].update(dt)
        self.systems["item"].update(dt)
        self.systems["vision"].update(dt)
        self.systems["win"].update(dt)

        # Update spatial hash
        self.spatial_hash.clear()
        for entity in self.entities.all():
            if hasattr(entity, "position"):
                self.spatial_hash.insert(entity)

    def get_state_snapshot(self) -> Dict:
        """Used for networking (lockstep) and RL observation"""
        return {
            "tick": self.current_tick,
            "time": self.game_time,
            "winner": self.winner,
            "entities": [
                e.serialize() for e in self.entities.all()
                if hasattr(e, "serialize")
            ],
            "fog": {
                0: self.fog_of_war[0].tolist(),
                1: self.fog_of_war[1].tolist()
            }
        }

    def reset(self):
        """Full reset – for RL episodes"""
        self.__init__(seed=random.randint(0, 2**31))