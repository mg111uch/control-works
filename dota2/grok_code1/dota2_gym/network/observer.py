# network/observer.py
"""
Observer client – watches online games without input
Connects as spectator, receives full snapshots.
"""

import asyncio
import logging
from engine.model.game_model import GameModel
from engine.model.networking import PacketType, parse_packet_header, create_observe_packet

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NetworkObserver:
    def __init__(self, host: str = "127.0.0.1", port: int = 8765, headless=False):
        self.host = host
        self.port = port
        self.headless = headless
        self.reader = None
        self.writer = None

    async def run(self):
        logger.info(f"[OBSERVER] Connecting to {self.host}:{self.port}")
        try:
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)

            # Send observe packet
            observe_packet = create_observe_packet()
            self.writer.write(observe_packet)
            await self.writer.drain()

            while True:
                data = await self.reader.read(4096)
                tick, ptype = parse_packet_header(data)
                if ptype == PacketType.SNAPSHOT:
                    # Apply snapshot (simplified)
                    logger.info(f"[OBSERVER] Received snapshot for tick {tick}")

        except Exception as e:
            logger.error(f"[OBSERVER] Error: {e}")
        finally:
            if self.writer:
                self.writer.close()
                await self.writer.wait_closed()


async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()

    observer = NetworkObserver(host=args.host, port=args.port, headless=args.headless)
    await observer.run()


if __name__ == "__main__":
    asyncio.run(main())