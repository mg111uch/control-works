import json
import yaml
import os
from typing import Dict, Any

class ConfigLoader:
    def __init__(self):
        self.constants = self._load_constants()
        self.hero_data = self._load_hero_data()
        self.items_data = self._load_items_data()

    def _load_constants(self) -> Dict[str, Any]:
        with open('config/constants.json', 'r') as f:
            return json.load(f)

    def _load_hero_data(self) -> Dict[str, Any]:
        with open('config/heroes/shadow_fiend.yaml', 'r') as f:
            return yaml.safe_load(f)

    def _load_items_data(self) -> Dict[str, Dict[str, Any]]:
        items = {}
        items_dir = 'config/items'
        for filename in os.listdir(items_dir):
            if filename.endswith('.yaml'):
                with open(os.path.join(items_dir, filename), 'r') as f:
                    data = yaml.safe_load(f)
                    items[data['internal_name']] = data
        return items

    def load_hero(self, hero_name: str) -> Dict[str, Any]:
        if hero_name == "shadow_fiend":
            return self.hero_data
        raise ValueError(f"Hero {hero_name} not found")
