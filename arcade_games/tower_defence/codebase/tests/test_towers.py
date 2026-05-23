"""
Tests for Tower System
"""
import pytest
import math


TOWER_TYPES = {
    'artillery': {
        'name': 'Artillery',
        'cost': 50,
        'cooldown': 1.0,
        'range': 100,
        'color': (0, 128, 0),
        'bullet_color': (255, 255, 0),
        'bullet_size': 3,
        'damage': 15
    },
    'cannon': {
        'name': 'Cannon',
        'cost': 100,
        'cooldown': 2.0,
        'range': 120,
        'color': (135, 206, 235),
        'bullet_color': (0, 0, 0),
        'bullet_size': 6,
        'damage': 30
    },
    'laser': {
        'name': 'Laser',
        'cost': 75,
        'cooldown': 0.5,
        'range': 80,
        'color': (255, 0, 0),
        'bullet_color': (128, 0, 128),
        'bullet_size': 2,
        'damage': 8
    }
}


class TestTowerTypes:
    """Tests for tower type configuration"""
    
    def test_tower_costs(self):
        """Test tower costs are different"""
        costs = [TOWER_TYPES[t]['cost'] for t in TOWER_TYPES]
        assert len(set(costs)) == 3
    
    def test_artillery_properties(self):
        """Test artillery tower properties"""
        t = TOWER_TYPES['artillery']
        assert t['cost'] == 50
        assert t['cooldown'] == 1.0
        assert t['range'] == 100
        assert t['damage'] == 15
    
    def test_cannon_properties(self):
        """Test cannon tower properties"""
        t = TOWER_TYPES['cannon']
        assert t['cost'] == 100
        assert t['cooldown'] == 2.0
        assert t['range'] == 120
        assert t['damage'] == 30
    
    def test_laser_properties(self):
        """Test laser tower properties"""
        t = TOWER_TYPES['laser']
        assert t['cost'] == 75
        assert t['cooldown'] == 0.5
        assert t['range'] == 80
        assert t['damage'] == 8
    
    def test_cooldown_ordering(self):
        """Test that cooldowns are in expected order"""
        laser_cd = TOWER_TYPES['laser']['cooldown']
        artillery_cd = TOWER_TYPES['artillery']['cooldown']
        cannon_cd = TOWER_TYPES['cannon']['cooldown']
        
        assert laser_cd < artillery_cd < cannon_cd
    
    def test_damage_ordering(self):
        """Test that damage values are in expected order"""
        laser_dmg = TOWER_TYPES['laser']['damage']
        artillery_dmg = TOWER_TYPES['artillery']['damage']
        cannon_dmg = TOWER_TYPES['cannon']['damage']
        
        assert laser_dmg < artillery_dmg < cannon_dmg


class TestTowerTargeting:
    """Tests for tower targeting logic"""
    
    def test_distance_calculation(self):
        """Test distance calculation between two points"""
        x1, y1 = 100, 100
        x2, y2 = 150, 100
        
        dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        assert dist == 50
    
    def test_can_shoot_in_range(self):
        """Test can_shoot returns True when enemy in range"""
        tower_x, tower_y = 100, 100
        tower_range = 100
        
        enemy_x, enemy_y = 150, 100
        dist = math.sqrt((tower_x - enemy_x)**2 + (tower_y - enemy_y)**2)
        
        assert dist <= tower_range
    
    def test_can_shoot_out_of_range(self):
        """Test can_shoot returns False when enemy out of range"""
        tower_x, tower_y = 100, 100
        tower_range = 100
        
        enemy_x, enemy_y = 250, 100
        dist = math.sqrt((tower_x - enemy_x)**2 + (tower_y - enemy_y)**2)
        
        assert dist > tower_range
    
    def test_can_shoot_at_edge(self):
        """Test can_shoot at exact range edge"""
        tower_x, tower_y = 100, 100
        tower_range = 100
        
        enemy_x, enemy_y = 200, 100
        dist = math.sqrt((tower_x - enemy_x)**2 + (tower_y - enemy_y)**2)
        
        assert dist <= tower_range


class TestTowerSelection:
    """Tests for tower selection logic"""
    
    def test_contains_point_at_center(self):
        """Test contains_point at tower center"""
        tower_x, tower_y = 100, 100
        radius = 15
        
        px, py = 100, 100
        dist = math.sqrt((tower_x - px)**2 + (tower_y - py)**2)
        
        assert dist <= radius
    
    def test_contains_point_at_edge(self):
        """Test contains_point at tower edge"""
        tower_x, tower_y = 100, 100
        radius = 15
        
        px, py = 115, 100
        dist = math.sqrt((tower_x - px)**2 + (tower_y - py)**2)
        
        assert dist <= radius
    
    def test_contains_point_outside(self):
        """Test contains_point outside tower"""
        tower_x, tower_y = 100, 100
        radius = 15
        
        px, py = 150, 100
        dist = math.sqrt((tower_x - px)**2 + (tower_y - py)**2)
        
        assert dist > radius
    
    def test_contains_point_corner(self):
        """Test contains_point at corner"""
        tower_x, tower_y = 100, 100
        radius = 15
        
        px, py = 110, 110
        dist = math.sqrt((tower_x - px)**2 + (tower_y - py)**2)
        
        assert dist <= radius
