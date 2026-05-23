"""
Task 6: Shadow Fiend Abilities (QWE + R)
- Shadowraze (3 ranges)
- Requiem of Souls
- Cooldown system
"""
import numpy as np
from dataclasses import dataclass
from typing import Optional, List
from engine.ecs.entity_manager import EntityManager
from engine.ecs.components import *


@dataclass
class AbilityComponent:
    """Ability cooldown tracking"""
    q_cooldown: float = 0.0
    w_cooldown: float = 0.0
    e_cooldown: float = 0.0
    r_cooldown: float = 0.0
    
    q_ready: bool = True
    w_ready: bool = True
    e_ready: bool = True
    r_ready: bool = True


class AbilitySystem:
    """Handles ability casting and effects"""
    
    def __init__(self, entity_manager: EntityManager, dt: float = 1/15):
        self.em = entity_manager
        self.dt = dt
        
        # Shadowraze config
        self.raze_cooldown = 10.0
        self.raze_mana_cost = 90
        self.raze_damage = 100
        self.raze_radius = 250
        
        # Raze distances from hero
        self.raze_near = 200
        self.raze_medium = 450
        self.raze_far = 700
        
        # Requiem config
        self.requiem_cooldown = 120.0
        self.requiem_mana_cost = 150
        self.requiem_base_lines = 18
        self.requiem_lines_per_soul = 0.5
        self.requiem_damage_per_line = 80
        self.requiem_radius = 1000
    
    def update(self):
        """Update ability cooldowns"""
        heroes = self.em.get_entities_with_component('hero')
        
        for hero_id in heroes:
            abilities = self.em.get_component(hero_id, 'ability')
            if not abilities:
                # Add ability component if missing
                self.em.add_component(hero_id, 'ability', AbilityComponent())
                abilities = self.em.get_component(hero_id, 'ability')
            
            # Update cooldowns
            if abilities.q_cooldown > 0:
                abilities.q_cooldown = max(0, abilities.q_cooldown - self.dt)
                abilities.q_ready = abilities.q_cooldown <= 0
            
            if abilities.w_cooldown > 0:
                abilities.w_cooldown = max(0, abilities.w_cooldown - self.dt)
                abilities.w_ready = abilities.w_cooldown <= 0
            
            if abilities.e_cooldown > 0:
                abilities.e_cooldown = max(0, abilities.e_cooldown - self.dt)
                abilities.e_ready = abilities.e_cooldown <= 0
            
            if abilities.r_cooldown > 0:
                abilities.r_cooldown = max(0, abilities.r_cooldown - self.dt)
                abilities.r_ready = abilities.r_cooldown <= 0
    
    def cast_shadowraze(self, hero_id: int, raze_type: str) -> bool:
        """
        Cast Shadowraze
        raze_type: 'near', 'medium', or 'far'
        """
        hero = self.em.get_component(hero_id, 'hero')
        position = self.em.get_component(hero_id, 'position')
        stats = self.em.get_component(hero_id, 'stats')
        abilities = self.em.get_component(hero_id, 'ability')
        
        if not all([hero, position, stats, abilities]):
            return False
        
        # Determine which ability slot to use
        if raze_type == 'near':
            ready = abilities.q_ready
            cooldown_attr = 'q_cooldown'
            ready_attr = 'q_ready'
        elif raze_type == 'medium':
            ready = abilities.w_ready
            cooldown_attr = 'w_cooldown'
            ready_attr = 'w_ready'
        elif raze_type == 'far':
            ready = abilities.e_ready
            cooldown_attr = 'e_cooldown'
            ready_attr = 'e_ready'
        else:
            return False
        
        # Check cooldown and mana
        if not ready or stats.current_mana < self.raze_mana_cost:
            return False
        
        # Consume mana
        stats.current_mana -= self.raze_mana_cost
        
        # Set cooldown
        setattr(abilities, cooldown_attr, self.raze_cooldown)
        setattr(abilities, ready_attr, False)
        
        # Determine raze distance
        if raze_type == 'near':
            distance = self.raze_near
        elif raze_type == 'medium':
            distance = self.raze_medium
        else:  # far
            distance = self.raze_far
        
        # Calculate raze position (in front of hero)
        # For simplicity, assume hero facing right
        raze_x = position.x + distance
        raze_y = position.y
        
        # Apply damage in AOE
        self._apply_aoe_damage(raze_x, raze_y, self.raze_radius, 
                              self.raze_damage, hero.team)
        
        print(f"[Abilities] Shadowraze ({raze_type}) cast at ({raze_x:.0f}, {raze_y:.0f})")
        return True
    
    def cast_requiem(self, hero_id: int) -> bool:
        """Cast Requiem of Souls"""
        hero = self.em.get_component(hero_id, 'hero')
        position = self.em.get_component(hero_id, 'position')
        stats = self.em.get_component(hero_id, 'stats')
        abilities = self.em.get_component(hero_id, 'ability')
        
        if not all([hero, position, stats, abilities]):
            return False
        
        # Check cooldown and mana
        if not abilities.r_ready or stats.current_mana < self.requiem_mana_cost:
            return False
        
        # Consume mana
        stats.current_mana -= self.requiem_mana_cost
        
        # Set cooldown
        abilities.r_cooldown = self.requiem_cooldown
        abilities.r_ready = False
        
        # Calculate lines based on souls
        num_lines = int(self.requiem_base_lines + hero.souls * self.requiem_lines_per_soul)
        damage_per_line = self.requiem_damage_per_line
        
        # Apply damage (simplified - circular AOE)
        total_damage = num_lines * damage_per_line * 0.5  # Reduced for balance
        self._apply_aoe_damage(position.x, position.y, self.requiem_radius,
                              total_damage, hero.team)
        
        # Lose half of souls
        souls_lost = hero.souls // 2
        hero.souls -= souls_lost
        
        print(f"[Abilities] Requiem cast! {num_lines} lines, lost {souls_lost} souls")
        return True
    
    def _apply_aoe_damage(self, x: float, y: float, radius: float, 
                         damage: float, caster_team: int):
        """Apply damage to all enemies in AOE"""
        center = PositionComponent(x, y)
        
        # Check all entities
        for entity_id in self.em.get_all_entities():
            position = self.em.get_component(entity_id, 'position')
            stats = self.em.get_component(entity_id, 'stats')
            
            if not position or not stats or not stats.is_alive():
                continue
            
            # Check team
            hero = self.em.get_component(entity_id, 'hero')
            creep = self.em.get_component(entity_id, 'creep')
            
            target_team = -1
            if hero:
                target_team = hero.team
            elif creep:
                target_team = creep.team
            
            if target_team == caster_team:
                continue  # Don't damage allies
            
            # Check distance
            distance = center.distance_to(position)
            if distance <= radius:
                # Apply damage
                actual_damage = stats.take_damage(damage)
                print(f"  [AOE] Hit entity {entity_id} for {actual_damage:.0f} damage")


