"""Configuration loading system for YAML/JSON files"""
import yaml
import json
from pathlib import Path
from typing import Dict, Any


class ConfigLoader:
    """Load and parse configuration files (YAML/JSON)"""
    
    def __init__(self, config_dir: str = None):
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path(__file__).parent.parent / 'config'
    
    def load_game_config(self, path: str) -> Dict[str, Any]:
        """Load main game configuration"""
        full_path = Path(path) if Path(path).is_absolute() else self.config_dir.parent / path
        return self._load_yaml(full_path)
    
    def load_hero_config(self, hero_name: str) -> Dict[str, Any]:
        """Load hero configuration by name"""
        path = self.config_dir / 'heroes' / f'{hero_name}.yaml'
        return self._load_yaml(path)
    
    def load_items_config(self) -> Dict[str, Any]:
        """Load items configuration"""
        path = self.config_dir / 'items' / 'items.yaml'
        return self._load_yaml(path)
    
    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load YAML file"""
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _load_json(self, path: Path) -> Dict[str, Any]:
        """Load JSON file"""
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)