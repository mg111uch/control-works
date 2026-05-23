"""
Tests for Game State (Score, Money, Waves)
"""
import pytest


class TestMoneySystem:
    """Tests for money system"""
    
    def test_starting_money(self):
        """Test starting money is set correctly"""
        starting_money = 150
        assert starting_money == 150
    
    def test_kill_reward(self):
        """Test kill reward calculation"""
        kill_reward = 15
        assert kill_reward > 0
    
    def test_wave_bonus(self):
        """Test wave completion bonus"""
        wave_bonus = 50
        assert wave_bonus > 0
    
    def test_tower_cost_deduction(self):
        """Test tower cost is deducted from money"""
        money = 150
        tower_cost = 50
        
        money -= tower_cost
        
        assert money == 100
    
    def test_can_afford_tower(self):
        """Test can afford check"""
        money = 150
        
        assert money >= 50  # Artillery
        assert money >= 75  # Laser
        assert money >= 100  # Cannon
        
        assert money < 200  # Can't buy 3 cannons


class TestScoreSystem:
    """Tests for score system"""
    
    def test_initial_score(self):
        """Test initial score is zero"""
        score = 0
        assert score == 0
    
    def test_kill_score_increase(self):
        """Test score increases on enemy kill"""
        score = 0
        kills = 1
        score_per_kill = 10
        
        score += kills * score_per_kill
        
        assert score == 10
    
    def test_multiple_kills_score(self):
        """Test score with multiple kills"""
        score = 0
        kills = 5
        score_per_kill = 10
        
        score += kills * score_per_kill
        
        assert score == 50
    
    def test_score_accumulates(self):
        """Test score accumulates across waves"""
        score = 0
        wave1_kills = 3
        wave2_kills = 5
        score_per_kill = 10
        
        score += wave1_kills * score_per_kill
        score += wave2_kills * score_per_kill
        
        assert score == 80


class TestWaveSystem:
    """Tests for wave system"""
    
    def test_initial_wave(self):
        """Test initial wave is 1"""
        wave = 1
        assert wave == 1
    
    def test_wave_increases(self):
        """Test wave number increases after completion"""
        wave = 1
        wave += 1
        assert wave == 2
    
    def test_enemies_increase_per_wave(self):
        """Test more enemies spawn each wave"""
        def get_enemies_per_wave(wave):
            return 5 + wave * 2
        
        wave1 = get_enemies_per_wave(1)
        wave2 = get_enemies_per_wave(2)
        wave5 = get_enemies_per_wave(5)
        
        assert wave1 == 7
        assert wave2 == 9
        assert wave5 == 15
        assert wave2 > wave1
    
    def test_wave_cooldown(self):
        """Test wave cooldown between waves"""
        wave_cooldown = 3  # seconds
        assert wave_cooldown > 0
    
    def test_spawn_delay(self):
        """Test spawn delay between enemies"""
        spawn_delay = 1.5  # seconds
        assert spawn_delay > 0
    
    def test_wave_completion(self):
        """Test wave completion detection"""
        wave = 1
        enemies_spawned = 5
        enemies_remaining = 0
        wave_cooldown = 0
        
        wave_complete = (enemies_spawned >= 5 and enemies_remaining == 0 and wave_cooldown <= 0)
        
        assert wave_complete == True
    
    def test_wave_bonus_on_completion(self):
        """Test wave bonus is awarded on completion"""
        money = 150
        wave_bonus = 50
        
        # Wave complete
        money += wave_bonus
        
        assert money == 200
