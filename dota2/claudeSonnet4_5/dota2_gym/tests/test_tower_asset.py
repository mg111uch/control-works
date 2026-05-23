"""
Tests for tower asset loading
"""
import pytest
import pygame
from pathlib import Path


class TestTowerAssetLoading:
    """Test tower asset loading functionality"""
    
    def setup_method(self):
        """Setup before each test"""
        pygame.init()
        self.screen = pygame.Surface((1280, 720))
    
    def teardown_method(self):
        """Cleanup after each test"""
        pygame.quit()
    
    def test_radiant_tower_asset_exists(self):
        """Test that radiant tower asset file exists"""
        tower_path = Path(__file__).parent.parent / 'assets' / 'entity' / 'radiant_tower.png'
        assert tower_path.exists(), f"Radiant tower asset not found at {tower_path}"
    
    def test_radiant_tower_asset_loads_successfully(self):
        """Test that radiant tower asset can be loaded as pygame surface"""
        tower_path = Path(__file__).parent.parent / 'assets' / 'entity' / 'radiant_tower.png'
        assert tower_path.exists(), "Radiant tower asset file does not exist"
        
        tower_surface = pygame.image.load(str(tower_path))
        assert tower_surface is not None, "Failed to load tower surface"
        assert isinstance(tower_surface, pygame.Surface), "Loaded object is not a pygame Surface"
    
    def test_entity_renderer_has_tower_asset(self):
        """Test that EntityMainRenderer can load and use tower assets"""
        from view.dota2_view.entities_main import EntityMainRenderer
        
        font_tiny = pygame.font.Font(None, 14)
        font_small = pygame.font.Font(None, 18)
        
        renderer = EntityMainRenderer(self.screen, font_tiny, font_small)
        
        tower_path = Path(__file__).parent.parent / 'assets' / 'entity' / 'radiant_tower.png'
        if tower_path.exists():
            renderer.load_tower_asset('radiant', str(tower_path))
            assert renderer.tower_assets is not None, "Tower assets dict should be initialized"
            assert 'radiant' in renderer.tower_assets, "Radiant tower should be in assets dict"
            assert renderer.tower_assets['radiant'] is not None, "Radiant tower surface should be loaded"
    
    def test_tower_asset_fallback_to_procedural(self):
        """Test that procedural rendering is used when tower asset is not available"""
        from view.dota2_view.entities_main import EntityMainRenderer
        from engine.config_loader import ConfigLoader
        from engine.model.game_model import GameModel
        
        config_loader = ConfigLoader()
        config = config_loader.load_game_config('config/game_config.yaml')
        
        game_model = GameModel(config)
        game_model.initialize_game()
        
        font_tiny = pygame.font.Font(None, 14)
        font_small = pygame.font.Font(None, 18)
        
        renderer = EntityMainRenderer(self.screen, font_tiny, font_small)
        
        renderer.load_tower_asset('radiant', '/nonexistent/path/radiant_tower.png')
        assert renderer.tower_assets.get('radiant') is None, "Radiant tower should be None when file not found"
    
    def test_tower_rendering_uses_asset(self):
        """Test that towers are rendered with asset when available"""
        from view.dota2_view.entities_main import EntityMainRenderer
        from engine.config_loader import ConfigLoader
        from engine.model.game_model import GameModel
        from view.dota2_view.camera import Camera
        
        config_loader = ConfigLoader()
        config = config_loader.load_game_config('config/game_config.yaml')
        
        game_model = GameModel(config)
        game_model.initialize_game()
        
        font_tiny = pygame.font.Font(None, 14)
        font_small = pygame.font.Font(None, 18)
        
        renderer = EntityMainRenderer(self.screen, font_tiny, font_small)
        
        tower_path = Path(__file__).parent.parent / 'assets' / 'entity' / 'radiant_tower.png'
        if tower_path.exists():
            renderer.load_tower_asset('radiant', str(tower_path))
            assert renderer.tower_assets.get('radiant') is not None, "Radiant tower should be loaded"
            
            camera = Camera(self.screen, config, config['game']['map_width'], config['game']['map_height'])
            world_to_screen = camera.world_to_screen
            
            em = game_model.entity_manager
            
            renderer.render_towers(em, world_to_screen, self.screen.get_width(), self.screen.get_height())
