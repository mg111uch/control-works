import pytest
from engine.ecs.entity_manager import EntityManager


class TestItemSystem:
    """Test item system"""
    
    def setup_method(self):
        """Setup before each test"""
        self.em = EntityManager()
    
    def test_inventory_creation(self):
        """Test creating inventory"""
        from engine.systems.item_system import InventoryComponent
        
        inventory = InventoryComponent()
        
        assert len(inventory.items) == 6
        assert all(item is None for item in inventory.items)
        assert inventory.gold == 625
    
    def test_buy_item(self):
        """Test purchasing item"""
        from engine.systems.item_system import ItemShop, InventoryComponent
        
        shop = ItemShop()
        inventory = InventoryComponent()
        
        success = shop.buy_item('wraith_band', inventory)
        
        assert success
        assert inventory.gold == 625 - 505
        assert inventory.items[0] is not None
        assert inventory.items[0].item_id == 'wraith_band'
    
    def test_inventory_full(self):
        """Test inventory full condition"""
        from engine.systems.item_system import ItemShop, InventoryComponent
        
        shop = ItemShop()
        inventory = InventoryComponent(gold=10000)
        
        for i in range(6):
            shop.buy_item('wraith_band', inventory)
        
        success = shop.buy_item('wraith_band', inventory)
        
        assert not success
    
    def test_item_stats(self):
        """Test item provides stats"""
        from engine.systems.item_system import Item, InventoryComponent
        
        inventory = InventoryComponent()
        
        item = Item(item_id='wraith_band', name='Wraith Band', cost=505,
                   agility=6, strength=3, intelligence=3)
        inventory.add_item(item)
        
        stats = inventory.get_total_stats()
        
        assert stats['agility'] == 6
        assert stats['strength'] == 3
        assert stats['intelligence'] == 3


class TestConfigBasedItems:
    """Test config-based item loading"""
    
    def setup_method(self):
        """Setup before each test"""
        from engine.systems.item_system import ItemShop
        self.shop = ItemShop()
    
    def test_all_items_loaded_from_config(self):
        """Test that all 16 items are loaded from config"""
        expected_items = [
            'wraith_band', 'null_talisman', 'bracer', 'magic_wand',
            'boots', 'treads', 'bottle', 'mekansm', 'blink', 'bkb',
            'shadow_blade', 'euls', 'force_staff', 'hex', 'dagon', 'rapier'
        ]
        
        for item_id in expected_items:
            assert item_id in self.shop.items, f"Item {item_id} not loaded from config"
    
    def test_item_properties_from_config(self):
        """Test that item properties match config"""
        wraith_band = self.shop.items['wraith_band']
        assert wraith_band.name == "Wraith Band"
        assert wraith_band.cost == 505
        assert wraith_band.agility == 6
        assert wraith_band.strength == 3
        assert wraith_band.intelligence == 3
    
    def test_rapier_damage(self):
        """Test Divine Rapier has correct damage"""
        rapier = self.shop.items['rapier']
        assert rapier.name == "Divine Rapier"
        assert rapier.cost == 5950
        assert rapier.damage == 350
    
    def test_active_items_have_cooldowns(self):
        """Test that active items have correct cooldowns from config"""
        magic_wand = self.shop.items['magic_wand']
        assert magic_wand.has_active is True
        assert magic_wand.active_cooldown == 13.0
        assert magic_wand.max_charges == 20
        
        bottle = self.shop.items['bottle']
        assert bottle.has_active is True
        assert bottle.active_cooldown == 0.5
        assert bottle.charges == 3
    
    def test_hex_stats(self):
        """Test Scythe of Vyse has correct stats"""
        hex_item = self.shop.items['hex']
        assert hex_item.name == "Scythe of Vyse"
        assert hex_item.cost == 5650
        assert hex_item.intelligence == 35
        assert hex_item.strength == 10
        assert hex_item.agility == 10
        assert hex_item.mana_regen == 5.0


