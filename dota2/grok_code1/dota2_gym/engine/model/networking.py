# engine/model/networking.py
"""
Networking utilities for lockstep deterministic simulation.
Provides:
  • Input packet serialization (client → server)
  • State snapshot serialization (server → client / observer)
  • Delta compression helpers (optional future use)
  • Tick synchronization
"""

import json
import struct
from typing import Dict, Any, List
import numpy as np


class PacketType:
    INPUT = 0          # Client → Server
    SNAPSHOT = 1       # Server → Client/Observer
    ACK = 2            # Acknowledgement
    PING = 3
    JOIN = 4
    OBSERVE = 5


def serialize_input_packet(tick: int, input_data: Dict[str, Any]) -> bytes:
    """
    Serialize client input into compact binary + JSON hybrid.
    Format:
      [4 bytes: tick] [1 byte: type=0] [JSON payload]
    """
    payload = {
        "tick": tick,
        "move": input_data.get("move_target"),
        "attack_move": bool(input_data.get("attack_move", False)),
        "raze": input_data.get("cast_raze"),
        "requiem": bool(input_data.get("cast_requiem", False)),
        "item": input_data.get("use_item"),
        "stop": bool(input_data.get("stop", False))
    }
    if payload["move"] is not None:
        payload["move"] = payload["move"].tolist()
    json_str = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    return struct.pack("<IB", tick, PacketType.INPUT) + json_str + b'\x00'


def deserialize_input_packet(data: bytes) -> Dict[str, Any]:
    """Parse raw bytes from client"""
    if len(data) < 5:
        return None
    tick = struct.unpack("<I", data[:4])[0]
    packet_type = data[4]
    if packet_type != PacketType.INPUT:
        return None

    try:
        json_str = data[5:].split(b'\x00', 1)[0]
        payload = json.loads(json_str.decode('utf-8'))
        move = payload.get("move")
        if move:
            payload["move_target"] = np.array(move, dtype=np.float32)
        else:
            payload["move_target"] = None
        payload["attack_move"] = payload.get("attack_move", False)
        payload["cast_requiem"] = payload.get("cast_requiem", False)
        payload["stop"] = payload.get("stop", False)
        return payload
    except:
        return None


def serialize_snapshot(model) -> bytes:
    """
    Serialize full game state snapshot.
    Used every tick for lockstep + observers.
    """
    snapshot = model.get_state_snapshot()

    # Reduce precision for bandwidth
    for ent in snapshot["entities"]:
        if "position" in ent:
            pos = np.array(ent["position"], dtype=np.float32)
            ent["position"] = [round(pos[0], 1), round(pos[1], 1)]

    payload = {
        "tick": snapshot["tick"],
        "time": round(snapshot["time"], 2),
        "winner": snapshot["winner"],
        "entities": snapshot["entities"]
    }

    json_str = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    return struct.pack("<IB", snapshot["tick"], PacketType.SNAPSHOT) + json_str + b'\x00'


def compress_fog_of_war(fog_grid: np.ndarray) -> bytes:
    """RLE compress fog of war grid (224x200 bool → tiny string)"""
    flat = fog_grid.flatten().astype(np.uint8)
    compressed = []
    count = 1
    prev = flat[0]
    for val in flat[1:]:
        if val == prev and count < 255:
            count += 1
        else:
            compressed.extend([prev, count])
            count = 1
            prev = val
    compressed.extend([prev, count])
    return bytes(compressed)


def decompress_fog_of_war(data: bytes, width=224, height=200) -> np.ndarray:
    """Decompress RLE back to bool grid"""
    grid = np.zeros(width * height, dtype=bool)
    i = 0
    pos = 0
    while i < len(data) and pos < len(grid):
        val = data[i]
        count = data[i + 1] if i + 1 < len(data) else 1
        grid[pos:pos + count] = bool(val)
        pos += count
        i += 2
    return grid.reshape((height, width))


def create_join_packet(player_name: str = "Player") -> bytes:
    payload = {"type": "join", "name": player_name}
    json_str = json.dumps(payload).encode('utf-8')
    return struct.pack("<IB", 0, PacketType.JOIN) + json_str + b'\x00'


def create_observe_packet() -> bytes:
    return struct.pack("<IB", 0, PacketType.OBSERVE) + b'{"type":"observe"}\x00'


def create_ping_packet(client_tick: int) -> bytes:
    return struct.pack("<IBI", client_tick, PacketType.PING, client_tick)


def parse_packet_header(data: bytes) -> tuple:
    """Extract tick and type from first 5 bytes"""
    if len(data) < 5:
        return None, None
    return struct.unpack("<IB", data[:5])


def deserialize_snapshot(data):
    """Deserialize snapshot from bytes"""
    json_str = data[5:].split(b'\x00', 1)[0]
    snapshot = json.loads(json_str.decode('utf-8'))
    return snapshot


# Optional: Delta snapshot (for future bandwidth optimization)
def create_delta_snapshot(prev_snapshot: Dict, new_snapshot: Dict) -> Dict:
    """Compare two snapshots and send only changed entities"""
    new_ents = {e["id"]: e for e in new_snapshot["entities"]}
    prev_ents = {e["id"]: e for e in prev_snapshot["entities"]}

    changed = []
    for eid, ent in new_ents.items():
        if eid not in prev_ents or prev_ents[eid] != ent:
            changed.append(ent)

    removed = [eid for eid in prev_ents if eid not in new_ents]

    return {
        "tick": new_snapshot["tick"],
        "changed": changed,
        "removed": removed
    }