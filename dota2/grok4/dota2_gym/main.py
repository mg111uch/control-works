# dota2_gym/main.py
import argparse
import asyncio
import sys
import time
from enum import Enum

import pygame

from engine.model.game_model import GameModel
from engine.view.renderer_interface import RendererInterface
from engine.view.pygame_view import PygameView
from engine.controller.human_controller import HumanController
from engine.controller.ai_controller import RandomAIController
from env.dota_gym_env import DotaGymEnv
from network.client import NetworkClient
from network.observer import NetworkObserver


class GameMode(Enum):
    LOCAL = "local"          # Human vs Human (shared input or split controls)
    AI = "ai"                # Human vs Random AI
    HEADLESS = "headless"    # RL training / self-play (no renderer)
    CLIENT = "client"        # Online multiplayer client
    OBSERVER = "observer"    # Spectator mode


async def run_headless(episodes: int = 1000):
    env = DotaGymEnv(headless=True)
    print(f"Starting {episodes} headless episodes...")
    start = time.time()
    for ep in range(episodes):
        obs, _ = env.reset()
        done = False
        steps = 0
        while not done:
            action = {
                'mouse': env.action_space['mouse'].sample(),
                'buttons': env.action_space['buttons'].sample()
            }
            obs, reward, done, truncated, info = env.step(action)
            done = done or truncated
            steps += 1
        if (ep + 1) % 100 == 0:
            elapsed = time.time() - start
            print(f"Episode {ep+1}/{episodes} – {steps} steps – {(ep+1)/elapsed:.1f} eps/s")
    env.close()


def create_renderer(render_mode: str, model: GameModel) -> RendererInterface | None:
    """Factory – returns appropriate renderer or None for headless"""
    if render_mode is None or render_mode == "none":
        return None

    if render_mode in ("human", "rgb_array"):
        pygame.init()
        screen = pygame.display.set_mode((1280, 720))
        pygame.display.set_caption("dota2_gym – Shadow Fiend 1v1")
        return PygameView(screen, model)

    raise ValueError(f"Unknown render_mode: {render_mode}")


def main():
    parser = argparse.ArgumentParser(description="dota2_gym – 1v1 Shadow Fiend MOBA + RL")
    parser.add_argument("--mode", choices=[m.value for m in GameMode], default="local",
                        help="Game mode")
    parser.add_argument("--render", choices=["human", "rgb_array", "none"], default="human",
                        help="Rendering mode (none = headless)")
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--episodes", type=int, default=1000)
    args = parser.parse_args()

    # Headless RL training
    if args.mode == GameMode.HEADLESS.value:
        asyncio.run(run_headless(args.episodes))
        return

    # Create shared game model
    model = GameModel()

    # Network modes
    if args.mode == GameMode.CLIENT.value:
        client = NetworkClient(model, host=args.host, port=args.port)
        renderer = create_renderer(args.render, model)
        if renderer:
            renderer.init()
        asyncio.run(client.connect_and_run(renderer))
        return

    if args.mode == GameMode.OBSERVER.value:
        observer = NetworkObserver(host=args.host, port=args.port)
        renderer = create_renderer(args.render, model)
        if renderer:
            renderer.init()
        asyncio.run(observer.run(renderer))
        return

    # Local modes – create renderer
    renderer = create_renderer(args.render, model)
    if renderer:
        renderer.init()

    # Controllers
    if args.mode == GameMode.AI.value:
        controller_p0 = HumanController(model, player_id=0)
        controller_p1 = RandomAIController(model, player_id=1)
    else:  # local = human vs human (both use same input for now)
        controller_p0 = HumanController(model, player_id=0)
        controller_p1 = HumanController(model, player_id=0)  # Mirror controls

    model.register_controller(0, controller_p0)
    model.register_controller(1, controller_p1)

    # Main loop
    running = True
    dt = 1.0 / 15.0
    accumulator = 0.0
    current_time = time.time()

    while running:
        new_time = time.time()
        frame_time = new_time - current_time
        current_time = new_time
        accumulator += frame_time

        # Handle events (only if renderer exists)
        if renderer:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                controller_p0.handle_event(event)
                if args.mode == GameMode.LOCAL.value:
                    controller_p1.handle_event(event)

        # Fixed timestep update
        while accumulator >= dt:
            model.update(dt)
            accumulator -= dt

        # Render
        if renderer:
            renderer.render()
            renderer.flip()
            if hasattr(renderer, "clock"):
                renderer.clock.tick(15)

    # Cleanup
    if renderer:
        renderer.close()
    sys.exit()


if __name__ == "__main__":
    main()