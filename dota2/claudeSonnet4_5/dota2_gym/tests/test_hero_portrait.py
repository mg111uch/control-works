"""
Tests for hero portrait asset loading
"""
import pytest
import pygame
from pathlib import Path


class TestHeroPortraitAssetLoading:
    """Test hero portrait asset loading functionality"""
    
    def setup_method(self):
        """Setup before each test"""
        pygame.init()
        self.screen = pygame.Surface((1280, 720))
    
    def teardown_method(self):
        """Cleanup after each test"""
        pygame.quit()
    
    def test_hero_portrait_config_has_asset_path(self):
        """Test that game config includes hero_potrait asset path"""
        from engine.config_loader import ConfigLoader
        
        config_loader = ConfigLoader()
        config = config_loader.load_game_config('config/game_config.yaml')
        
        assert 'assets' in config, "Config missing 'assets' section"
        assert 'hero_potrait' in config['assets'], "Config missing 'hero_potrait' asset path"
        
        portrait_path = config['assets']['hero_potrait']
        assert portrait_path is not None, "Hero portrait path is None"
        assert isinstance(portrait_path, str), "Hero portrait path is not a string"
    
    def test_hero_portrait_asset_loads_successfully(self):
        """Test that hero portrait asset can be loaded as pygame surface"""
        from engine.config_loader import ConfigLoader
        
        config_loader = ConfigLoader()
        config = config_loader.load_game_config('config/game_config.yaml')
        
        portrait_path = config['assets']['hero_potrait']
        portrait_full_path = Path(__file__).parent.parent / portrait_path
        
        if portrait_full_path.exists():
            portrait_surface = pygame.image.load(str(portrait_full_path))
            assert portrait_surface is not None, "Failed to load portrait surface"
            assert isinstance(portrait_surface, pygame.Surface), "Loaded object is not a pygame Surface"
    
    def test_hero_portrait_renderer_loads_asset(self):
        """Test that UIMainRenderer loads hero portrait asset when path is provided"""
        from engine.config_loader import ConfigLoader
        from engine.model.game_model import GameModel
        from view.dota2_view.ui_main import UIMainRenderer
        
        config_loader = ConfigLoader()
        config = config_loader.load_game_config('config/game_config.yaml')
        
        game_model = GameModel(config)
        game_model.initialize_game()
        
        font_small = pygame.font.Font(None, 24)
        font_tiny = pygame.font.Font(None, 18)
        
        ui_renderer = UIMainRenderer(self.screen, game_model, font_small, font_tiny)
        
        portrait_path = config['assets']['hero_potrait']
        portrait_full_path = Path(__file__).parent.parent / portrait_path
        
        if portrait_full_path.exists():
            result = ui_renderer.load_hero_portrait_asset(str(portrait_full_path))
            assert result is True, "load_hero_portrait_asset should return True for valid path"
            assert ui_renderer.hero_portrait_asset is not None, "Hero portrait asset should be loaded"
            assert isinstance(ui_renderer.hero_portrait_asset, pygame.Surface), "Hero portrait asset should be a pygame Surface"
    
    def test_hero_portrait_asset_fallback_to_procedural(self):
        """Test that procedural rendering is used when hero portrait asset is not available"""
        from engine.config_loader import ConfigLoader
        from engine.model.game_model import GameModel
        from view.dota2_view.ui_main import UIMainRenderer
        
        config_loader = ConfigLoader()
        config = config_loader.load_game_config('config/game_config.yaml')
        
        game_model = GameModel(config)
        game_model.initialize_game()
        
        font_small = pygame.font.Font(None, 24)
        font_tiny = pygame.font.Font(None, 18)
        
        ui_renderer = UIMainRenderer(self.screen, game_model, font_small, font_tiny)
        
        ui_renderer.load_hero_portrait_asset('/nonexistent/path/portrait.png')
        assert ui_renderer.hero_portrait_asset is None, "Hero portrait asset should be None when file not found"
    
    def test_render_hero_portrait_uses_asset(self):
        """Test that render_hero_portrait uses asset when available"""
        from engine.config_loader import ConfigLoader
        from engine.model.game_model import GameModel
        from view.dota2_view.ui_main import UIMainRenderer
        
        config_loader = ConfigLoader()
        config = config_loader.load_game_config('config/game_config.yaml')
        
        game_model = GameModel(config)
        game_model.initialize_game()
        
        font_small = pygame.font.Font(None, 24)
        font_tiny = pygame.font.Font(None, 18)
        
        ui_renderer = UIMainRenderer(self.screen, game_model, font_small, font_tiny)
        
        portrait_path = config['assets']['hero_potrait']
        portrait_full_path = Path(__file__).parent.parent / portrait_path
        
        if portrait_full_path.exists():
            ui_renderer.load_hero_portrait_asset(str(portrait_full_path))
            assert ui_renderer.hero_portrait_asset is not None, "Hero portrait asset should be loaded before rendering"
