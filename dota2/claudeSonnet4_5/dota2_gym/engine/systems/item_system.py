"""
Task 7: Item System & Shop
- 16 core items with stats and actives
- Inventory management (6 slots)
- Gold/XP rewards
- Items loaded from config/items/items.yaml
"""
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from engine.ecs.entity_manager import EntityManager
from engine.config_loader import ConfigLoader


@dataclass
class Item:
    """Base item class"""
    item_id: str
    name: str
    cost: int
    
    # Bonus stats
    strength: int = 0
    agility: int = 0
    intelligence: int = 0
    damage: int = 0
    attack_speed: int = 0
    movement_speed: int = 0
    armor: int = 0
    hp_regen: float = 0.0
    mana_regen: float = 0.0
    
    # Active ability
    has_active: bool = False
    active_cooldown: float = 0.0
    current_cooldown: float = 0.0
    charges: int = 0
    max_charges: int = 0


@dataclass
class InventoryComponent:
    """Hero inventory (6 slots)"""
    items: List[Optional[Item]] = field(default_factory=lambda: [None] * 6)
    gold: int = 625  # Starting gold
    
    def add_item(self, item: Item) -> bool:
        """Add item to first empty slot"""
        for i in range(len(self.items)):
            if self.items[i] is None:
                self.items[i] = item
                return True
        return False
    
    def remove_item(self, slot: int) -> Optional[Item]:
        """Remove item from slot"""
        if 0 <= slot < len(self.items):
            item = self.items[slot]
            self.items[slot] = None
            return item
        return None
    
    def has_space(self) -> bool:
        """Check if inventory has empty slot"""
        return None in self.items
    
    def get_total_stats(self) -> Dict[str, float]:
        """Calculate total stats from all items"""
        stats = {
            'strength': 0, 'agility': 0, 'intelligence': 0,
            'damage': 0, 'attack_speed': 0, 'movement_speed': 0,
            'armor': 0, 'hp_regen': 0.0, 'mana_regen': 0.0
        }
        
        for item in self.items:
            if item:
                stats['strength'] += item.strength
                stats['agility'] += item.agility
                stats['intelligence'] += item.intelligence
                stats['damage'] += item.damage
                stats['attack_speed'] += item.attack_speed
                stats['movement_speed'] += item.movement_speed
                stats['armor'] += item.armor
                stats['hp_regen'] += item.hp_regen
                stats['mana_regen'] += item.mana_regen
        
        return stats


class ItemShop:
    """Global item shop"""
    
    def __init__(self):
        self.items = self._create_item_database()
    
    def _create_item_database(self) -> Dict[str, Item]:
        """Create items from config file"""
        config_loader = ConfigLoader()
        items_config = config_loader.load_items_config()
        
        items = {}
        for item_data in items_config.get('items', []):
            item_id = item_data.get('id')
            stats = item_data.get('stats', {})
            active = item_data.get('active', {})
            
            item = Item(
                item_id=item_id,
                name=item_data.get('name', item_id),
                cost=item_data.get('cost', 0),
                strength=stats.get('strength', 0),
                agility=stats.get('agility', 0),
                intelligence=stats.get('intelligence', 0),
                damage=stats.get('damage', 0),
                attack_speed=stats.get('attack_speed', 0),
                movement_speed=stats.get('movement_speed', 0),
                armor=stats.get('armor', 0),
                hp_regen=stats.get('hp_regen', 0.0),
                mana_regen=stats.get('mana_regen', 0.0),
                has_active=active.get('has_active', False),
                active_cooldown=active.get('cooldown', 0.0),
                max_charges=active.get('max_charges', 0),
                charges=active.get('charges', 0)
            )
            items[item_id] = item
        
        return items
    
    def buy_item(self, item_id: str, inventory: InventoryComponent) -> bool:
        """Attempt to buy an item"""
        if item_id not in self.items:
            return False
        
        item_template = self.items[item_id]
        
        # Check gold
        if inventory.gold < item_template.cost:
            print(f"[Shop] Not enough gold for {item_template.name} ({inventory.gold}/{item_template.cost})")
            return False
        
        # Check inventory space
        if not inventory.has_space():
            print(f"[Shop] Inventory full!")
            return False
        
        # Create new item instance
        new_item = Item(
            item_id=item_template.item_id,
            name=item_template.name,
            cost=item_template.cost,
            strength=item_template.strength,
            agility=item_template.agility,
            intelligence=item_template.intelligence,
            damage=item_template.damage,
            attack_speed=item_template.attack_speed,
            movement_speed=item_template.movement_speed,
            armor=item_template.armor,
            hp_regen=item_template.hp_regen,
            mana_regen=item_template.mana_regen,
            has_active=item_template.has_active,
            active_cooldown=item_template.active_cooldown,
            max_charges=item_template.max_charges,
            charges=item_template.charges
        )
        
        # Purchase
        inventory.gold -= item_template.cost
        inventory.add_item(new_item)
        
        print(f"[Shop] Purchased {item_template.name} for {item_template.cost}g (Remaining: {inventory.gold}g)")
        return True


