# engine/controller/network_controller.py
import json
import asyncio
import numpy as np
from typing import Dict, Any, Optional


class NetworkController:
    """
    Controller used on the **server side** for remote players.
    Receives input packets from clients (via WebSocket or TCP) and applies them
    exactly like a local HumanController would.
    Fully compatible with lockstep networking.
    """
    def __init__(self, model, player_id: int):
        self.model = model
        self.player_id = player_id
        self.hero = None

        # Latest input received from the client
        self.current_input: Dict[str, Any] = {
            "move_target": None,      # np.array([x, y])
            "attack_move": False,
            "cast_raze": None,        # "short" / "medium" / "long"
            "cast_requiem": False,
            "use_item": None,         # 0–5
            "stop": False,
            "mouse_screen": None      # Optional: raw screen pos for camera sync
        }

        self.last_update_tick = -1  # For input prediction / replay protection

    def find_hero(self):
        if self.hero is None:
            for ent in self.model.entities.all():
                if getattr(ent, "player_id", -1) == self.player_id and hasattr(ent, "cast_raze"):
                    self.hero = ent
                    break

    def apply_input_packet(self, packet: Dict[str, Any], server_tick: int):
        """
        Called by the network server when a new packet arrives.
        Packet format (JSON):
        {
            "tick": 1234,
            "move": [8000.0, 7200.0],        # optional world target
            "attack_move": true/false,
            "raze": "short"/"medium"/"long"/null,
            "requiem": true/false,
            "item": 2 or null,
            "stop": true/false
        }
        """
        if packet.get("tick", -1) <= self.last_update_tick:
            return  # Ignore old/out-of-order packets

        self.last_update_tick = packet.get("tick", server_tick)

        move = packet.get("move")
        if move and len(move) == 2:
            self.current_input["move_target"] = np.array(move, dtype=np.float32)

        self.current_input["attack_move"] = bool(packet.get("attack_move", False))
        raze = packet.get("raze")
        if raze in ("short", "medium", "long"):
            self.current_input["cast_raze"] = raze
        else:
            self.current_input["cast_raze"] = None

        self.current_input["cast_requiem"] = bool(packet.get("requiem", False))
        item = packet.get("item")
        self.current_input["use_item"] = item if isinstance(item, int) and 0 <= item <= 5 else None
        self.current_input["stop"] = bool(packet.get("stop", False))

    def update(self, dt: float):
        """
        Called every tick by GameModel.
        Applies the latest received input to the hero.
        """
        self.find_hero()
        if not self.hero:
            return

        # === Movement ===
        if self.current_input["move_target"] is not None:
            direction = self.current_input["move_target"] - self.hero.get_component("position").value
            dist = np.linalg.norm(direction)
            if dist > 10:
                direction = direction / dist
                speed = self.hero.get_move_speed()
                self.hero.get_component("velocity").value = direction * speed
            else:
                self.hero.get_component("velocity").value = np.zeros(2)

        # === Abilities ===
        if self.current_input["cast_raze"]:
            self.hero.cast_raze(self.current_input["cast_raze"])

        if self.current_input["cast_requiem"]:
            self.hero.cast_requiem()

        # === Items ===
        if self.current_input["use_item"] is not None:
            inv = self.hero.get_component("inventory")
            if inv and 0 <= self.current_input["use_item"] < 6:
                item = inv.slots[self.current_input["use_item"]]
                if item:
                    # Will be handled by ItemSystem later
                    pass

        # === Stop ===
        if self.current_input["stop"]:
            self.hero.get_component("velocity").value = np.zeros(2)

        # Clear one-time actions (so they don't repeat forever)
        self.current_input["cast_raze"] = None
        self.current_input["cast_requiem"] = False
        self.current_input["use_item"] = None
        self.current_input["stop"] = False
        self.current_input["move_target"] = None  # persistent until new packet