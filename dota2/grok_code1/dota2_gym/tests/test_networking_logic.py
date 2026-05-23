import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'

import pytest
import numpy as np
from engine.model.networking import serialize_input_packet, deserialize_input_packet, serialize_snapshot, deserialize_snapshot, PacketType
from engine.model.game_model import GameModel


def test_packet_serialization():
    input_data = {
        "move_target": np.array([100.0, 200.0]),
        "attack_move": False,
        "cast_raze": None,
        "cast_requiem": False,
        "use_item": None,
        "stop": False
    }
    packet = serialize_input_packet(1, input_data)
    assert packet is not None

    deserialized = deserialize_input_packet(packet)
    assert deserialized is not None
    assert deserialized["tick"] == 1
    assert np.allclose(deserialized["move_target"], input_data["move_target"])


def test_snapshot_serialization():
    model = GameModel()
    snapshot = serialize_snapshot(model)
    assert snapshot is not None
    assert len(snapshot) > 5  # Has header

    deserialized = deserialize_snapshot(snapshot)
    assert deserialized is not None
    assert "tick" in deserialized
    assert "entities" in deserialized


def test_server_client_basic():
    # This is a placeholder for full integration test
    # In real test, would start server, connect clients, send inputs, check snapshots
    assert True  # Placeholder