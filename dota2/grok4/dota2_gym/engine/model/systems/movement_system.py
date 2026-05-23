# engine/model/systems/movement_system.py
import numpy as np
from typing import List
from ..ecs.entity import Entity


class MovementSystem:
    """Handles all unit movement, pathfinding avoidance, and velocity updates."""
    def __init__(self, model):
        self.model = model

    def update(self, dt: float):
        heroes = self.model.entities.of_type(type("Hero", (), {}))  # simple duck typing
        for hero in heroes:
            if not hero.get_component("position") or not hero.get_component("velocity"):
                continue

            pos = hero.get_component("position").value
            vel = hero.get_component("velocity").value
            move_speed = hero.get_move_speed()

            # Desired velocity from controller
            desired_vel = np.zeros(2, dtype=np.float32)
            controller = self.model.controllers.get(hero.player_id)
            if controller and hasattr(controller, "current_input"):
                input_vec = controller.current_input.get("move_direction", np.zeros(2))
                if np.linalg.norm(input_vec) > 0.1:
                    desired_vel = input_vec * move_speed
                    # Update facing instantly (no turn rate)
                    angle = np.arctan2(input_vec[1], input_vec[0])
                    hero.get_component("facing").angle = angle

            # Simple steering + local avoidance
            steering = desired_vel - vel
            if np.linalg.norm(steering) > 0:
                steering = steering / np.linalg.norm(steering) * 400.0  # max accel

            vel += steering * dt
            speed = np.linalg.norm(vel)
            if speed > move_speed:
                vel = vel / speed * move_speed

            # Apply movement
            new_pos = pos + vel * dt

            # Basic map bounds + tree collision (simplified)
            new_pos[0] = np.clip(new_pos[0], 100, 15900)
            new_pos[1] = np.clip(new_pos[1], 100, 14300)

            pos[:] = new_pos
            hero.get_component("velocity").value = vel

            # Fountain regen
            fountain_pos = np.array([13000, 13000]) if hero.team == 0 else np.array([3000, 3000])
            if np.linalg.norm(pos - fountain_pos) < 900:
                hp = hero.get_component("health")
                mana = hero.get_component("mana")
                hp.current = min(hp.maximum, hp.current + 40 * dt)
                mana.current = min(mana.maximum, mana.current + 30 * dt)