# network/observer.py
"""
Observer client – watches online games without input
Connects as spectator, receives full snapshots, renders.
Perfect for tournaments, replays, or AI visualization.
"""

import asyncio
import json
import pygame
import websockets
from engine.view.pygame_view import PygameView


class NetworkObserver:
    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port

    async def run(self, screen, clock):
        uri = f"ws://{self.host}:{self.port}"
        print(f"[OBSERVER] Connecting to {uri}...")

        try:
            async with websockets.connect(uri) as websocket:
                print("[OBSERVER] Connected! Requesting observer mode...")
                await websocket.send(json.dumps({"type": "observe"}))

                renderer = None
                model = None

                running = True
                while running:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            running = False

                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=0.016)
                        data = json.loads(message)

                        if "snapshot" in data:
                            snapshot = data["snapshot"]
                            if model is None:
                                from engine.model.game_model import GameModel
                                model = GameModel()
                                renderer = PygameView(screen, model)

                            # Apply snapshot (same as client)
                            model.current_tick = snapshot["tick"]
                            model.game_time = snapshot["time"]
                            model.winner = snapshot.get("winner")

                            # Simplified entity sync
                            # In full version: use entity reconstruction system

                            if model.winner is not None:
                                print(f"[OBSERVER] Game Over! Winner: Player {model.winner}")

                        renderer.render() if renderer else None
                        pygame.display.flip()
                        clock.tick(15)

                    except asyncio.TimeoutError:
                        pass
                    except websockets.ConnectionClosed:
                        print("[OBSERVER] Server disconnected")
                        break

        except Exception as e:
            print(f"[OBSERVER] Failed: {e}")

        pygame.quit()


# Run observer
if __name__ == "__main__":
    import pygame
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    clock = pygame.time.Clock()

    observer = NetworkObserver(host="127.0.0.1", port=8765)
    asyncio.run(observer.run(screen, clock))