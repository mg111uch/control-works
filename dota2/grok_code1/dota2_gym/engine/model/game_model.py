# engine/model/game_model.py
import json
from .ecs.entity import EntityManager
from .systems.movement_system import MovementSystem
from .combat import CombatSystem
from .spatial_hash import SpatialHash


class GameModel:
    def __init__(self):
        with open('config/constants.json', 'r') as f:
            self.constants = json.load(f)
        self.entities = EntityManager()
        self.spatial_hash = SpatialHash()
        self.systems = {
            "movement": MovementSystem(self),
            "combat": CombatSystem(self),
        }
        self.controllers = {}
        self.game_time = 0.0
        self.current_tick = 0
        self.winner = None

    def register_controller(self, player_id, controller):
        self.controllers[player_id] = controller

    def update(self, dt):
        self.current_tick += 1
        self.game_time += dt
        # Update spatial hash first
        self.spatial_hash.clear()
        for entity in self.entities.all():
            self.spatial_hash.insert(entity)
        self.systems["movement"].update(dt)
        self.systems["combat"].update(dt)

    def get_state_snapshot(self):
        return {
            "tick": self.current_tick,
            "time": self.game_time,
            "winner": self.winner,
            "entities": [e.serialize() for e in self.entities.all() if hasattr(e, "serialize")]
        }
