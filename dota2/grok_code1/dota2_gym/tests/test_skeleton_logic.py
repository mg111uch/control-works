import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'

import pytest
import numpy as np
from config.loader import ConfigLoader
from engine.model.ecs.entity import EntityManager, Entity, Component

def test_config_loading():
    loader = ConfigLoader()
    assert 'game' in loader.constants
    assert 'hero' in loader.constants
    assert 'name' in loader.hero_data
    assert loader.hero_data['name'] == 'Shadow Fiend'
    assert 'wraith_band' in loader.items_data
    assert loader.items_data['wraith_band']['cost'] == 505

def test_ecs_create_destroy_entity():
    # Mock model
    class MockModel:
        pass
    model = MockModel()
    manager = EntityManager()

    # Create entity
    entity = Entity(model)
    manager.add(entity)
    assert len(manager.all()) == 1
    assert manager.find_by_id(entity.id) == entity

    # Add component
    comp = Component(value=42)
    entity.add_component('test', comp)
    assert entity.get_component('test').value == 42

    # Destroy entity
    manager.remove(entity)
    assert len(manager.all()) == 0
    assert manager.find_by_id(entity.id) is None

def test_state_determinism():
    # Save state -> Action -> Load state -> Verify equality
    loader = ConfigLoader()
    manager = EntityManager()
    class MockModel:
        pass
    model = MockModel()

    # Initial state
    entity = Entity(model)
    entity.add_component('position', Component(x=10, y=20))
    manager.add(entity)
    initial_state = str(manager.all())

    # Action: modify
    entity.get_component('position').x = 30

    # Load state: reset
    entity.get_component('position').x = 10
    loaded_state = str(manager.all())

    assert initial_state == loaded_state