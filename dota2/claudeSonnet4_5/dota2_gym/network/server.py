#!/usr/bin/env python3
"""
Lockstep Networking Server
Handles game state synchronization between clients
"""
import asyncio
import struct
import json
from typing import Dict, List, Set
from dataclasses import dataclass
from engine.model.game_model import GameModel


@dataclass
class PlayerInput:
    """Player input packet"""
    player_id: int
    tick: int
    action_type: int  # 0=move, 1=attack, 2=ability
    target_x: float
    target_y: float
    target_entity: int = -1
    ability_key: str = ""


class GameServer:
    """Authoritative game server with lockstep synchronization"""
    
    def __init__(self, config: Dict, port: int = 8888):
        self.config = config
        self.port = port
        self.game_model = GameModel(config)
        
        # Network state
        self.clients: Dict[int, asyncio.StreamWriter] = {}
        self.player_inputs: Dict[int, List[PlayerInput]] = {}
        self.ready_players: Set[int] = set()
        
        # Game state
        self.current_tick = 0
        self.running = False
        self.max_players = 2
        
    async def start(self):
        """Start the server"""
        server = await asyncio.start_server(
            self.handle_client, 
            '0.0.0.0', 
            self.port
        )
        
        print(f"[Server] Listening on port {self.port}")
        print(f"[Server] Waiting for {self.max_players} players...")
        
        async with server:
            await server.serve_forever()
    
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle new client connection"""
        addr = writer.get_extra_info('peername')
        print(f"[Server] New connection from {addr}")
        
        # Assign player ID
        player_id = len(self.clients)
        
        if player_id >= self.max_players:
            print(f"[Server] Rejected {addr} - game full")
            writer.close()
            await writer.wait_closed()
            return
        
        self.clients[player_id] = writer
        self.player_inputs[player_id] = []
        
        # Send welcome packet
        await self.send_welcome(player_id, writer)
        
        print(f"[Server] Player {player_id} connected from {addr}")
        
        # Start game when all players connected
        if len(self.clients) == self.max_players and not self.running:
            await self.start_game()
        
        # Handle client messages
        try:
            while True:
                # Read packet header (4 bytes: packet type)
                header = await reader.readexactly(4)
                packet_type = struct.unpack('!I', header)[0]
                
                if packet_type == 1:  # Input packet
                    await self.handle_input_packet(player_id, reader)
                elif packet_type == 2:  # Ready packet
                    self.ready_players.add(player_id)
                elif packet_type == 99:  # Disconnect
                    break
                    
        except asyncio.IncompleteReadError:
            print(f"[Server] Player {player_id} disconnected")
        except Exception as e:
            print(f"[Server] Error with player {player_id}: {e}")
        finally:
            if player_id in self.clients:
                del self.clients[player_id]
            writer.close()
            await writer.wait_closed()
    
    async def send_welcome(self, player_id: int, writer: asyncio.StreamWriter):
        """Send welcome packet to client"""
        # Packet: [type(4)] [player_id(4)] [map_width(4)] [map_height(4)]
        packet = struct.pack('!IIII', 
            0,  # Welcome packet type
            player_id,
            self.config['game']['map_width'],
            self.config['game']['map_height']
        )
        writer.write(packet)
        await writer.drain()
    
    async def handle_input_packet(self, player_id: int, reader: asyncio.StreamReader):
        """Handle input packet from client"""
        # Packet format: [tick(4)] [action_type(4)] [target_x(4f)] [target_y(4f)] [target_entity(4)]
        data = await reader.readexactly(24)
        tick, action_type, target_x, target_y, target_entity = struct.unpack('!IIffI', data)
        
        input_data = PlayerInput(
            player_id=player_id,
            tick=tick,
            action_type=action_type,
            target_x=target_x,
            target_y=target_y,
            target_entity=target_entity
        )
        
        self.player_inputs[player_id].append(input_data)
    
    async def start_game(self):
        """Initialize and start the game loop"""
        print("[Server] All players connected - starting game!")
        
        self.game_model.initialize_game()
        self.running = True
        
        # Broadcast initial state
        await self.broadcast_state()
        
        # Start game loop
        asyncio.create_task(self.game_loop())
    
    async def game_loop(self):
        """Main game loop - lockstep tick processing"""
        tick_rate = self.config['game']['tick_rate']
        tick_interval = 1.0 / tick_rate
        
        while self.running:
            start_time = asyncio.get_event_loop().time()
            
            # Wait for all players to be ready for this tick
            while len(self.ready_players) < len(self.clients):
                await asyncio.sleep(0.001)
            
            self.ready_players.clear()
            
            # Process inputs for this tick
            self.process_inputs()
            
            # Tick game simulation
            self.game_model.tick()
            self.current_tick += 1
            
            # Broadcast state to all clients
            await self.broadcast_state()
            
            # Maintain tick rate
            elapsed = asyncio.get_event_loop().time() - start_time
            sleep_time = max(0, tick_interval - elapsed)
            await asyncio.sleep(sleep_time)
    
    def process_inputs(self):
        """Process all player inputs for current tick"""
        for player_id, inputs in self.player_inputs.items():
            if player_id not in self.game_model.player_heroes:
                continue
            
            hero_id = self.game_model.player_heroes[player_id]
            
            for input_data in inputs:
                if input_data.tick != self.current_tick:
                    continue
                
                if input_data.action_type == 0:  # Move
                    self.game_model.movement_system.set_move_target(
                        hero_id, input_data.target_x, input_data.target_y
                    )
                elif input_data.action_type == 1:  # Attack
                    target_pos = self.game_model.entity_manager.get_component(
                        input_data.target_entity, 'position'
                    )
                    if target_pos:
                        self.game_model.combat_system.create_attack_projectile(
                            hero_id, target_pos.x, target_pos.y
                        )
            
            # Clear processed inputs
            self.player_inputs[player_id] = [
                i for i in inputs if i.tick > self.current_tick
            ]
    
    async def broadcast_state(self):
        """Broadcast game state to all connected clients"""
        state_data = self.serialize_state()
        
        # Packet: [type(4)] [tick(4)] [data_length(4)] [json_data]
        json_bytes = json.dumps(state_data).encode('utf-8')
        packet = struct.pack('!III', 3, self.current_tick, len(json_bytes)) + json_bytes
        
        for player_id, writer in self.clients.items():
            try:
                writer.write(packet)
                await writer.drain()
            except Exception as e:
                print(f"[Server] Error sending to player {player_id}: {e}")
    
    def serialize_state(self) -> Dict:
        """Serialize game state to dictionary"""
        em = self.game_model.entity_manager
        
        entities = []
        for entity_id in em.get_all_entities():
            position = em.get_component(entity_id, 'position')
            hero = em.get_component(entity_id, 'hero')
            stats = em.get_component(entity_id, 'stats')
            projectile = em.get_component(entity_id, 'projectile')
            
            entity_data = {
                'id': entity_id,
                'type': 'hero' if hero else 'projectile' if projectile else 'unknown'
            }
            
            if position:
                entity_data['x'] = position.x
                entity_data['y'] = position.y
            
            if hero:
                entity_data['team'] = hero.team
                entity_data['souls'] = hero.souls
            
            if stats:
                entity_data['hp'] = stats.current_hp
                entity_data['max_hp'] = stats.max_hp
            
            entities.append(entity_data)
        
        return {
            'tick': self.current_tick,
            'game_time': self.game_model.game_time,
            'entities': entities
        }


async def main():
    """Run the server"""
    from engine.config_loader import ConfigLoader
    
    config_loader = ConfigLoader()
    config = config_loader.load_game_config('config/game_config.yaml')
    
    server = GameServer(config)
    await server.start()


if __name__ == '__main__':
    asyncio.run(main())