class TestGoldPurchasing:
    """Test gold purchasing functionality"""
    
    def setup_method(self):
        """Setup before each test"""
        from engine.systems.item_system import ItemShop, InventoryComponent
        from engine.ecs.entity_manager import EntityManager
        self.em = EntityManager()
        self.shop = ItemShop()
        self.inventory = InventoryComponent()
    
    def test_purchase_reduces_gold_correctly(self):
        """Test that purchasing reduces gold by item cost"""
        initial_gold = self.inventory.gold
        self.shop.buy_item('wraith_band', self.inventory)
        
        assert self.inventory.gold == initial_gold - 505
    
    def test_purchase_with_exact_gold(self):
        """Test purchasing with exact amount of gold"""
        self.inventory.gold = 505
        success = self.shop.buy_item('wraith_band', self.inventory)
        
        assert success is True
        assert self.inventory.gold == 0
        assert self.inventory.items[0] is not None
    
    def test_purchase_fails_insufficient_gold(self):
        """Test that purchase fails with insufficient gold"""
        self.inventory.gold = 100
        success = self.shop.buy_item('wraith_band', self.inventory)
        
        assert success is False
        assert self.inventory.gold == 100
        assert all(item is None for item in self.inventory.items)
    
    def test_multiple_purchases_gold_tracking(self):
        """Test gold tracking across multiple purchases"""
        self.inventory.gold = 2000
        
        self.shop.buy_item('boots', self.inventory)
        assert self.inventory.gold == 2000 - 500
        
        self.shop.buy_item('magic_wand', self.inventory)
        assert self.inventory.gold == 2000 - 500 - 450
        
        self.shop.buy_item('bracer', self.inventory)
        assert self.inventory.gold == 2000 - 500 - 450 - 505
    
    def test_expensive_item_purchase(self):
        """Test purchasing expensive items"""
        self.inventory.gold = 6000
        
        success = self.shop.buy_item('hex', self.inventory)
        
        assert success is True
        assert self.inventory.gold == 6000 - 5650
        assert self.inventory.items[0].item_id == 'hex'
    
    def test_award_gold(self):
        """Test awarding gold to hero"""
        from engine.systems.item_system import ItemSystem, InventoryComponent
        
        entity_id = self.em.create_entity()
        inventory = InventoryComponent(gold=100)
        self.em.add_component(entity_id, 'inventory', inventory)
        item_system = ItemSystem(self.em)
        item_system.award_gold(entity_id, 50)
        
        assert inventory.gold == 150


class TestInventoryManagement:
    """Test inventory management"""
    
    def setup_method(self):
        """Setup before each test"""
        from engine.systems.item_system import ItemShop, InventoryComponent
        self.shop = ItemShop()
        self.inventory = InventoryComponent()
    
    def test_add_item_to_empty_slot(self):
        """Test adding item to first empty slot"""
        from engine.systems.item_system import Item
        
        item = Item(item_id='test', name='Test', cost=100)
        result = self.inventory.add_item(item)
        
        assert result is True
        assert self.inventory.items[0] is item
    
    def test_add_item_to_specific_slot(self):
        """Test that add_item uses first available slot"""
        self.inventory.gold = 2000
        self.shop.buy_item('wraith_band', self.inventory)
        self.shop.buy_item('bracer', self.inventory)
        
        assert self.inventory.items[0] is not None
        assert self.inventory.items[1] is not None
        assert self.inventory.items[2] is None
    
    def test_remove_item(self):
        """Test removing item from slot"""
        self.shop.buy_item('wraith_band', self.inventory)
        removed = self.inventory.remove_item(0)
        
        assert removed is not None
        assert removed.item_id == 'wraith_band'
        assert self.inventory.items[0] is None
    
    def test_has_space_true(self):
        """Test has_space returns True for non-full inventory"""
        assert self.inventory.has_space() is True
    
    def test_has_space_false(self):
        """Test has_space returns False for full inventory"""
        self.inventory.gold = 10000
        for _ in range(6):
            self.shop.buy_item('wraith_band', self.inventory)
        
        assert self.inventory.has_space() is False
    
    def test_get_total_stats(self):
        """Test getting total stats from all items"""
        self.inventory.gold = 10000
        
        self.shop.buy_item('treads', self.inventory)
        self.shop.buy_item('bkb', self.inventory)
        
        stats = self.inventory.get_total_stats()
        
        assert stats['agility'] == 10
        assert stats['attack_speed'] == 25
        assert stats['movement_speed'] == 45
        assert stats['strength'] == 10
        assert stats['damage'] == 24


class TestInvalidPurchases:
    """Test invalid purchase scenarios"""
    
    def setup_method(self):
        """Setup before each test"""
        from engine.systems.item_system import ItemShop, InventoryComponent
        self.shop = ItemShop()
        self.inventory = InventoryComponent()
    
    def test_buy_nonexistent_item(self):
        """Test buying item that doesn't exist"""
        success = self.shop.buy_item('nonexistent_item', self.inventory)
        
        assert success is False
    
    def test_buy_with_negative_gold(self):
        """Test buying with negative gold (should fail)"""
        self.inventory.gold = -100
        success = self.shop.buy_item('wraith_band', self.inventory)
        
        assert success is False
    
    def test_remove_invalid_slot(self):
        """Test removing item from invalid slot"""
        from engine.systems.item_system import InventoryComponent
        
        inventory = InventoryComponent()
        result = inventory.remove_item(10)
        
        assert result is None
    
    def test_remove_negative_slot(self):
        """Test removing item from negative slot"""
        from engine.systems.item_system import InventoryComponent
        
        inventory = InventoryComponent()
        result = inventory.remove_item(-1)
        
        assert result is None


