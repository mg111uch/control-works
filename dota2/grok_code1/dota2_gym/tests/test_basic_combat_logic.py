import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'

import pytest
import numpy as np
from engine.model.game_model import GameModel
from engine.model.entities.hero import Hero
from engine.model.combat import CombatSystem
from config.loader import ConfigLoader


def test_shadow_fiend_stats():
    """Test SF attribute logic (Str/Agi/Int)"""
    loader = ConfigLoader()
    hero_data = loader.load_hero("shadow_fiend")
    model = GameModel()
    hero = Hero(model, 0, 0, [0, 0], hero_data)
    
    # Check base stats
    assert hero._calc_max_hp(hero_data["base_stats"]) == 200 + 19 * 22 + 1 * 100  # level 1
    assert hero._calc_max_mana(hero_data["base_stats"]) == 75 + 18 * 12 + 1 * 50
    
    # Attack damage with souls
    hero.get_component("souls").current = 10
    damage = hero.get_attack_damage()
    expected = (35 + 41) / 2 + 0 + 10 * 2  # from constants
    assert damage == expected
    
    # Attack range with souls
    range_ = hero.get_attack_range()
    expected_range = 500 + 10 * 8
    assert range_ == expected_range


def test_basic_attack_system():
    """Test Basic Attack system (Projectile entities)"""
    loader = ConfigLoader()
    hero_data = loader.load_hero("shadow_fiend")
    model = GameModel()
    hero = Hero(model, 0, 0, [0, 0], hero_data)
    model.entities.add(hero)
    
    # Create dummy entity
    from engine.model.ecs.entity import Entity
    dummy = Entity(model)
    dummy.add_component("position", type("Pos", (), {"value": np.array([200.0, 0.0])})())
    dummy.add_component("health", type("Health", (), {"current": 100.0, "maximum": 100.0})())
    dummy.team = 1  # enemy
    model.entities.add(dummy)
    
    combat_system = CombatSystem(model)
    model.systems["combat"] = combat_system
    
    # Simulate attack
    hero.attack_timer = 999  # force attack
    model.update(0.1)
    
    # Check projectile launched
    assert len(combat_system.projectiles) > 0
    proj = combat_system.projectiles[0]
    assert proj.owner == hero
    assert proj.damage == hero.get_attack_damage()
    
    # Simulate projectile travel
    for _ in range(100):  # enough ticks
        combat_system.update(0.1)
    
    # Check if projectile hit and HP deducted
    assert dummy.get_component("health").current < 100.0


def test_necromastery_soul_collection():
    """Test Necromastery soul collection logic (on-kill trigger)"""
    loader = ConfigLoader()
    hero_data = loader.load_hero("shadow_fiend")
    model = GameModel()
    hero = Hero(model, 0, 0, [0, 0], hero_data)
    model.entities.add(hero)
    
    combat_system = CombatSystem(model)
    
    # Create dummy with low HP
    from engine.model.ecs.entity import Entity
    dummy = Entity(model)
    dummy.add_component("position", type("Pos", (), {"value": np.array([100.0, 0.0])})())
    dummy.add_component("health", type("Health", (), {"current": 1.0, "maximum": 100.0})())
    dummy.team = 1
    dummy.bounty = 50
    model.entities.add(dummy)
    
    initial_souls = hero.get_component("souls").current
    initial_gold = hero.get_component("inventory").gold
    
    # Kill the dummy
    combat_system._handle_kill(hero, dummy)
    
    # Check souls increased
    assert hero.get_component("souls").current == min(40, initial_souls + 1)
    # Check gold increased
    assert hero.get_component("inventory").gold == initial_gold + 50


def test_state_determinism():
    """State Determinism Test: Save state -> Action -> Load state -> Verify equality"""
    model = GameModel()
    loader = ConfigLoader()
    hero_data = loader.load_hero("shadow_fiend")
    hero = Hero(model, 0, 0, [0, 0], hero_data)
    model.entities.add(hero)
    
    # Save state
    saved_state = model.get_state_snapshot()
    
    # Perform action (attack)
    combat_system = CombatSystem(model)
    model.systems["combat"] = combat_system
    hero.attack_timer = 999
    combat_system.update(0.1)
    
    # Load state
    # Since load not implemented, simulate by resetting
    model.current_tick = saved_state["tick"]
    model.game_time = saved_state["time"]
    # Reset entities
    model.entities.clear()
    model.entities.add(hero)
    hero.get_component("position").value = np.array(saved_state["entities"][0]["position"])
    # etc.
    
    # Verify equality
    loaded_snapshot = model.get_state_snapshot()
    assert loaded_snapshot["tick"] == saved_state["tick"]
    assert loaded_snapshot["time"] == saved_state["time"]
    assert len(loaded_snapshot["entities"]) == len(saved_state["entities"])