"""
Game Model with proper base positions and all systems
"""
import numpy as np
import json
import os
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass

from engine.ecs.entity_manager import EntityManager
from engine.ecs.components import *
from engine.systems.movement_system import MovementSystem
from engine.systems.combat_system import CombatSystem
from engine.systems.spatial_hash import SpatialHash
from engine.config_loader import ConfigLoader
from engine.systems.creep_system import CreepSpawner, CreepAI
from engine.systems.tower_system import TowerSystem
from engine.systems.ability_system import AbilitySystem
from engine.systems.item_system import ItemSystem
from engine.systems.stair_geometry import (
    Vec2, StairPolygon, ElevationZone, generate_stair_polygon,
    is_point_in_polygon, get_elevation_at_position, can_cross_elevation_directly,
    find_nearest_stair_to_position, find_path_a_star
)


class StairRegistry:
    """
    Registry for managing stairs and elevation zones in the game world.
    Loads stair data from map_polygons.txt and provides query methods
    for pathfinding and elevation detection.
    """
    
    def __init__(self, config: Dict):
        self.stairs: List[StairPolygon] = []
        self.elevation_zones: List[ElevationZone] = []
        self.stair_thickness = config.get('movement', {}).get('stair_thickness', 15.0)
    
    def load_stairs_from_file(self, filepath: str) -> None:
        """
        Load stairs and elevation zones from map_polygons.txt file.
        
        File format:
        - Elevation zone name (header)
        - Polygon vertices as "x,y x,y x,y ..."
        - "Stairs" section header
        - Stair definitions as "S_name x1,y1 x2,y2"
        """
        self.stairs = []
        self.elevation_zones = []
        
        if not os.path.exists(filepath):
            print(f"[StairRegistry] Warning: File not found: {filepath}")
            return
        
        with open(filepath, 'r') as f:
            lines = [line.strip() for line in f.readlines()]
        
        current_section = None
        current_zone_name = None
        
        for line in lines:
            if not line:
                continue
            
            # Check for section headers - only switch to stairs section if line is exactly "stairs"
            if line.lower() == 'stairs':
                current_section = 'stairs'
                continue
            
            # Check if this is a zone name (non-polygon line)
            if current_section != 'stairs':
                # Check if this is a zone name line (doesn't start with digit after first word)
                if not line[:10].replace(' ', '')[0].isdigit():
                    current_zone_name = line
                    continue
                
                # Parse polygon vertices
                try:
                    vertices = self._parse_vertices(line)
                    if vertices and len(vertices) >= 3:
                        # Determine elevation based on zone name
                        if current_zone_name and 'low_ground' in current_zone_name.lower():
                            elevation = 0.0  # Low ground
                        else:
                            elevation = 2.0  # High ground (default)
                        
                        zone = ElevationZone(
                            name=current_zone_name or f"elevation_{len(self.elevation_zones)}",
                            elevation=elevation,
                            polygon=vertices
                        )
                        self.elevation_zones.append(zone)
                        current_zone_name = None  # Reset for next zone
                except ValueError:
                    pass
            else:
                # Parse stair definition
                try:
                    parts = line.split()
                    if len(parts) >= 3:
                        stair_name = parts[0]
                        p1 = self._parse_point(parts[1])
                        p2 = self._parse_point(parts[2])
                        
                        if p1 and p2:
                            p1_vec = Vec2(p1[0], p1[1])
                            p2_vec = Vec2(p2[0], p2[1])
                            
                            # Generate thickened stair polygon
                            polygon = generate_stair_polygon(
                                (p1[0], p1[1]), 
                                (p2[0], p2[1]), 
                                self.stair_thickness
                            )
                            
                            stair = StairPolygon(
                                name=stair_name,
                                p1=p1_vec,
                                p2=p2_vec,
                                polygon=polygon,
                                thickness=self.stair_thickness
                            )
                            self.stairs.append(stair)
                except (ValueError, IndexError):
                    pass
        
        print(f"[StairRegistry] Loaded {len(self.stairs)} stairs and {len(self.elevation_zones)} elevation zones")
    
    def _parse_point(self, point_str: str) -> Optional[Tuple[float, float]]:
        """Parse a point string like 'x,y' into a tuple"""
        try:
            parts = point_str.split(',')
            if len(parts) == 2:
                return (float(parts[0]), float(parts[1]))
        except (ValueError, IndexError):
            pass
        return None
    
    def _parse_vertices(self, line: str) -> List[Vec2]:
        """Parse a line of space-separated vertices into Vec2 list"""
        vertices = []
        parts = line.split()
        for part in parts:
            point = self._parse_point(part)
            if point:
                vertices.append(Vec2(point[0], point[1]))
        return vertices
    
    def get_all_stairs(self) -> List[StairPolygon]:
        """Return all loaded stairs"""
        return self.stairs
    
    def get_elevation_zones(self) -> List[ElevationZone]:
        """Return all elevation zones"""
        return self.elevation_zones
    
    def get_elevation_at_position(self, position: Vec2) -> float:
        """
        Get the elevation level at a given position.
        Returns 0.0 for river/low ground, 1.0 for default low ground, 2.0 for high ground.
        Position should be in game coordinates (0-7000), which will be scaled to (0-700) for comparison.
        """
        # Scale position to match polygon coordinates (polygons use 0-700, game uses 0-7000)
        scaled_pos = Vec2(position.x * 0.1, position.y * 0.1)
        return get_elevation_at_position(scaled_pos, self.elevation_zones)
    
    def find_optimal_stair(self, from_pos: Vec2, to_pos: Vec2) -> Optional[StairPolygon]:
        """
        Find the optimal stair for moving from from_pos to to_pos.
        Returns the stair that minimizes total travel distance.
        """
        from_elev = self.get_elevation_at_position(from_pos)
        to_elev = self.get_elevation_at_position(to_pos)
        
        # Same elevation - no stair needed
        if from_elev == to_elev:
            return None
        
        # Scale positions for stair lookup (use consistent 10x scaling)
        scaled_from = Vec2(from_pos.x * 0.1, from_pos.y * 0.1)
        scaled_to = Vec2(to_pos.x * 0.1, to_pos.y * 0.1)
        
        # Calculate max search distance based on direct distance
        direct_dist = (scaled_to - scaled_from).length()
        max_stair_search = min(direct_dist * 1.5, 200.0)  # Search within 1.5x direct distance, max 200 units
        
        # Find nearest stair on current elevation
        nearest_stair, _ = find_nearest_stair_to_position(
            scaled_from, self.stairs, from_elev, max_stair_search
        )
        
        return nearest_stair
    
    def find_stair_by_name_with_scaling(self, stair_name: str) -> Optional[StairPolygon]:
        """
        Find a stair by name and return it with game-scale coordinates (10x).
        """
        for stair in self.stairs:
            if stair.name == stair_name:
                # Return stair with scaled coordinates for game world
                return StairPolygon(
                    name=stair.name,
                    p1=Vec2(stair.p1.x * 10, stair.p1.y * 10),
                    p2=Vec2(stair.p2.x * 10, stair.p2.y * 10),
                    polygon=[Vec2(p.x * 10, p.y * 10) for p in stair.polygon],
                    thickness=stair.thickness * 10
                )
        return None
    
    def can_move_directly(self, from_pos: Vec2, to_pos: Vec2) -> bool:
        """
        Check if direct movement between positions is allowed.
        Returns False if crossing elevation boundary without using a stair.
        """
        # Scale positions for elevation check
        scaled_from = Vec2(from_pos.x * 0.1, from_pos.y * 0.1)
        scaled_to = Vec2(to_pos.x * 0.1, to_pos.y * 0.1)
        
        # Scale stairs for intersection check → stairs already in mini-coords
        scaled_stairs = []
        for stair in self.stairs:
            scaled_stairs.append(StairPolygon(
                name=stair.name,
                p1=Vec2(stair.p1.x, stair.p1.y),
                p2=Vec2(stair.p2.x, stair.p2.y),
                polygon=[Vec2(p.x, p.y) for p in stair.polygon],
                thickness=stair.thickness
            ))
        
        return can_cross_elevation_directly(
            scaled_from, scaled_to, self.elevation_zones, scaled_stairs
        )
    
    def find_stair_waypoints(self, from_pos: Vec2, to_pos: Vec2) -> Optional[List[Vec2]]:
        """
        Find waypoints for navigating from from_pos to to_pos using stairs.
        Returns list of waypoints (including final target), or None if no path.
        """
        # Scale positions for pathfinding
        scaled_from = Vec2(from_pos.x * 0.1, from_pos.y * 0.1)
        scaled_to = Vec2(to_pos.x * 0.1, to_pos.y * 0.1)
        
        # Let A* pathfinding decide the best route (Fix 8)
        # Removed early return: if self.can_move_directly(from_pos, to_pos):
        #     return [to_pos]
        
        # Convert stairs to format expected by find_path_a_star (already scaled)
        scaled_stairs = []
        for stair in self.stairs:
            scaled_stairs.append(StairPolygon(
                name=stair.name,
                p1=Vec2(stair.p1.x, stair.p1.y),
                p2=Vec2(stair.p2.x, stair.p2.y),
                polygon=[Vec2(p.x, p.y) for p in stair.polygon],
                thickness=stair.thickness
            ))
        
        # Use A* pathfinding with stair endpoints
        high_polys = [zone.polygon for zone in self.elevation_zones]
        path = find_path_a_star(scaled_from, scaled_to, high_polys, scaled_stairs)
        
        if path:
            # Scale path back to game coordinates
            return [Vec2(p.x * 10, p.y * 10) for p in path]
        
        return None
    
    def get_stair_by_name(self, name: str) -> Optional[StairPolygon]:
        """Find a stair by its name"""
        for stair in self.stairs:
            if stair.name == name:
                return stair
        return None
    
    def get_stair_endpoints(self) -> List[Vec2]:
        """Get all unique stair endpoints"""
        endpoints = []
        seen = set()
        
        for stair in self.stairs:
            p1_key = (round(stair.p1.x, 3), round(stair.p1.y, 3))
            p2_key = (round(stair.p2.x, 3), round(stair.p2.y, 3))
            
            if p1_key not in seen:
                endpoints.append(stair.p1)
                seen.add(p1_key)
            if p2_key not in seen:
                endpoints.append(stair.p2)
                seen.add(p2_key)
        
        return endpoints
    
    def is_on_stair(self, x: float, y: float) -> bool:
        """Check if position is on any stair (FIX 9)"""
        pos = Vec2(x * 0.1, y * 0.1)  # Scale to stair coordinates
        for stair in self.stairs:
            if stair.is_point_on_stair(pos, stair.thickness):
                return True
        return False
    
    def get_stair_polygons_dict(self) -> dict:
        """Get stair polygons as a dictionary for movement system (FIX 4)"""
        result = {}
        for stair in self.stairs:
            result[stair.name] = {
                'from_elevation': 2.0,  # High ground to low ground
                'to_elevation': 1.0,
                'polygon': stair.polygon,
                'center': (stair.midpoint.x * 10, stair.midpoint.y * 10),
                'waypoints': [(stair.p1.x * 10, stair.p1.y * 10), (stair.p2.x * 10, stair.p2.y * 10)]
            }
        return result


