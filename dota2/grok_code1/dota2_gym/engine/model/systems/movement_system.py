# engine/model/systems/movement_system.py
import numpy as np
from typing import List
from ..ecs.entity import Entity


class MovementSystem:
    """Handles all unit movement using linear interpolation to target."""
    def __init__(self, model):
        self.model = model

    def update(self, dt: float):
        # Assume entities with position, velocity, and move_target
        for entity in self.model.entities.all():
            pos_comp = entity.get_component("position")
            vel_comp = entity.get_component("velocity")
            target_comp = entity.get_component("move_target")
            if not pos_comp or not vel_comp:
                continue

            pos = pos_comp.value
            vel = vel_comp.value

            if target_comp:
                target = target_comp.value
                direction = target - pos
                dist = np.linalg.norm(direction)
                if dist > 0:
                    # Move towards target
                    move_speed = getattr(entity, 'move_speed', 300.0)  # default
                    vel[:] = direction / dist * min(move_speed, dist / dt)  # cap at dist
                else:
                    vel[:] = 0
                    # Remove target when reached
                    entity.remove_component("move_target")
            else:
                # No target, stop
                vel[:] = 0

            # Apply velocity
            new_pos = pos + vel * dt

            # Basic bounds
            new_pos[0] = np.clip(new_pos[0], 0, 16000)
            new_pos[1] = np.clip(new_pos[1], 0, 14400)

            pos[:] = new_pos