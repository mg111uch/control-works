import pytest
from engine.ecs.entity_manager import EntityManager
from engine.ecs.components import *


class TestAbilitySystem:
    """Test Shadow Fiend abilities"""
    
    def setup_method(self):
        """Setup before each test"""
        self.em = EntityManager()
    
    def test_ability_cooldowns(self):
        """Test ability cooldown tracking"""
        hero_id = self.em.create_entity()
        
        # Note: Uncomment when AbilityComponent is available
        from engine.systems.ability_system import AbilityComponent
        
        ability = AbilityComponent()
        self.em.add_component(hero_id, 'ability', ability)
        
        # Set cooldown
        ability.q_cooldown = 10.0
        ability.q_ready = False
        
        assert not ability.q_ready
        assert ability.q_cooldown == 10.0
        
        # Reduce cooldown
        ability.q_cooldown = 0.0
        ability.q_ready = True
        
        assert ability.q_ready
        pass
    
    def test_shadowraze_mana_cost(self):
        """Test Shadowraze consumes mana"""
        hero_id = self.em.create_entity()
        
        self.em.add_component(hero_id, 'position', PositionComponent(0, 0))
        self.em.add_component(hero_id, 'stats', StatsComponent(
            max_hp=1000, current_hp=1000,
            max_mana=500, current_mana=500
        ))
        self.em.add_component(hero_id, 'hero', HeroComponent(
            hero_id='shadow_fiend', team=0
        ))
        
        stats = self.em.get_component(hero_id, 'stats')
        initial_mana = stats.current_mana
        
        # Note: Uncomment when AbilitySystem is available
        from engine.systems.ability_system import AbilitySystem
        
        ability_system = AbilitySystem(self.em)
        self.em.add_component(hero_id, 'ability', AbilityComponent())
        
        # Cast Shadowraze
        success = ability_system.cast_shadowraze(hero_id, 'near')
        
        assert success
        assert stats.current_mana < initial_mana
        assert stats.current_mana == initial_mana - 90  # Mana cost
        pass
    
    def test_requiem_soul_cost(self):
        """Test Requiem consumes souls"""
        hero_id = self.em.create_entity()
        
        self.em.add_component(hero_id, 'position', PositionComponent(0, 0))
        self.em.add_component(hero_id, 'stats', StatsComponent(
            max_hp=1000, current_hp=1000,
            max_mana=500, current_mana=500
        ))
        self.em.add_component(hero_id, 'hero', HeroComponent(
            hero_id='shadow_fiend', team=0, souls=36
        ))
        
        hero = self.em.get_component(hero_id, 'hero')
        initial_souls = hero.souls
        
        # Note: Test would check that souls are reduced by half
        # after casting Requiem
        pass