class GameModel:
    """
    Enhanced game state with all features
    """
    
    def __init__(self, config: Dict):
        self.config = config
        
        # Core ECS
        self.entity_manager = EntityManager()
        self.spatial_hash = SpatialHash()
        self.entity_manager.spatial_hash = self.spatial_hash  # Link spatial hash to entity manager
        
        # Systems
        dt = 1.0 / config['game']['tick_rate']
        self.movement_system = MovementSystem(self.entity_manager, dt, self)
        self.combat_system = CombatSystem(self.entity_manager, dt, self)
        self.creep_spawner = CreepSpawner(self.entity_manager, config)
        self.creep_ai = CreepAI(self.entity_manager, self.creep_spawner)
        self.tower_system = TowerSystem(self.entity_manager)
        self.ability_system = AbilitySystem(self.entity_manager, dt)
        self.item_system = ItemSystem(self.entity_manager, dt)
        
        # Game state
        self.tick_count = 0
        self.game_time = 0.0
        self.dt = dt
        self.game_ended = False
        self.winner = None
        
        # Pregame countdown state
        self.in_pregame = True
        self.pregame_countdown = 15.0  # 15 seconds pregame
        self.pregame_elapsed = 0.0
        
        # Gold popup system for visual feedback
        self.gold_popups: list = []
        
        # Player heroes
        self.player_heroes: Dict[int, int] = {}

        # Base positions
        self.radiant_base = (400, 6800)  # Top-left
        self.dire_base = (6800, 400)  # Bottom-right
        
        # Load configurations
        self.config_loader = ConfigLoader()
        self.sf_config = self.config_loader.load_hero_config('shadow_fiend')
        
        # Initialize StairRegistry for stair-aware pathfinding
        self.stair_registry = StairRegistry(config)
        
        # Find the config directory (look up from current directory structure)
        # Check multiple possible locations for map_polygons.txt
        possible_paths = [
            os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'map_polygons.txt'),
            os.path.join(os.path.dirname(__file__), '..', '..', '..', 'config', 'map_polygons.txt'),
            os.path.join(os.path.dirname(__file__), 'config', 'map_polygons.txt'),
        ]
        
        polygon_file = None
        for path in possible_paths:
            if os.path.exists(path):
                polygon_file = path
                break
        
        if polygon_file:
            self.stair_registry.load_stairs_from_file(polygon_file)
        else:
            print(f"[StairRegistry] Warning: Could not find map_polygons.txt in any of these locations:")
            for path in possible_paths:
                print(f"  - {path}")
        
        # Pass registry and spatial hash to movement system
        self.movement_system.set_stair_registry(self.stair_registry)
    
    @property
    def stair_geometry(self):
        """Access to stair geometry utilities (FIX 4, 5, 9)"""
        return self.stair_registry
    
    def get_elevation_at_position(self, x: float, y: float) -> float:
        """Get elevation at a position (FIX 4, 5, 9)"""
        pos = Vec2(x, y)
        return self.stair_registry.get_elevation_at_position(pos)
    
    def initialize_game(self) -> None:
        """Initialize a new game"""
        print("\n" + "="*50)
        print("INITIALIZING GAME")
        print("="*50)
        
        # Create Radiant Shadow Fiend (bottom-left, in base)
        self.player_heroes[0] = self._create_shadow_fiend(
            team=0,
            x=self.radiant_base[0],
            y=self.radiant_base[1]
        )
        
        # Create Dire Shadow Fiend (top-right, in base)
        self.player_heroes[1] = self._create_shadow_fiend(
            team=1,
            x=self.dire_base[0],
            y=self.dire_base[1]
        )
        
        # Create towers along diagonal between bases
        if self.tower_system:
            # Mid lane towers
            # Radiant towers (near top-left base)
            self.tower_system.create_tower(team=0, tier=1, x=2800, y=4400)
            self.tower_system.create_tower(team=0, tier=2, x=2100, y=5100)
            self.tower_system.create_tower(team=0, tier=3, x=1300, y=5900)

            # Dire towers (near bottom-right base)
            self.tower_system.create_tower(team=1, tier=1, x=4400, y=2800)
            self.tower_system.create_tower(team=1, tier=2, x=5100, y=2100)
            self.tower_system.create_tower(team=1, tier=3, x=5900, y=1300)

            # Top lane towers
            # Radiant top lane
            self.tower_system.create_tower(team=0, tier=1, x=500, y=2400)
            self.tower_system.create_tower(team=0, tier=2, x=500, y=4000)
            self.tower_system.create_tower(team=0, tier=3, x=500, y=5400)            

            # Dire top lane
            self.tower_system.create_tower(team=1, tier=1, x=1600, y=600)
            self.tower_system.create_tower(team=1, tier=2, x=3600, y=600)
            self.tower_system.create_tower(team=1, tier=3, x=5400, y=600)

            # Bottom lane towers
            # Radiant bottom lane
            self.tower_system.create_tower(team=0, tier=1, x=5600, y=6600)
            self.tower_system.create_tower(team=0, tier=2, x=3600, y=6600)
            self.tower_system.create_tower(team=0, tier=3, x=1800, y=6600)

            # Dire bottom lane
            self.tower_system.create_tower(team=1, tier=1, x=6700, y=4800)
            self.tower_system.create_tower(team=1, tier=2, x=6700, y=3400)
            self.tower_system.create_tower(team=1, tier=3, x=6700, y=2000)
        
        print(f"✓ Created 2 Shadow Fiend heroes")
        print(f"  Radiant (Team 0): Entity {self.player_heroes[0]} at {self.radiant_base}")
        print(f"  Dire (Team 1): Entity {self.player_heroes[1]} at {self.dire_base}")
        print(f"✓ Created 18 towers (3 per lane for 3 lanes)")
        print("="*50 + "\n")
    
    def _create_shadow_fiend(self, team: int, x: float, y: float) -> int:
        """Create a Shadow Fiend hero entity"""
        entity_id = self.entity_manager.create_entity()
        
        base = self.sf_config['base_stats']
        
        # Calculate stats
        max_hp = base['base_hp'] + base['strength'] * 20
        max_mana = base['base_mana'] + base['intelligence'] * 12
        
        # Add components
        self.entity_manager.add_component(
            entity_id, 'position',
            PositionComponent(x, y)
        )
        
        self.entity_manager.add_component(
            entity_id, 'velocity',
            VelocityComponent(0.0, 0.0)
        )
        
        self.entity_manager.add_component(
            entity_id, 'movement',
            MovementComponent(move_speed=base['movement_speed'])
        )
        
        self.entity_manager.add_component(
            entity_id, 'stats',
            StatsComponent(
                max_hp=max_hp,
                current_hp=max_hp,
                max_mana=max_mana,
                current_mana=max_mana,
                armor=base['base_armor'],
                magic_resist=base['base_magic_resist']
            )
        )
        
        self.entity_manager.add_component(
            entity_id, 'hero',
            HeroComponent(
                hero_id='shadow_fiend',
                level=1,
                strength=base['strength'],
                agility=base['agility'],
                intelligence=base['intelligence'],
                souls=0,
                team=team,
                facing_angle=-np.pi/4 if team == 0 else 3*np.pi/4,  # Face towards enemy base
                kills=0,
                deaths=0,
                assists=0,
                last_hits=0,
                denies=0
            )
        )
        
        self.entity_manager.add_component(
            entity_id, 'combat',
            CombatComponent(
                damage_min=base['base_damage_min'],
                damage_max=base['base_damage_max'],
                attack_range=base['base_attack_range'],
                attack_speed=base['base_attack_speed'],
                attack_cooldown=1.7,
                last_attack_time=-10.0  # Can attack immediately
            )
        )
        
        self.entity_manager.add_component(
            entity_id, 'collision',
            CollisionComponent(radius=36.0)  # Increased by 50% from 24
        )

        # Add selection component
        from engine.ecs.components import SelectionComponent
        self.entity_manager.add_component(
            entity_id, 'selection',
            SelectionComponent(selected=(team == 0), selectable=True)
        )
        
        # Add ability component
        from engine.ecs.components import AbilityComponent
        self.entity_manager.add_component(
            entity_id, 'ability',
            AbilityComponent()
        )
        
        # Add inventory component
        try:
            from engine.systems.item_system import InventoryComponent
            self.entity_manager.add_component(
                entity_id, 'inventory',
                InventoryComponent(gold=625)  # Starting gold
            )
        except ImportError:
            pass
        
        return entity_id
    
    def tick(self) -> None:
        """Update game state by one tick"""
        import time
        frame_start = time.perf_counter()
        MAX_FRAME_TIME = 0.016  # 60 FPS budget
        
        # Handle pregame countdown
        if self.in_pregame:
            self.pregame_elapsed += self.dt
            if self.pregame_elapsed >= self.pregame_countdown:
                self.in_pregame = False
                self.pregame_elapsed = 0.0
                self.game_time = 0.0
                self.tick_count = 0
                print("\n" + "="*50)
                print("GAME START! Creeps spawning...")
                print("="*50 + "\n")
            
            # Update systems during pregame (movement, combat, etc.)
            self.movement_system.update()
            self.combat_system.update()
            self.ability_system.update()
            self.item_system.update()
            self._update_necromastery()
            self._update_hero_facing()
            self._update_spatial_hash()
            return  # Skip creep/tower updates during pregame
        
        self.tick_count += 1
        self.game_time += self.dt
        
        # Update systems (skip during pregame)
        self.movement_system.update()
        
        # Check frame budget before combat system
        if time.perf_counter() - frame_start > MAX_FRAME_TIME:
            return  # Skip remaining updates this frame
        
        self.combat_system.update()
        
        # Check frame budget before creep AI
        if time.perf_counter() - frame_start > MAX_FRAME_TIME:
            return  # Skip remaining updates this frame
        
        if not self.in_pregame:
            self.creep_spawner.update(self.game_time)
            self.creep_ai.update(self.movement_system, self.combat_system, self.game_time)
            
            # Check frame budget before tower system
            if time.perf_counter() - frame_start > MAX_FRAME_TIME:
                return  # Skip remaining updates this frame
            
            self.tower_system.update(self.combat_system, self.game_time)
        self.ability_system.update()
        self.item_system.update()
        
        # Update Necromastery bonuses
        self._update_necromastery()

        # Update hero facing angles
        self._update_hero_facing()
        
        # Check win condition
        self._check_win_condition()
        
        # Update spatial hash
        self._update_spatial_hash()
        
        # Update gold popups
        self._update_gold_popups()
        
        # Cleanup dead entities
        self._cleanup_dead_entities()
    
    def _update_necromastery(self) -> None:
        """Update Shadow Fiend combat stats based on souls"""
        necro = self.sf_config['necromastery']
        
        for hero_id in self.entity_manager.get_entities_with_component('hero'):
            hero = self.entity_manager.get_component(hero_id, 'hero')
            combat = self.entity_manager.get_component(hero_id, 'combat')
            
            if hero and combat and hero.hero_id == 'shadow_fiend':
                bonus_damage = hero.souls * necro['damage_per_soul']
                bonus_range = hero.souls * necro['attack_range_per_soul']
                
                base = self.sf_config['base_stats']
                combat.damage_min = base['base_damage_min'] + bonus_damage
                combat.damage_max = base['base_damage_max'] + bonus_damage
                combat.attack_range = base['base_attack_range'] + bonus_range
    
    def _update_hero_facing(self) -> None:
        """Update hero facing angles based on movement"""
        for hero_id in self.entity_manager.get_entities_with_component('hero'):
            hero = self.entity_manager.get_component(hero_id, 'hero')
            position = self.entity_manager.get_component(hero_id, 'position')
            movement = self.entity_manager.get_component(hero_id, 'movement')
            
            if hero and position and movement:
                if movement.is_moving and movement.target_x is not None:
                    # Calculate angle to target
                    dx = movement.target_x - position.x
                    dy = movement.target_y - position.y
                    hero.facing_angle = float(np.arctan2(dy, dx))
    
    def _check_win_condition(self) -> None:
        """Check if game has ended"""
        if self.game_ended:
            return
        
        # Check if any tower is destroyed
        if self.tower_system:
            towers = self.entity_manager.get_entities_with_component('tower')
            for tower_id in towers:
                stats = self.entity_manager.get_component(tower_id, 'stats')
                tower = self.entity_manager.get_component(tower_id, 'tower')
                
                if stats and tower and not stats.is_alive():
                    self.game_ended = True
                    self.winner = 1 - tower.team
                    print(f"\n{'='*50}")
                    print(f"GAME OVER! Tower destroyed!")
                    print(f"Winner: {'Radiant' if self.winner == 0 else 'Dire'}")
                    print(f"{'='*50}\n")
                    return
        
        # Check if any hero is dead
        for player_id, hero_id in self.player_heroes.items():
            stats = self.entity_manager.get_component(hero_id, 'stats')
            hero = self.entity_manager.get_component(hero_id, 'hero')
            
            if stats and hero and not stats.is_alive():
                hero.deaths += 1
                self.game_ended = True
                self.winner = 1 - hero.team
                print(f"\n{'='*50}")
                print(f"GAME OVER! Hero killed!")
                print(f"Winner: {'Radiant' if self.winner == 0 else 'Dire'}")
                print(f"{'='*50}\n")
                return
    
    def _cleanup_dead_entities(self) -> None:
        """Remove dead entities"""
        to_remove = []
        
        for entity_id in self.entity_manager.get_all_entities():
            stats = self.entity_manager.get_component(entity_id, 'stats')
            
            # Don't remove heroes or towers
            if (self.entity_manager.has_component(entity_id, 'hero') or
                self.entity_manager.has_component(entity_id, 'tower')):
                continue
            
            if stats and not stats.is_alive():
                to_remove.append(entity_id)
        
        for entity_id in to_remove:
            # Remove from spatial hash before destroying (FIX 3)
            pos = self.entity_manager.get_component(entity_id, 'position')
            if pos:
                self.spatial_hash.remove_at_position(entity_id, pos.x, pos.y)
            self.entity_manager.destroy_entity(entity_id)
    
    def _update_spatial_hash(self) -> None:
        """Update spatial hash incrementally - only update entities that moved"""
        for entity_id in self.entity_manager.get_entities_with_component('position'):
            position = self.entity_manager.get_component(entity_id, 'position')
            
            if position and hasattr(position, 'changed') and position.changed:
                # Remove from old location (spatial hash tracks this internally)
                self.spatial_hash.remove(entity_id)
                # Add to new location
                self.spatial_hash.insert(entity_id, position.x, position.y)
                position.changed = False  # Reset flag
    
    def add_gold_popup(self, x: float, y: float, gold: int) -> None:
        """Add a gold popup at the specified location"""
        self.gold_popups.append({
            'x': x,
            'y': y,
            'gold': gold,
            'time': 1.0  # 1 second duration
        })
    
    def _update_gold_popups(self) -> None:
        """Update gold popup timers and remove expired ones"""
        expired = []
        for popup in self.gold_popups:
            popup['time'] -= self.dt
            if popup['time'] <= 0:
                expired.append(popup)
        
        for popup in expired:
            self.gold_popups.remove(popup)
    
    def save_snapshot(self) -> str:
        """Save game state to JSON"""
        state = {
            'tick_count': self.tick_count,
            'game_time': self.game_time,
            'entities': []
        }
        
        for entity_id in self.entity_manager.get_all_entities():
            entity_data = {'id': entity_id}
            
            # Save all components
            for comp_type in ['position', 'stats', 'hero', 'combat']:
                comp = self.entity_manager.get_component(entity_id, comp_type)
                if comp:
                    entity_data[comp_type] = comp.__dict__
            
            state['entities'].append(entity_data)
        
        return json.dumps(state, indent=2)
    
    def load_snapshot(self, snapshot_json: str) -> None:
        """Load game state from JSON"""
        state = json.loads(snapshot_json)
        
        # Clear current state
        self.entity_manager.clear()
        
        # Restore game state
        self.tick_count = state['tick_count']
        self.game_time = state['game_time']
        
        # Restore entities
        for entity_data in state['entities']:
            # Note: This is simplified - full implementation would
            # restore all components properly
            pass
        
        print(f"[Snapshot] Loaded state from tick {self.tick_count}")