# engine/model/projectiles/tower_projectile.py
import numpy as np
from ..ecs.entity import Entity


class TowerProjectile(Entity):
    def __init__(self, model, start_pos: np.ndarray, target, owner: Entity, damage: float):
        super().__init__(model)
        direction = target.get_component("position").value - start_pos
        dist = np.linalg.norm(direction)
        direction = direction / (dist + 1e-8)

        self.add_component("position", type("Pos", (), {"value": start_pos.copy()}))
        self.add_component("projectile", type("Proj", (), {
            "direction": direction,
            "speed": 1200.0,
            "lifetime": dist / 1200.0 + 0.2,
            "age": 0.0
        }))
        self.owner = owner
        self.target = target
        self.damage = damage

    def update(self, dt: float):
        proj = self.get_component("projectile")
        proj.age += dt
        if proj.age >= proj.lifetime:
            self.model.entities.remove(self)
            return

        pos = self.get_component("position").value
        pos += proj.direction * proj.speed * dt

        # Hit detection
        target_pos = self.target.get_component("position").value
        if np.linalg.norm(pos - target_pos) < 50:
            # Apply damage (call CombatSystem logic)
            health = self.target.get_component("health")
            if health:
                health.current -= self.damage
                if health.current <= 0:
                    # Kill handled elsewhere
                    pass
            self.model.entities.remove(self)