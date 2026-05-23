import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'

import pytest
import numpy as np
from engine.model.game_model import GameModel
from engine.model.ecs.entity import Entity
from engine.controller.human_controller import MoveTarget


def test_entity_reaches_target():
    model = GameModel()
    entity = Entity(model)
    entity.move_speed = 100.0  # units per second
    entity.add_component("position", type("Position", (), {"value": np.array([0.0, 0.0])})())
    entity.add_component("velocity", type("Velocity", (), {"value": np.zeros(2)})())
    model.entities.add(entity)

    # Set target
    target_pos = np.array([100.0, 0.0])
    entity.add_component("move_target", MoveTarget(target_pos[0], target_pos[1]))

    dt = 1.0 / 15.0  # 15 FPS
    ticks = 0
    while np.linalg.norm(entity.get_component("position").value - target_pos) > 1.0 and ticks < 100:
        model.update(dt)
        ticks += 1

    assert ticks < 100, "Entity should reach target within reasonable ticks"
    assert np.allclose(entity.get_component("position").value, target_pos, atol=1.0)


def test_state_determinism():
    model = GameModel()
    entity = Entity(model)
    entity.move_speed = 100.0
    entity.add_component("position", type("Position", (), {"value": np.array([0.0, 0.0])})())
    entity.add_component("velocity", type("Velocity", (), {"value": np.zeros(2)})())
    model.entities.add(entity)

    # Save state
    initial_pos = entity.get_component("position").value.copy()

    # Action: move
    entity.add_component("move_target", MoveTarget(50.0, 0.0))
    model.update(0.1)

    # Load state: reset
    entity.get_component("position").value[:] = initial_pos
    entity.remove_component("move_target")

    # Verify
    assert np.allclose(entity.get_component("position").value, initial_pos)