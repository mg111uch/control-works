"""Tests for configuration loading"""
import pytest
from pathlib import Path
from engine.config_loader import ConfigLoader


class TestConfigLoader:
    """Test configuration loading system"""
    
    def setup_method(self):
        """Setup before each test"""
        self.config_loader = ConfigLoader()
    
    def test_load_game_config(self):
        """Test loading main game configuration"""
        config = self.config_loader.load_game_config('config/game_config.yaml')
        
        assert config is not None
        assert 'game' in config
        assert 'rendering' in config
        assert 'fog_of_war' in config
        
        # Check game settings
        assert config['game']['tick_rate'] == 15
        assert config['game']['map_width'] == 7200
        assert config['game']['map_height'] == 7200
        
        # Check rendering settings
        assert config['rendering']['screen_width'] == 1280
        assert config['rendering']['screen_height'] == 720
        
        # Check fog of war
        assert 'enabled' in config['fog_of_war']
        assert config['fog_of_war']['vision_radius'] == 1800
    
    def test_load_hero_config(self):
        """Test loading hero configuration"""
        config = self.config_loader.load_hero_config('shadow_fiend')
        
        assert config is not None
        assert config['name'] == 'Shadow Fiend'
        assert config['hero_id'] == 'shadow_fiend'
        
        # Check base stats
        assert 'base_stats' in config
        base = config['base_stats']
        assert base['strength'] == 20
        assert base['agility'] == 20
        assert base['intelligence'] == 20
        
        # Check movement
        assert base['movement_speed'] == 310
        assert base['turn_rate'] == 999
        
        # Check combat
        assert base['base_damage_min'] == 49
        assert base['base_damage_max'] == 59
        assert base['base_attack_range'] == 500
        
        # Check necromastery
        assert 'necromastery' in config
        necro = config['necromastery']
        assert necro['max_souls'] == 36
        assert necro['damage_per_soul'] == 2
        assert necro['attack_range_per_soul'] == 3.33
    
    def test_load_items_config(self):
        """Test loading items configuration"""
        config = self.config_loader.load_items_config()
        
        assert config is not None
        assert 'items' in config
        assert len(config['items']) > 0
        
        # Check first item
        first_item = config['items'][0]
        assert 'id' in first_item
        assert 'name' in first_item
        assert 'cost' in first_item
    
    def test_config_file_not_found(self):
        """Test handling of missing config file"""
        with pytest.raises(FileNotFoundError):
            self.config_loader.load_hero_config('nonexistent_hero')
    
    def test_config_structure(self):
        """Test that all required config files exist"""
        config_dir = Path(__file__).parent.parent / 'config'
        
        # Check main config
        assert (config_dir / 'game_config.yaml').exists()
        
        # Check heroes folder
        heroes_dir = config_dir / 'heroes'
        assert heroes_dir.exists()
        assert (heroes_dir / 'shadow_fiend.yaml').exists()
        
        # Check items folder
        items_dir = config_dir / 'items'
        assert items_dir.exists()
        assert (items_dir / 'items.yaml').exists()