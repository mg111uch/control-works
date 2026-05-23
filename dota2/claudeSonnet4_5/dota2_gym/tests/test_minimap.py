"""
Tests for minimap asset loading
"""
import pytest
import pygame
from pathlib import Path


class TestMinimapAssetLoading:
    """Test minimap asset loading functionality"""
    
    def setup_method(self):
        """Setup before each test"""
        pygame.init()
        self.screen = pygame.Surface((1280, 720))
    
    def teardown_method(self):
        """Cleanup after each test"""
        pygame.quit()
    
    def test_minimap_asset_exists(self):
        """Test that minimap asset file exists"""
        minimap_path = Path(__file__).parent.parent / 'assets' / 'minimap.png'
        assert minimap_path.exists(), f"Minimap asset not found at {minimap_path}"
    
    def test_minimap_asset_loads_successfully(self):
        """Test that minimap asset can be loaded as pygame surface"""
        from engine.config_loader import ConfigLoader
        
        config_loader = ConfigLoader()
        config = config_loader.load_game_config('config/game_config.yaml')
        
        minimap_path = Path(__file__).parent.parent / 'assets' / 'minimap.png'
        assert minimap_path.exists(), "Minimap asset file does not exist"
        
        minimap_surface = pygame.image.load(str(minimap_path))
        assert minimap_surface is not None, "Failed to load minimap surface"
        assert isinstance(minimap_surface, pygame.Surface), "Loaded object is not a pygame Surface"
    
    def test_minimap_config_has_asset_path(self):
        """Test that game config includes minimap asset path"""
        from engine.config_loader import ConfigLoader
        
        config_loader = ConfigLoader()
        config = config_loader.load_game_config('config/game_config.yaml')
        
        assert 'assets' in config, "Config missing 'assets' section"
        assert 'minimap' in config['assets'], "Config missing 'minimap' asset path"
        
        minimap_path = config['assets']['minimap']
        assert minimap_path is not None, "Minimap path is None"
        assert isinstance(minimap_path, str), "Minimap path is not a string"
    
    def test_minimap_renderer_uses_asset(self):
        """Test that UIMainRenderer renders minimap with asset when available"""
        from engine.config_loader import ConfigLoader
        from engine.model.game_model import GameModel
        from view.dota2_view.camera import Camera, Minimap
        from view.dota2_view.ui_main import UIMainRenderer
        
        config_loader = ConfigLoader()
        config = config_loader.load_game_config('config/game_config.yaml')
        
        game_model = GameModel(config)
        game_model.initialize_game()
        
        camera = Camera(self.screen, config, config['game']['map_width'], config['game']['map_height'])
        minimap = Minimap(self.screen, config['game']['map_width'], config['game']['map_height'])
        
        font_small = pygame.font.Font(None, 24)
        font_tiny = pygame.font.Font(None, 18)
        
        ui_renderer = UIMainRenderer(self.screen, game_model, font_small, font_tiny)
        
        minimap_path = Path(__file__).parent.parent / 'assets' / 'minimap.png'
        if minimap_path.exists():
            ui_renderer.load_minimap_asset(str(minimap_path))
            assert ui_renderer.minimap_asset is not None, "Minimap asset should be loaded"
            assert isinstance(ui_renderer.minimap_asset, pygame.Surface), "Minimap asset should be a pygame Surface"
    
    def test_minimap_asset_fallback_to_procedural(self):
        """Test that procedural rendering is used when minimap asset is not available"""
        from view.dota2_view.ui_main import UIMainRenderer
        from engine.model.game_model import GameModel
        from engine.config_loader import ConfigLoader
        from view.dota2_view.camera import Camera, Minimap
        
        config_loader = ConfigLoader()
        config = config_loader.load_game_config('config/game_config.yaml')
        
        game_model = GameModel(config)
        game_model.initialize_game()
        
        font_small = pygame.font.Font(None, 24)
        font_tiny = pygame.font.Font(None, 18)
        
        ui_renderer = UIMainRenderer(self.screen, game_model, font_small, font_tiny)
        
        ui_renderer.load_minimap_asset('/nonexistent/path/minimap.png')
        assert ui_renderer.minimap_asset is None, "Minimap asset should be None when file not found"
