# env/dota_gym_env.py
import gymnasium as gym
from gymnasium.spaces import Box, Discrete, Dict
import numpy as np
import pygame
from engine.model.game_model import GameModel
from engine.controller.ai_controller import RandomAIController


class DotaGymEnv(gym.Env):
    metadata = {"render_modes": ["human", "rgb_array"], "name": "dota2_gym_v0"}

    def __init__(self, headless=False):
        super().__init__()
        self.headless = headless
        self.model = GameModel()
        self.model.register_controller(1, RandomAIController(self.model, player_id=1))

        # Hybrid action space
        self.action_space = Dict({
            "mouse": Box(low=0.0, high=1.0, shape=(2,), dtype=np.float32),   # normalized screen pos
            "buttons": Discrete(14)  # 0-3: abilities, 4-9: items, 10: stop, 11: attack-move, 12-13: unused
        })

        # Observation: flattened vector of visible entities
        self.observation_space = Box(low=-1, high=5000, shape=(3000,), dtype=np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.model.reset()
        return self._get_obs(), {}

    def step(self, action):
        # Translate action → controller input
        mouse_norm = action["mouse"]
        button = action["buttons"]

        # Convert normalized mouse to world position (centered on hero)
        hero = next(e for e in self.model.entities.all() if getattr(e, "player_id", -1) == 0)
        hero_pos = hero.get_component("position").value
        world_x = hero_pos[0] + (mouse_norm[0] - 0.5) * 4000
        world_y = hero_pos[1] + (mouse_norm[1] - 0.5) * 4000

        # Simulate one full tick with human input
        controller = self.model.controllers[0]
        controller.current_input = {
            "move_target": np.array([world_x, world_y]),
            "right_click": True,
            "ability": button if button < 4 else None,
            "item": button - 4 if 4 <= button < 10 else None
        }

        self.model.update(1/15.0)

        obs = self._get_obs()
        reward = self._compute_reward()
        done = self.model.winner is not None
        info = {"winner": self.model.winner}

        return obs, reward, done, False, info

    def _get_obs(self):
        # Simple observation: hero state + visible entities count + distances
        hero = next(e for e in self.model.entities.all() if getattr(e, "player_id", -1) == 0)
        pos = hero.get_component("position").value
        visible = self.model.spatial_hash.query_radius(pos, 1800)
        visible_entities = self.model.systems["vision"].get_visible_entities(0)
        obs_features = self._entities_to_vector(visible_entities)

        vec = np.zeros(3000, dtype=np.float32)
        idx = 0
        vec[idx:idx+2] = pos / 16000.0
        idx += 2
        vec[idx] = hero.get_component("health").current / 2000.0
        idx += 1
        vec[idx] = hero.get_component("souls").current / 40.0
        idx += 1
        # Add more features as needed
        return vec

    def _compute_reward(self):
        # Dense reward
        hero = next(e for e in self.model.entities.all() if getattr(e, "player_id", -1) == 0)
        souls = hero.get_component("souls").current
        gold = hero.get_component("inventory").gold
        return souls * 0.1 + gold * 0.001

    def render(self):
        if not self.headless:
            from engine.view.pygame_view import PygameView
            if not hasattr(self, "view"):
                screen = pygame.display.set_mode((1280, 720))
                self.view = PygameView(screen, self.model)
            self.view.render()
            pygame.display.flip()

    def close(self):
        pass