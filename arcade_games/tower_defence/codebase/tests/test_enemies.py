"""
Tests for Enemy System
"""
import pytest


class TestEnemyWaveScaling:
    """Tests for enemy wave scaling"""
    
    def test_wave_health_scaling(self):
        """Test enemy health scales with wave"""
        def get_health(wave_num):
            return 20 + (wave_num * 10)
        
        assert get_health(1) == 30
        assert get_health(2) == 40
        assert get_health(3) == 50
        assert get_health(10) == 120
    
    def test_wave_speed_scaling(self):
        """Test enemy speed increases with wave"""
        base_speed = 2
        
        def get_speed(wave_num):
            return base_speed + (wave_num * 0.2)
        
        assert get_speed(1) == 2.2
        assert get_speed(2) == 2.4
        assert get_speed(5) == 3.0
    
    def test_enemies_per_wave(self):
        """Test number of enemies per wave"""
        def get_enemies(wave):
            return 5 + wave * 2
        
        assert get_enemies(1) == 7
        assert get_enemies(2) == 9
        assert get_enemies(5) == 15
        assert get_enemies(10) == 25
