# network/server.py
import asyncio
import json
from engine.model.game_model import GameModel

async def handle_client(reader, writer):
    model = GameModel()
    player_id = len(model.controllers)
    model.controllers[player_id] = None  # placeholder

    while True:
        try:
            data = await reader.read(4096)
            if not data:
                break
            msg = json.loads(data.decode())
            # Store input
            if player_id in (0, 1):
                model.controllers[player_id].current_input = msg.get("input", {})

            model.update(1/15.0)
            snapshot = model.get_state_snapshot()
            writer.write(json.dumps(snapshot).encode() + b"\n")
            await writer.drain()
        except:
            break

    writer.close()

async def main():
    server = await asyncio.start_server(handle_client, "0.0.0.0", 8765)
    print("Lockstep server running on :8765")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())