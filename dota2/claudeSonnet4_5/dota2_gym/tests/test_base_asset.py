"""
Tests for base asset loading
"""
import pytest
import pygame
from pathlib import Path


class TestBaseAssetLoading:
    """Test base asset loading functionality"""
    
    def setup_method(self):
        """Setup before each test"""
        pygame.init()
        self.screen = pygame.Surface((1280, 720))
    
    def teardown_method(self):
        """Cleanup after each test"""
        pygame.quit()
    
    def test_radiant_base_asset_exists(self):
        """Test that radiant base asset file exists"""
        base_path = Path(__file__).parent.parent / 'assets' / 'entity' / 'radiant_base.png'
        assert base_path.exists(), f"Radiant base asset not found at {base_path}"
    
    def test_dire_base_asset_exists(self):
        """Test that dire base asset file exists"""
        base_path = Path(__file__).parent.parent / 'assets' / 'entity' / 'dire_base.png'
        assert base_path.exists(), f"Dire base asset not found at {base_path}"
    
    def test_radiant_base_asset_loads_successfully(self):
        """Test that radiant base asset can be loaded as pygame surface"""
        base_path = Path(__file__).parent.parent / 'assets' / 'entity' / 'radiant_base.png'
        assert base_path.exists(), "Radiant base asset file does not exist"
        
        base_surface = pygame.image.load(str(base_path))
        assert base_surface is not None, "Failed to load base surface"
        assert isinstance(base_surface, pygame.Surface), "Loaded object is not a pygame Surface"
    
    def test_dire_base_asset_loads_successfully(self):
        """Test that dire base asset can be loaded as pygame surface"""
        base_path = Path(__file__).parent.parent / 'assets' / 'entity' / 'dire_base.png'
        assert base_path.exists(), "Dire base asset file does not exist"
        
        base_surface = pygame.image.load(str(base_path))
        assert base_surface is not None, "Failed to load base surface"
        assert isinstance(base_surface, pygame.Surface), "Loaded object is not a pygame Surface"
    
    def test_dota2_view_has_base_asset_method(self):
        """Test that Dota2View has method to load base assets"""
        from view.dota2_view.dota2_view import Dota2View
        from engine.config_loader import ConfigLoader
        from engine.model.game_model import GameModel
        
        config_loader = ConfigLoader()
        config = config_loader.load_game_config('config/game_config.yaml')
        game_model = GameModel(config)
        
        view = Dota2View(self.screen, game_model)
        
        assert hasattr(view, '_load_base_assets'), "Dota2View should have _load_base_assets method"
        assert hasattr(view, 'base_assets'), "Dota2View should have base_assets attribute"
    
    def test_base_rendering_uses_asset(self):
        """Test that bases are rendered with asset when available"""
        from view.dota2_view.dota2_view import Dota2View
        from engine.config_loader import ConfigLoader
        from engine.model.game_model import GameModel
        
        config_loader = ConfigLoader()
        config = config_loader.load_game_config('config/game_config.yaml')
        game_model = GameModel(config)
        
        view = Dota2View(self.screen, game_model)
        
        assert view.base_assets is not None, "base_assets dict should be initialized"
        assert 'radiant' in view.base_assets, "Radiant base should be in base_assets"
        assert 'dire' in view.base_assets, "Dire base should be in base_assets"
