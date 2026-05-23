# engine/model/projectiles/raze_projectile.py
import numpy as np
from ..ecs.entity import Entity, Component


class Projectile(Component):
    def __init__(self, direction: np.ndarray, speed: float, lifetime: float):
        self.direction = direction.astype(np.float32)
        self.speed = speed
        self.age = 0.0
        self.max_lifetime = lifetime


class Damage(Component):
    def __init__(self, value: float, damage_type: str = "magical", owner = None):
        self.value = value
        self.type = damage_type
        self.owner = owner


class AreaOfEffect(Component):
    def __init__(self, radius: float):
        self.radius = radius


class RazeProjectile(Entity):
    """Shadow Raze ground explosion projectile"""
    def __init__(self, model, start_pos: np.ndarray, direction: np.ndarray, distance: float, owner):
        super().__init__(model)
        pos_comp = type("Pos", (Component,), {"value": start_pos.copy()})
        self.add_component("position", pos_comp())
        self.add_component("velocity", type("Vel", (Component,), {"value": direction * 900})())

        # Travel to target distance then explode
        travel_time = distance / 900.0
        self.add_component("projectile", Projectile(direction, 900, travel_time + 0.1))

        # Damage on arrival
        level = owner.level - 1
        damage = model.constants["raze"]["damage"][level]
        self.add_component("damage", Damage(damage, "magical", owner))
        self.add_component("aoe", AreaOfEffect(250))

        self.owner = owner
        self.has_exploded = False

    def update(self, dt: float):
        proj = self.get_component("projectile")
        proj.age += dt
        if proj.age >= proj.max_lifetime and not self.has_exploded:
            self.explode()
            self.has_exploded = True

    def explode(self):
        pos = self.get_component("position").value
        entities = self.model.spatial_hash.query_radius(pos, 250)
        for ent in entities:
            if not hasattr(ent, "get_component") or ent == self.owner:
                continue
            health = ent.get_component("health")
            if health:
                damage = self.get_component("damage").value
                health.current -= damage
                if health.current <= 0:
                    self.owner.get_component("souls").current = min(
                        40, self.owner.get_component("souls").current + 1
                    )
        # Remove self after explosion
        self.model.entities.remove(self)