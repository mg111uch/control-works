# engine/model/entities/creep.py
import numpy as np
from ..ecs.entity import Entity


class Creep(Entity):
    def __init__(self, model, team: int, creep_type: str, position, waypoints, wave_number: int):
        super().__init__(model)
        self.team = team
        self.creep_type = creep_type
        self.wave_number = wave_number

        # Stats (match Dota 2)
        stats = {
            "melee":  {"hp": 550, "damage": 22, "bounty": 40, "speed": 325},
            "ranged": {"hp": 300, "damage": 45, "bounty": 48, "speed": 300},
            "siege":  {"hp": 875, "damage": 40, "bounty": 88, "speed": 280}
        }
        s = stats[creep_type]
        self.bounty = model.systems["creep_spawn"].get_bounty(creep_type, wave_number)

        self.add_component("position", type("Pos", (), {"value": position.copy()}))
        self.add_component("velocity", type("Vel", (), {"value": np.zeros(2)}))
        self.add_component("health", type("Health", (), {"current": s["hp"], "maximum": s["hp"]}))
        self.add_component("facing", type("Facing", (), {"angle": 0.0}))

        self.waypoints = waypoints.copy()
        self.current_waypoint = 0
        self.move_speed = s["speed"]
        self.damage = s["damage"]

    def update(self, dt: float):
        if self.current_waypoint >= len(self.waypoints):
            self.model.entities.remove(self)
            return

        target = self.waypoints[self.current_waypoint]
        pos = self.get_component("position").value
        direction = target - pos
        dist = np.linalg.norm(direction)

        if dist < 100:
            self.current_waypoint += 1
        else:
            direction = direction / (dist + 1e-8)
            self.get_component("velocity").value = direction * self.move_speed
            self.get_component("facing").angle = np.arctan2(direction[1], direction[0])