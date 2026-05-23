# network/client.py
"""
WebSocket client for online 1v1 / training
Connects to lockstep server, sends input every tick,
receives authoritative snapshots.
Fully compatible with HumanController + RL agents.
"""

import asyncio
import json
import websockets
import numpy as np
from typing import Optional
import pygame

from engine.model.game_model import GameModel
from engine.view.pygame_view import PygameView
from engine.controller.human_controller import HumanController


class NetworkClient:
    def __init__(self, model: GameModel, host: str = "127.0.0.1", port: int = 8765):
        self.model = model
        self.host = host
        self.port = port
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.player_id: Optional[int] = None
        self.tick = 0

        # Local human controller (sends input to server)
        self.local_controller = HumanController(self.model, player_id=0)

    async def connect_and_run(self, screen, clock):
        uri = f"ws://{self.host}:{self.port}"
        print(f"[CLIENT] Connecting to {uri}...")

        try:
            async with websockets.connect(uri) as websocket:
                self.websocket = websocket
                print(f"[CLIENT] Connected! Waiting for player assignment...")

                # Send join request
                await websocket.send(json.dumps({"type": "join", "name": "Player"}))

                # Main loop
                running = True
                renderer = PygameView(screen, self.model)

                while running:
                    # 1. Handle pygame events → local input
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            running = False
                        self.local_controller.handle_event(event)

                    # 2. Send input packet every tick
                    if self.player_id is not None:
                        packet = self._build_input_packet()
                        try:
                            await websocket.send(json.dumps(packet))
                        except:
                            print("[CLIENT] Send failed")
                            break

                    # 3. Receive snapshot (non-blocking)
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=0.001)
                        snapshot = json.loads(message)
                        self._apply_snapshot(snapshot)
                    except asyncio.TimeoutError:
                        pass  # No new snapshot this frame
                    except:
                        print("[CLIENT] Connection lost")
                        break

                    # 4. Render
                    renderer.render()
                    pygame.display.flip()
                    clock.tick(15)
                    self.tick += 1

        except Exception as e:
            print(f"[CLIENT] Connection failed: {e}")

        pygame.quit()

    def _build_input_packet(self) -> dict:
        """Convert local controller state → server packet"""
        inp = self.local_controller.current_input

        move = None
        if inp["move_target"] is not None:
            move = inp["move_target"].tolist()

        return {
            "tick": self.tick,
            "player_id": self.player_id,
            "move": move,
            "attack_move": inp["attack_move"],
            "raze": inp["cast_raze"],
            "requiem": inp["cast_requiem"],
            "item": inp["use_item"],
            "stop": inp["stop"]
        }

    def _apply_snapshot(self, snapshot: dict):
        """Apply authoritative state from server"""
        if "player_id" in snapshot:
            self.player_id = snapshot["player_id"]
            print(f"[CLIENT] Assigned as Player {self.player_id}")

        if "state" in snapshot:
            state = snapshot["state"]
            self.model.current_tick = state["tick"]
            self.model.game_time = state["time"]
            self.model.winner = state.get("winner")

            # Apply entities
            self.model.entities.clear()
            for ent_data in state["entities"]:
                # Simplified – real version uses entity factory
                pass

            # Apply fog of war
            if "fog" in state:
                for pid in [0, 1]:
                    if str(pid) in state["fog"]:
                        self.model.fog_of_war[pid] = np.array(state["fog"][str(pid)], dtype=bool)


# Run client
if __name__ == "__main__":
    import pygame
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    clock = pygame.time.Clock()

    model = GameModel()
    client = NetworkClient(model, host="127.0.0.1", port=8765)
    asyncio.run(client.connect_and_run(screen, clock))