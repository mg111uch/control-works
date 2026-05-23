# network/server.py
import asyncio
import logging
from engine.model.game_model import GameModel
from engine.model.networking import PacketType, serialize_snapshot, deserialize_input_packet, parse_packet_header, create_join_packet

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LockstepServer:
    def __init__(self, host="0.0.0.0", port=8765, headless=False):
        self.host = host
        self.port = port
        self.headless = headless
        self.model = GameModel()
        self.clients = {}  # player_id -> writer
        self.pending_inputs = {}  # tick -> {player_id: input}
        self.current_tick = 0
        self.dt = 1.0 / 15.0

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        logger.info(f"New connection from {addr}")

        player_id = None
        try:
            # Wait for join packet
            data = await reader.read(1024)
            tick, ptype = parse_packet_header(data)
            if ptype == PacketType.JOIN:
                player_id = len(self.clients)
                self.clients[player_id] = writer
                self.model.controllers[player_id] = type("Controller", (), {"current_input": {}})()
                logger.info(f"Player {player_id} joined")

                # Send initial snapshot
                snapshot_data = serialize_snapshot(self.model)
                writer.write(snapshot_data)
                await writer.drain()

            while True:
                data = await reader.read(1024)
                if not data:
                    break

                tick, ptype = parse_packet_header(data)
                if ptype == PacketType.INPUT:
                    input_data = deserialize_input_packet(data)
                    if input_data:
                        if tick not in self.pending_inputs:
                            self.pending_inputs[tick] = {}
                        self.pending_inputs[tick][player_id] = input_data
                        logger.debug(f"Received input from player {player_id} for tick {tick}")

        except Exception as e:
            logger.error(f"Error handling client {addr}: {e}")
        finally:
            if player_id is not None and player_id in self.clients:
                del self.clients[player_id]
            writer.close()
            logger.info(f"Connection closed for {addr}")

    async def game_loop(self):
        while True:
            await asyncio.sleep(self.dt)

            # Apply inputs for current tick
            if self.current_tick in self.pending_inputs:
                inputs = self.pending_inputs.pop(self.current_tick)
                for pid, inp in inputs.items():
                    if pid in self.model.controllers:
                        self.model.controllers[pid].current_input = inp

            # Update game
            self.model.update(self.dt)

            # Broadcast snapshot
            snapshot_data = serialize_snapshot(self.model)
            for writer in self.clients.values():
                try:
                    writer.write(snapshot_data)
                    await writer.drain()
                except:
                    pass  # Client disconnected

            self.current_tick += 1

    async def run(self):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        logger.info(f"Lockstep server running on {self.host}:{self.port} (headless={self.headless})")

        # Start game loop
        asyncio.create_task(self.game_loop())

        async with server:
            await server.serve_forever()


async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    args = parser.parse_args()

    server = LockstepServer(headless=args.headless)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())