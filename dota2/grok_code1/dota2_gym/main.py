import pygame
import sys
import numpy as np
import asyncio
import argparse
from engine.view.renderer_interface import RendererInterface
from engine.view.pygame_view import PygameView
from engine.model.game_model import GameModel
from engine.model.ecs.entity import Entity
from engine.controller.human_controller import HumanController, MoveTarget
from network.server import LockstepServer
from network.client import NetworkClient
from network.observer import NetworkObserver


class ClientMenuRenderer(RendererInterface):
    def __init__(self, screen, host, port):
        super().__init__()
        self.screen = screen
        self.host = host
        self.port = port
        self.fow_enabled = True
        self.font = pygame.font.SysFont(None, 36)
        self.connected = False
        self.model = None
        self.client = None

    def init(self):
        pass

    def render(self):
        self.screen.fill((0, 0, 0))
        title = self.font.render("Dota2 Gym - Shadow Fiend 1v1", True, (255, 255, 255))
        self.screen.blit(title, (400, 200))

        mode_text = self.font.render("Mode: Client", True, (255, 255, 255))
        self.screen.blit(mode_text, (400, 250))

        fow_text = self.font.render(f"FoW: {'On' if self.fow_enabled else 'Off'}", True, (255, 255, 255))
        self.screen.blit(fow_text, (400, 300))

        toggle_text = self.font.render("Press T to toggle FoW", True, (255, 255, 255))
        self.screen.blit(toggle_text, (400, 350))

        start_text = self.font.render(f"Press S to connect to {self.host}:{self.port}", True, (255, 255, 255))
        self.screen.blit(start_text, (350, 400))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_t:
                    self.fow_enabled = not self.fow_enabled
                if event.key == pygame.K_s:
                    # Connect
                    self.model = GameModel()
                    self.client = NetworkClient(self.model, host=self.host, port=self.port, headless=False)
                    self.connected = True
                    return False  # Exit menu
        return True

    def get_surface(self):
        return self.screen

    def flip(self):
        pygame.display.flip()

    def close(self):
        pygame.quit()


class MenuRenderer(RendererInterface):
    def __init__(self, screen):
        super().__init__()
        self.screen = screen
        self.fow_enabled = True
        self.font = pygame.font.SysFont(None, 36)

    def init(self):
        pass

    def render(self):
        self.screen.fill((0, 0, 0))
        title = self.font.render("Dota2 Gym - Shadow Fiend 1v1", True, (255, 255, 255))
        self.screen.blit(title, (400, 200))

        fow_text = self.font.render(f"FoW: {'On' if self.fow_enabled else 'Off'}", True, (255, 255, 255))
        self.screen.blit(fow_text, (400, 300))

        toggle_text = self.font.render("Press T to toggle FoW", True, (255, 255, 255))
        self.screen.blit(toggle_text, (400, 350))

        start_text = self.font.render("Press S to start Local Mode", True, (255, 255, 255))
        self.screen.blit(start_text, (400, 400))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_t:
                    self.fow_enabled = not self.fow_enabled
                if event.key == pygame.K_s:
                    return False  # Exit menu
        return True

    def get_surface(self):
        return self.screen

    def flip(self):
        pygame.display.flip()

    def close(self):
        pygame.quit()


def main():
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("dota2_gym – Main Menu")

    menu = MenuRenderer(screen)
    menu.init()

    running = True
    while running:
        menu.render()
        menu.flip()
        running = menu.handle_events()

    print(f"Starting game with FoW: {menu.fow_enabled}")

    # Start movement demo
    run_movement_demo(screen)

    menu.close()


def run_movement_demo(screen):
    pygame.display.set_caption("dota2_gym – Movement Demo")

    model = GameModel()
    # Create a demo entity
    entity = Entity(model)
    entity.player_id = 0
    entity.move_speed = 300.0
    entity.add_component("position", type("Position", (), {"value": np.array([8000.0, 7200.0])})())
    entity.add_component("velocity", type("Velocity", (), {"value": np.zeros(2)})())
    model.entities.add(entity)

    view = PygameView(screen, model)
    view.init()

    controller = HumanController(model, player_id=0, view=view)
    model.register_controller(0, controller)

    clock = pygame.time.Clock()
    dt = 1.0 / 15.0
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            controller.handle_event(event)

        model.update(dt)
        view.render()
        view.flip()
        clock.tick(15)

    view.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="dota2_gym")
    parser.add_argument("--mode", choices=["local", "server", "client", "observer"], default="local")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    if args.mode == "server":
        server = LockstepServer(headless=args.headless)
        asyncio.run(server.run())
    elif args.mode == "client":
        if args.headless:
            model = GameModel()
            client = NetworkClient(model, host=args.host, port=args.port, headless=args.headless)
            asyncio.run(client.connect_and_run())
        else:
            # Non-headless client with menu
            import pygame
            pygame.init()
            screen = pygame.display.set_mode((1280, 720))
            pygame.display.set_caption("dota2_gym – Client Menu")

            menu = ClientMenuRenderer(screen, args.host, args.port)
            menu.init()

            running = True
            while running:
                menu.render()
                menu.flip()
                running = menu.handle_events()

            if menu.connected:
                # Now run the game
                pygame.display.set_caption("dota2_gym – Client")
                view = PygameView(screen, menu.model)

                # Run client in thread
                import threading
                client_thread = threading.Thread(target=lambda: asyncio.run(menu.client.connect_and_run()))
                client_thread.start()

                # Pygame loop
                clock = pygame.time.Clock()
                running = True
                while running:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            running = False

                    view.render()
                    view.flip()
                    clock.tick(15)

                client_thread.join()
                view.close()
            else:
                pygame.quit()
    elif args.mode == "observer":
        observer = NetworkObserver(host=args.host, port=args.port, headless=args.headless)
        asyncio.run(observer.run())
    else:
        main()