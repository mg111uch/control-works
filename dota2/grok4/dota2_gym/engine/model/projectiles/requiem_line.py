# engine/model/projectiles/requiem_line.py
import numpy as np
from ..ecs.entity import Entity


class RequiemLine(Entity):
    """One line from Requiem of Souls"""
    def __init__(self, model, start_pos: np.ndarray, direction: np.ndarray, damage_per_line: float, owner):
        super().__init__(model)
        pos_comp = type("Pos", (Component,), {"value": start_pos.copy()})
        self.add_component("position", pos_comp())

        self.direction = direction.astype(np.float32)
        self.speed = 600.0
        self.width = 125.0
        self.damage = damage_per_line
        self.owner = owner
        self.traveled = 0.0
        self.max_distance = 2000.0
        self.hit_entities = set()

    def update(self, dt: float):
        pos = self.get_component("position").value
        move = self.direction * self.speed * dt
        pos += move
        self.traveled += np.linalg.norm(move)

        # Check hits
        candidates = self.model.spatial_hash.query_radius(pos, self.width + 100)
        for ent in candidates:
            if ent == self.owner or ent.id in self.hit_entities:
                continue
            if not hasattr(ent, "get_component"):
                continue
            health = ent.get_component("health")
            if not health:
                continue
            # Simple cylinder check
            to_ent = ent.get_component("position").value - pos
            proj_dist = np.dot(to_ent, self.direction)
            if proj_dist < 0:
                continue
            closest = pos + self.direction * proj_dist
            dist_to_line = np.linalg.norm(ent.get_component("position").value - closest)
            if dist_to_line <= self.width:
                health.current -= self.damage
                self.hit_entities.add(ent.id)
                if health.current <= 0:
                    self.owner.get_component("souls").current = 0  # release on death

        if self.traveled >= self.max_distance:
            self.model.entities.remove(self)