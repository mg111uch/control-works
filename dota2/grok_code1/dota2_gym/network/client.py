# network/client.py
"""
Client for online 1v1 / training
Connects to lockstep server, sends input every tick,
receives authoritative snapshots.
"""

import asyncio
import logging
import numpy as np
from engine.model.game_model import GameModel
from engine.model.networking import PacketType, serialize_input_packet, deserialize_input_packet, parse_packet_header, create_join_packet, serialize_snapshot, deserialize_snapshot
from engine.controller.human_controller import HumanController

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NetworkClient:
    def __init__(self, model: GameModel, host: str = "127.0.0.1", port: int = 8765, headless=False):
        self.model = model
        self.host = host
        self.port = port
        self.headless = headless
        self.reader = None
        self.writer = None
        self.player_id = None
        self.tick = 0
        self.local_controller = HumanController(self.model, player_id=0)

    async def connect_and_run(self):
        logger.info(f"[CLIENT] Connecting to {self.host}:{self.port}")
        try:
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)

            # Send join packet
            join_packet = create_join_packet("Player")
            self.writer.write(join_packet)
            await self.writer.drain()

            # Wait for initial snapshot
            data = await self.reader.read(4096)
            tick, ptype = parse_packet_header(data)
            if ptype == PacketType.SNAPSHOT:
                self._apply_snapshot(data)

            # Main loop
            while True:
                # Send input
                input_data = self.local_controller.current_input
                packet = serialize_input_packet(self.tick, input_data)
                self.writer.write(packet)
                await self.writer.drain()

                # Receive snapshot
                data = await self.reader.read(4096)
                tick, ptype = parse_packet_header(data)
                if ptype == PacketType.SNAPSHOT:
                    self._apply_snapshot(data)

                await asyncio.sleep(1.0 / 15.0)
                self.tick += 1

        except Exception as e:
            logger.error(f"[CLIENT] Error: {e}")
        finally:
            if self.writer:
                self.writer.close()
                await self.writer.wait_closed()

    def _apply_snapshot(self, data):
        snapshot = deserialize_snapshot(data)
        self.model.current_tick = snapshot['tick']
        self.model.game_time = snapshot['time']
        self.model.winner = snapshot['winner']

        # Sync entities
        self.model.entities.clear()
        for ent_data in snapshot['entities']:
            from engine.model.ecs.entity import Entity, Component
            ent = Entity(self.model, ent_data['id'])
            for comp_name, comp_data in ent_data.get('components', {}).items():
                if comp_name == 'position':
                    ent.add_component('position', Component(value=np.array(comp_data['value'])))
                elif comp_name == 'velocity':
                    ent.add_component('velocity', Component(value=np.array(comp_data['value'])))
                # Add other components as needed
            self.model.entities.add(ent)


async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()

    model = GameModel()
    client = NetworkClient(model, host=args.host, port=args.port, headless=args.headless)
    await client.connect_and_run()


if __name__ == "__main__":
    asyncio.run(main())