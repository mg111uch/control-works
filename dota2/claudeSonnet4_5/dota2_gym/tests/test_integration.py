"""
test_integration.py - Full game integration tests
"""
import pytest


class TestGameIntegration:
    """Test full game integration"""
    
    def test_game_initialization(self):
        """Test game initializes with all systems"""
        from engine.config_loader import ConfigLoader
        from engine.model.game_model import GameModel
        
        config_loader = ConfigLoader()
        config = config_loader.load_game_config('config/game_config.yaml')
        
        game_model = GameModel(config)
        game_model.initialize_game()
        
        # Should have 2 heroes
        assert len(game_model.player_heroes) == 2
        assert 0 in game_model.player_heroes
        assert 1 in game_model.player_heroes
    
    def test_game_tick_progression(self):
        """Test game ticks advance properly"""
        from engine.config_loader import ConfigLoader
        from engine.model.game_model import GameModel
        
        config_loader = ConfigLoader()
        config = config_loader.load_game_config('config/game_config.yaml')
        
        game_model = GameModel(config)
        game_model.initialize_game()
        
        # Game starts in pregame - run through pregame first
        # 15 seconds pregame at 15 ticks/sec = ~225 ticks, use 230 to be safe
        for _ in range(230):
            game_model.tick()
        
        assert not game_model.in_pregame
        assert game_model.game_time >= 0.0  # Reset after pregame, may have a few ticks after
        
        initial_tick = game_model.tick_count
        initial_time = game_model.game_time
        
        # Run 15 ticks (1 second) after pregame
        for _ in range(15):
            game_model.tick()
        
        assert game_model.tick_count == initial_tick + 15
        assert game_model.game_time == pytest.approx(initial_time + 1.0, abs=0.01)
    
    def test_win_condition(self):
        """Test game ends when hero dies"""
        from engine.config_loader import ConfigLoader
        from engine.model.game_model import GameModel
        
        config_loader = ConfigLoader()
        config = config_loader.load_game_config('config/game_config.yaml')
        
        game_model = GameModel(config)
        game_model.initialize_game()
        
        # Skip pregame to test win condition
        game_model.in_pregame = False
        
        # Kill one hero
        hero_id = game_model.player_heroes[0]
        stats = game_model.entity_manager.get_component(hero_id, 'stats')
        stats.current_hp = 0
        
        # Tick to check win condition
        game_model.tick()
        
        assert game_model.game_ended
        assert game_model.winner == 1  # Dire wins


# if __name__ == '__main__':
#     pytest.main([__file__, '-v'])