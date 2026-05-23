"""Network client for connecting to game server"""
import asyncio
import struct
import json


class GameClient:
    """Client for connecting to Dota2 Gym server"""
    
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None
        self.player_id = None
        self.connected = False
    
    async def connect(self):
        """Connect to server"""
        self.reader, self.writer = await asyncio.open_connection(
            self.host, self.port
        )
        
        # Wait for welcome packet
        header = await self.reader.readexactly(4)
        packet_type = struct.unpack('!I', header)[0]
        
        if packet_type == 0:  # Welcome
            data = await self.reader.readexactly(12)
            self.player_id, map_width, map_height = struct.unpack('!III', data)
            self.connected = True
            print(f"[Client] Connected as player {self.player_id}")
            return True
        
        return False
    
    async def send_input(self, tick, action_type, target_x, target_y, target_entity=-1):
        """Send input packet to server"""
        packet = struct.pack('!IIffI', 
            1,  # Input packet type
            tick, action_type, target_x, target_y, target_entity
        )
        self.writer.write(packet)
        await self.writer.drain()
    
    async def send_ready(self):
        """Send ready packet"""
        packet = struct.pack('!I', 2)  # Ready packet
        self.writer.write(packet)
        await self.writer.drain()
    
    async def receive_state(self):
        """Receive game state from server"""
        header = await self.reader.readexactly(12)
        packet_type, tick, data_length = struct.unpack('!III', header)
        
        if packet_type == 3:  # State packet
            json_data = await self.reader.readexactly(data_length)
            state = json.loads(json_data)
            return state
        
        return None
    
    async def disconnect(self):
        """Disconnect from server"""
        if self.writer:
            packet = struct.pack('!I', 99)  # Disconnect
            self.writer.write(packet)
            await self.writer.drain()
            self.writer.close()
            await self.writer.wait_closed()
            self.connected = False