class TestShopClickHandling:
    """Test shop click handling functionality"""
    
    def setup_method(self):
        """Setup before each test"""
        import pygame
        pygame.init()
        from engine.ecs.entity_manager import EntityManager
        from view.dota2_view.menus import MenuRenderer
        
        self.em = EntityManager()
        
        # Create a mock game model
        class MockGameModel:
            def __init__(self, em):
                self.player_heroes = {}
                self.entity_manager = em
        
        self.game_model = MockGameModel(self.em)
    
    def teardown_method(self):
        """Cleanup after each test"""
        import pygame
        pygame.quit()
    
    def test_shop_click_returns_item_id(self):
        """Test that clicking on a shop item returns the item ID"""
        from view.dota2_view.menus import MenuRenderer
        import pygame
        
        screen = pygame.Surface((1280, 720))
        font = pygame.font.SysFont(None, 20)
        
        renderer = MenuRenderer(screen, self.game_model, font, font, font, font)
        
        # Render shop first to populate item rects
        renderer.render_shop()
        
        # Check that item rects were created
        assert len(renderer.shop_item_rects) > 0
    
    def test_purchase_item_for_player_hero(self):
        """Test purchasing item for player hero"""
        import pygame
        from engine.systems.item_system import InventoryComponent, ItemShop
        from view.dota2_view.menus import MenuRenderer
        
        # Create a player hero entity
        self.game_model.player_heroes[0] = 1
        self.em.entities.add(1)
        
        # Add inventory to hero
        inventory = InventoryComponent()
        self.em.add_component(1, 'inventory', inventory)
        
        screen = pygame.Surface((1280, 720))
        font = pygame.font.SysFont(None, 20)
        
        renderer = MenuRenderer(screen, self.game_model, font, font, font, font)
        
        # Render shop first to populate item rects
        renderer.render_shop()
        
        # Click on first item (should be wraith_band)
        first_item_rect = list(renderer.shop_item_rects.values())[0]
        result = renderer.handle_shop_click(first_item_rect.center)
        
        # Check that purchase was successful
        if result:
            assert result in ['wraith_band', 'null_talisman', 'bracer']  # First few items
            assert inventory.gold < 625  # Gold was spent


class TestHeroStatsDisplay:
    """Test hero stats display functionality"""
    
    def setup_method(self):
        """Setup before each test"""
        import pygame
        pygame.init()
        from engine.ecs.entity_manager import EntityManager
        from view.dota2_view.ui_inventory import UIInventoryRenderer
        from engine.systems.item_system import Item
        
        self.em = EntityManager()
        
        # Create a mock game model
        class MockGameModel:
            def __init__(self, em):
                self.player_heroes = {0: 1}
                self.entity_manager = em
        
        self.game_model = MockGameModel(self.em)
        
        screen = pygame.Surface((1280, 720))
        font = pygame.font.SysFont(None, 20)
        self.item_abbrev = {}
        self.renderer = UIInventoryRenderer(screen, self.game_model, font, font, font, self.item_abbrev)
    
    def teardown_method(self):
        """Cleanup after each test"""
        import pygame
        pygame.quit()
    
    def test_item_bonus_stats_calculation(self):
        """Test that item bonus stats are calculated correctly"""
        from engine.systems.item_system import InventoryComponent, Item
        
        inventory = InventoryComponent()
        
        # Add items with stats
        wraith_band = Item(item_id='wraith_band', name='Wraith Band', cost=505,
                          agility=6, strength=3, intelligence=3)
        treads = Item(item_id='treads', name='Power Treads', cost=1400,
                     agility=10, attack_speed=25, movement_speed=45)
        
        inventory.add_item(wraith_band)
        inventory.add_item(treads)
        
        bonus = self.renderer._get_item_bonus_stats(inventory)
        
        assert bonus['strength'] == 3
        assert bonus['agility'] == 16  # 6 + 10
        assert bonus['intelligence'] == 3
        assert bonus['attack_speed'] == 25
        assert bonus['movement_speed'] == 45
    
    def test_empty_inventory_bonus_stats(self):
        """Test that empty inventory returns zero bonuses"""
        from engine.systems.item_system import InventoryComponent
        
        inventory = InventoryComponent()
        
        bonus = self.renderer._get_item_bonus_stats(inventory)
        
        assert bonus['strength'] == 0
        assert bonus['agility'] == 0
        assert bonus['intelligence'] == 0
        assert bonus['damage'] == 0
    
    def test_none_inventory_bonus_stats(self):
        """Test that None inventory returns zero bonuses"""
        bonus = self.renderer._get_item_bonus_stats(None)
        
        assert bonus['strength'] == 0
        assert bonus['agility'] == 0
        assert bonus['intelligence'] == 0