class AbilityUI:
    """Render ability cooldowns"""
    
    @staticmethod
    def render(screen, font, hero_id, ability_component, x: int, y: int):
        """Render ability cooldown UI"""
        import pygame
        
        abilities = [
            ('Q', ability_component.q_cooldown, ability_component.q_ready),
            ('W', ability_component.w_cooldown, ability_component.w_ready),
            ('E', ability_component.e_cooldown, ability_component.e_ready),
            ('R', ability_component.r_cooldown, ability_component.r_ready)
        ]
        
        ability_size = 40
        spacing = 50
        
        for i, (key, cooldown, ready) in enumerate(abilities):
            pos_x = x + i * spacing
            
            # Background
            color = (50, 200, 50) if ready else (100, 100, 100)
            pygame.draw.rect(screen, color, (pos_x, y, ability_size, ability_size))
            pygame.draw.rect(screen, (200, 200, 200), (pos_x, y, ability_size, ability_size), 2)
            
            # Key letter
            text = font.render(key, True, (255, 255, 255))
            text_rect = text.get_rect(center=(pos_x + ability_size // 2, y + ability_size // 2))
            screen.blit(text, text_rect)
            
            # Cooldown timer
            if not ready:
                cd_text = font.render(f"{cooldown:.1f}", True, (255, 200, 200))
                cd_rect = cd_text.get_rect(center=(pos_x + ability_size // 2, y + ability_size + 10))
                screen.blit(cd_text, cd_rect)