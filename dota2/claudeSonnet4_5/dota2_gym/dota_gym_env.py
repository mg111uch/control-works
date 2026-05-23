# =============================================================================
# TASK 9: Gymnasium Environment
# =============================================================================
import numpy as np
import gymnasium as gym
from gymnasium import spaces

class Dota2GymEnv(gym.Env):
    """
    Gymnasium environment for Dota2 1v1 Shadow Fiend
    Observation: 2000-dim vector
    Action: Hybrid (continuous position + discrete ability)
    """
    
    metadata = {'render_modes': ['human', 'rgb_array'], 'render_fps': 15}
    
    def __init__(self, render_mode=None):
        super().__init__()
        
        from engine.config_loader import ConfigLoader
        from engine.model.game_model import GameModel
        
        # Load config
        config_loader = ConfigLoader()
        self.config = config_loader.load_game_config('config/game_config.yaml')
        
        # Create game model
        self.game_model = GameModel(self.config)
        
        # Observation space: 2000-dim vector
        # Includes: hero stats, enemy stats, nearby units, vision grid, etc.
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf,
            shape=(2000,), dtype=np.float32
        )
        
        # Action space: Hybrid
        # Continuous: mouse position (x, y) normalized to [0, 1]
        # Discrete: action type (0=move, 1=attack, 2-5=abilities, 6-11=items)
        self.action_space = spaces.Dict({
            'mouse': spaces.Box(low=0, high=1, shape=(2,), dtype=np.float32),
            'action': spaces.Discrete(12)  # 0=move, 1=attack, 2=Q, 3=W, 4=E, 5=R, 6-11=items
        })
        
        self.render_mode = render_mode
        self.screen = None
        self.clock = None
    
    def reset(self, seed=None, options=None):
        """Reset environment"""
        super().reset(seed=seed)
        
        # Reset game
        self.game_model = GameModel(self.config)
        self.game_model.initialize_game()
        
        observation = self._get_observation()
        info = {}
        
        return observation, info
    
    def step(self, action):
        """Execute action and return next state"""
        # Parse action
        mouse_pos = action['mouse']  # [0, 1] range
        action_type = action['action']
        
        # Convert mouse to world coordinates
        map_width = self.config['game']['map_width']
        map_height = self.config['game']['map_height']
        world_x = mouse_pos[0] * map_width
        world_y = mouse_pos[1] * map_height
        
        # Execute action on player hero
        player_hero_id = self.game_model.player_heroes[0]
        
        if action_type == 0:  # Move
            self.game_model.movement_system.set_move_target(player_hero_id, world_x, world_y)
        elif action_type == 1:  # Attack (would need target selection)
            pass
        elif action_type >= 2 and action_type <= 5:  # Abilities
            if hasattr(self.game_model, 'ability_system'):
                ability_map = {2: 'near', 3: 'medium', 4: 'far', 5: 'r'}
                if action_type < 5:
                    self.game_model.ability_system.cast_shadowraze(player_hero_id, ability_map[action_type])
                else:
                    self.game_model.ability_system.cast_requiem(player_hero_id)
        elif action_type >= 6:  # Items
            if hasattr(self.game_model, 'item_system'):
                slot = action_type - 6
                self.game_model.item_system.use_item(player_hero_id, slot)
        
        # Step simulation
        self.game_model.tick()
        
        # Get next observation
        observation = self._get_observation()
        
        # Calculate reward
        reward = self._calculate_reward()
        
        # Check if episode is done
        terminated = self.game_model.game_ended
        truncated = False
        
        info = {
            'game_time': self.game_model.game_time,
            'tick': self.game_model.tick_count
        }
        
        return observation, reward, terminated, truncated, info
    
    def _get_observation(self) -> np.ndarray:
        """
        Construct 2000-dim observation vector
        Includes:
        - Player hero stats (position, HP, mana, souls, etc.)
        - Enemy hero stats
        - Nearby creeps/projectiles
        - Vision grid
        - Game state (time, gold, etc.)
        """
        obs = np.zeros(2000, dtype=np.float32)
        em = self.game_model.entity_manager
        
        idx = 0
        
        # Player hero (indices 0-99)
        if 0 in self.game_model.player_heroes:
            hero_id = self.game_model.player_heroes[0]
            pos = em.get_component(hero_id, 'position')
            stats = em.get_component(hero_id, 'stats')
            hero = em.get_component(hero_id, 'hero')
            combat = em.get_component(hero_id, 'combat')
            
            if pos:
                obs[idx:idx+2] = [pos.x / 7200, pos.y / 7200]  # Normalized position
                idx += 2
            
            if stats:
                obs[idx:idx+4] = [
                    stats.current_hp / stats.max_hp,
                    stats.current_mana / stats.max_mana,
                    stats.armor / 50.0,
                    stats.magic_resist / 100.0
                ]
                idx += 4
            
            if hero:
                obs[idx:idx+4] = [
                    hero.souls / 36.0,
                    hero.strength / 100.0,
                    hero.agility / 100.0,
                    hero.intelligence / 100.0
                ]
                idx += 4
            
            if combat:
                obs[idx:idx+3] = [
                    combat.damage_min / 200.0,
                    combat.attack_range / 1000.0,
                    combat.attack_cooldown / 2.0
                ]
                idx += 3
        
        # Enemy hero (indices 100-199)
        # ... similar encoding for enemy
        
        # Nearby entities (indices 200-999)
        # Vision grid (indices 1000-1999)
        
        return obs
    
    def _calculate_reward(self) -> float:
        """Calculate reward for current state"""
        reward = 0.0
        
        # Reward for HP difference
        if 0 in self.game_model.player_heroes and 1 in self.game_model.player_heroes:
            player_stats = self.game_model.entity_manager.get_component(
                self.game_model.player_heroes[0], 'stats'
            )
            enemy_stats = self.game_model.entity_manager.get_component(
                self.game_model.player_heroes[1], 'stats'
            )
            
            if player_stats and enemy_stats:
                hp_diff = (player_stats.current_hp / player_stats.max_hp - 
                          enemy_stats.current_hp / enemy_stats.max_hp)
                reward += hp_diff * 0.1
        
        # Reward for winning
        if self.game_model.game_ended:
            if self.game_model.winner == 0:
                reward += 100.0
            else:
                reward -= 100.0
        
        return reward
    
    def render(self):
        """Render the environment"""
        if self.render_mode == 'human':
            import pygame
            if self.screen is None:
                pygame.init()
                self.screen = pygame.display.set_mode((1280, 720))
                self.clock = pygame.time.Clock()
            
            # Render using PygameView
            from view.pygame_view import PygameView
            view = PygameView(self.screen, self.game_model)
            view.render()
            pygame.display.flip()
            self.clock.tick(self.metadata['render_fps'])
    
    def close(self):
        """Cleanup"""
        if self.screen is not None:
            import pygame
            pygame.quit()
            self.screen = None

# =============================================================================
# Example usage
# =============================================================================

if __name__ == '__main__':
    # Test Gymnasium environment
    env = Dota2GymEnv(render_mode='human')
    obs, info = env.reset()
    
    print(f"Observation shape: {obs.shape}")
    print(f"Action space: {env.action_space}")
    
    # Random agent
    for i in range(100):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        env.render()
        
        if terminated or truncated:
            break
    
    env.close()