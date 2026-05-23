# env/multiagent_env.py
"""
multiagent_env.py – PettingZoo Parallel Environment
Fully compatible with:
  • PettingZoo (AEC & Parallel APIs)
  • SB3, RLLib, CleanRL, MARLlib
  • Human + AI + Network + Self-play
  • Headless training at full speed
"""

from __future__ import annotations
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from pettingzoo import ParallelEnv
from pettingzoo.utils import parallel_to_aec, wrappers

from engine.model.game_model import GameModel
from engine.controller.ai_controller import RandomAIController
from engine.controller.human_controller import HumanController


class Dota2MultiAgentEnv(ParallelEnv):
    """
    PettingZoo Parallel Environment for 1v1 Shadow Fiend
    Agents: "player_0" and "player_1"
    """
    metadata = {
        "render_modes": ["human", "rgb_array"],
        "name": "dota2_1v1_v0",
        "is_parallelizable": True,
        "render_fps": 15,
    }

    def __init__(self, render_mode: Optional[str] = None, headless: bool = False):
        super().__init__()
        self.headless = headless or (render_mode is None)
        self.render_mode = render_mode

        # Create shared game model
        self.model = GameModel()
        self.model.is_headless = self.headless

        # Controllers (can be swapped at runtime)
        self.controllers = {
            "player_0": HumanController(self.model, player_id=0),
            "player_1": RandomAIController(self.model, player_id=1)
        }

        # Register controllers
        for agent, ctrl in self.controllers.items():
            pid = 0 if agent == "player_0" else 1
            self.model.register_controller(pid, ctrl)

        # PettingZoo required attributes
        self.possible_agents = ["player_0", "player_1"]
        self.agents = self.possible_agents[:]
        self.agent_name_mapping = {agent: i for i, agent in enumerate(self.agents)}

        # Action & observation spaces (identical for both agents)
        self.action_spaces = {
            agent: spaces.Dict({
                "mouse": spaces.Box(low=0.0, high=1.0, shape=(2,), dtype=np.float32),  # normalized screen
                "buttons": spaces.Discrete(14)  # 0-3: abilities, 4-9: items, 10-13: move/attack/stop/etc.
            }) for agent in self.agents
        }

        # Observation: ~3000-dim vector (positions, HP, cooldowns, visible entities)
        self.observation_spaces = {
            agent: spaces.Box(
                low=-1.0, high=5000.0, shape=(3072,), dtype=np.float32
            ) for agent in self.agents
        }

        # For rendering
        self.screen = None
        self.clock = None

    # ------------------------------------------------------------------ #
    # PettingZoo Parallel API
    # ------------------------------------------------------------------ #
    def reset(self, seed: Optional[int] = None, options: Optional[dict] = None):
        if seed is not None:
            self.model = GameModel(seed=seed)
        else:
            self.model.reset()

        # Re-register controllers
        for agent, ctrl in self.controllers.items():
            pid = 0 if agent == "player_0" else 1
            self.model.register_controller(pid, ctrl)

        observations = {agent: self._get_obs(agent) for agent in self.agents}
        infos = {agent: {} for agent in self.agents}
        return observations, infos

    def step(self, actions: Dict[str, Any]):
        # Apply actions via controllers
        for agent, action in actions.items():
            ctrl = self.controllers[agent]
            pid = self.agent_name_mapping[agent]

            # Translate action dict → controller input
            mouse_norm = action["mouse"]
            button = action["buttons"]

            # Convert mouse to world target (centered on hero)
            hero = next(e for e in self.model.entities.all() if getattr(e, "player_id", -1) == pid)
            pos = hero.get_component("position").value
            world_target = pos + (np.array(mouse_norm) - 0.5) * 4000

            ctrl.current_input = {
                "move_target": world_target,
                "attack_move": button == 11,
                "cast_raze": {0: "short", 1: "medium", 2: "long"}.get(button),
                "cast_requiem": button == 3,
                "use_item": button - 4 if 4 <= button < 10 else None,
                "stop": button == 10
            }

        # Advance one tick
        self.model.update(1.0 / 15.0)

        # Get new state
        observations = {agent: self._get_obs(agent) for agent in self.agents}
        rewards = {agent: self._get_reward(agent) for agent in self.agents}
        terminated = {agent: self.model.winner is not None for agent in self.agents}
        truncated = {agent: False for agent in self.agents}
        infos = {agent: {"winner": self.model.winner} for agent in self.agents}

        # Remove dead agents (optional)
        if self.model.winner is not None:
            self.agents = []

        return observations, rewards, terminated, truncated, infos

    def render(self):
        if self.render_mode == "human" and not self.headless:
            from engine.view.pygame_view import PygameView
            if not hasattr(self, "view"):
                import pygame
                pygame.init()
                self.screen = pygame.display.set_mode((1280, 720))
                self.clock = pygame.time.Clock()
                self.view = PygameView(self.screen, self.model)
            self.view.render()
            pygame.display.flip()
            self.clock.tick(15)

    def close(self):
        if hasattr(self, "screen"):
            import pygame
            pygame.quit()

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _get_obs(self, agent: str) -> np.ndarray:
        pid = self.agent_name_mapping[agent]
        hero = next((e for e in self.model.entities.all() if getattr(e, "player_id", -1) == pid), None)
        if not hero:
            return np.zeros(3072, dtype=np.float32)

        # Use VisionSystem to get visible entities
        visible = self.model.systems["vision"].get_visible_entities(pid)

        vec = np.zeros(3072, dtype=np.float32)
        idx = 0

        # Own state
        pos = hero.get_component("position").value
        vec[idx:idx+2] = pos / 16000.0
        idx += 2
        vec[idx] = hero.get_component("health").current / 2000.0
        idx += 1
        vec[idx] = hero.get_component("mana").current / 1000.0
        idx += 1
        vec[idx] = hero.get_component("souls").current / 40.0
        idx += 1
        vec[idx] = hero.level / 10.0
        idx += 1

        # Cooldowns
        for cd in ["raze_short", "raze_medium", "raze_long", "requiem"]:
            vec[idx] = hero.cooldowns.get(cd, 0.0) / 120.0
            idx += 1

        # Visible entities (up to 100)
        for ent in visible[:100]:
            epos = ent.get_component("position").value
            vec[idx:idx+2] = (epos - pos) / 4000.0
            idx += 2
            vec[idx] = ent.get_component("health").current / 2000.0 if ent.get_component("health") else 0.0
            idx += 1
            vec[idx] = 1.0 if getattr(ent, "team", -1) != hero.team else 0.0  # enemy?
            idx += 1

        return vec

    def _get_reward(self, agent: str) -> float:
        pid = self.agent_name_mapping[agent]
        hero = next((e for e in self.model.entities.all() if getattr(e, "player_id", -1) == pid), None)
        if not hero:
            return -10.0

        reward = 0.0
        reward += getattr(hero, "kills", 0) * 5.0
        reward += hero.get_component("souls").current * 0.1
        reward += hero.get_component("inventory").gold * 0.001
        reward += getattr(hero, "cs", 0) * 0.05

        if self.model.winner == pid:
            reward += 100.0
        elif self.model.winner is not None:
            reward -= 50.0

        return reward

    # ------------------------------------------------------------------ #
    # Convenience
    # ------------------------------------------------------------------ #
    def set_controller(self, agent: str, controller):
        """Swap AI/Human/Network at runtime"""
        self.controllers[agent] = controller
        pid = self.agent_name_mapping[agent]
        self.model.register_controller(pid, controller)


# PettingZoo wrappers for AEC compatibility
Dota2AECEnv = parallel_to_aec(Dota2MultiAgentEnv)


# Example usage:
if __name__ == "__main__":
    env = Dota2MultiAgentEnv(render_mode="human")
    observations, infos = env.reset()

    while env.agents:
        actions = {
            agent: env.action_spaces[agent].sample() for agent in env.agents
        }
        observations, rewards, terminations, truncations, infos = env.step(actions)
        env.render()