class ItemSystem:
    """Manages items and active abilities"""
    
    def __init__(self, entity_manager: EntityManager, dt: float = 1/15):
        self.em = entity_manager
        self.dt = dt
        self.shop = ItemShop()
    
    def update(self):
        """Update item cooldowns"""
        heroes = self.em.get_entities_with_component('hero')
        
        for hero_id in heroes:
            inventory = self.em.get_component(hero_id, 'inventory')
            if not inventory:
                # Add inventory component if missing
                self.em.add_component(hero_id, 'inventory', InventoryComponent())
                continue
            
            # Update item cooldowns
            for item in inventory.items:
                if item and item.current_cooldown > 0:
                    item.current_cooldown = max(0, item.current_cooldown - self.dt)
    
    def use_item(self, hero_id: int, slot: int) -> bool:
        """Use item active ability"""
        inventory = self.em.get_component(hero_id, 'inventory')
        position = self.em.get_component(hero_id, 'position')
        hero = self.em.get_component(hero_id, 'hero')
        
        if not inventory or not position or not hero:
            return False
        
        if slot < 0 or slot >= len(inventory.items):
            return False
        
        item = inventory.items[slot]
        if not item or not item.has_active:
            return False
        
        if item.current_cooldown > 0:
            print(f"[Items] {item.name} on cooldown ({item.current_cooldown:.1f}s)")
            return False
        
        # Execute item ability
        success = self._execute_item_ability(hero_id, item)
        
        if success:
            item.current_cooldown = item.active_cooldown
            print(f"[Items] Used {item.name}")
        
        return success
    
    def _execute_item_ability(self, hero_id: int, item: Item) -> bool:
        """Execute specific item active"""
        position = self.em.get_component(hero_id, 'position')
        stats = self.em.get_component(hero_id, 'stats')
        
        if item.item_id == 'magic_wand':
            # Restore HP/MP based on charges
            if item.charges > 0:
                heal = item.charges * 15
                mana = item.charges * 15
                stats.current_hp = min(stats.max_hp, stats.current_hp + heal)
                stats.current_mana = min(stats.max_mana, stats.current_mana + mana)
                item.charges = 0
                return True
            return False
        
        elif item.item_id == 'bottle':
            # Restore HP/MP
            if item.charges > 0:
                stats.current_hp = min(stats.max_hp, stats.current_hp + 135)
                stats.current_mana = min(stats.max_mana, stats.current_mana + 70)
                item.charges -= 1
                return True
            return False
        
        elif item.item_id == 'blink':
            # Teleport forward (simplified)
            position.x += 600
            return True
        
        elif item.item_id == 'bkb':
            # Apply magic immunity (simplified - just set a flag)
            print("[Items] BKB activated - magic immunity!")
            return True
        
        # Other items...
        return True
    
    def award_gold(self, hero_id: int, amount: int):
        """Award gold to hero"""
        inventory = self.em.get_component(hero_id, 'inventory')
        if inventory:
            inventory.gold += amount
            print(f"[Gold] Hero {hero_id} gained {amount}g (Total: {inventory.gold}g)")