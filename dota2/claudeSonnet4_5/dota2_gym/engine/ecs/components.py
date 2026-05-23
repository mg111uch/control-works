"""Component definitions for ECS - FIXED"""
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Tuple


@dataclass
class PositionComponent:
    """Entity position in world space"""
    x: float
    y: float
    changed: bool = True  # Track if position has changed for optimization
    
    def as_array(self) -> np.ndarray:
        return np.array([self.x, self.y], dtype=np.float64)
    
    def distance_to(self, other: 'PositionComponent') -> float:
        """Calculate distance to another position"""
        dx = self.x - other.x
        dy = self.y - other.y
        return float(np.sqrt(dx*dx + dy*dy))  # Ensure float return


@dataclass
class VelocityComponent:
    """Entity velocity"""
    vx: float = 0.0
    vy: float = 0.0
    
    def as_array(self) -> np.ndarray:
        return np.array([self.vx, self.vy], dtype=np.float64)


@dataclass
class MovementComponent:
    """Movement state and target"""
    target_x: Optional[float] = None
    target_y: Optional[float] = None
    move_speed: float = 300.0
    is_moving: bool = False
    
    # Waypoint queue for stair navigation
    waypoint_queue: List[Tuple[float, float]] = field(default_factory=list)
    
    # Final destination (when using waypoints)
    final_target_x: Optional[float] = None
    final_target_y: Optional[float] = None
    
    # Stair navigation state
    current_stair_id: Optional[str] = None
    on_stair: bool = False
    stair_transition_distance: float = 50.0  # Distance to approach stair
    
    # Creep waypoint tracking
    current_waypoint_index: int = 0
    
    # Path caching for performance (FIX 1)
    path_cache: Optional[List[Tuple[float, float]]] = None
    path_cache_target: Optional[Tuple[float, float]] = None
    path_recalc_cooldown: float = 0.0


@dataclass
class StatsComponent:
    """Entity stats (HP, mana, armor, etc.)"""
    max_hp: float
    current_hp: float
    max_mana: float
    current_mana: float
    armor: float = 0.0
    magic_resist: float = 25.0
    
    def take_damage(self, damage: float) -> float:
        """Apply damage and return actual damage taken"""
        actual_damage = damage
        self.current_hp = max(0, self.current_hp - actual_damage)
        return actual_damage
    
    def is_alive(self) -> bool:
        """Check if entity is alive"""
        return self.current_hp > 0


@dataclass
class HeroComponent:
    """Hero-specific data"""
    hero_id: str
    level: int = 1
    strength: float = 20.0
    agility: float = 20.0
    intelligence: float = 20.0
    souls: int = 0  # For Shadow Fiend's Necromastery
    team: int = 0  # 0 = Radiant, 1 = Dire
    facing_angle: float = 0.0  # Direction hero is facing (radians)
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    last_hits: int = 0
    denies: int = 0


@dataclass
class CombatComponent:
    """Combat stats and state"""
    damage_min: float
    damage_max: float
    attack_range: float
    attack_speed: float
    attack_cooldown: float
    last_attack_time: float = -10.0  # Start with ability to attack immediately
    attack_target: Optional[int] = None
    cached_target: Optional[int] = None  # Target cache for performance (FIX 7)
    
    def can_attack(self, current_time: float) -> bool:
        """Check if enough time has passed to attack again"""
        return current_time >= self.last_attack_time + self.attack_cooldown
    
    def get_random_damage(self) -> float:
        """Get random damage in range"""
        return float(np.random.uniform(self.damage_min, self.damage_max))


@dataclass
class ProjectileComponent:
    """Projectile data"""
    source_entity: int
    target_x: float
    target_y: float
    damage: float
    speed: float
    team: int
    lifetime: float = 10.0  # Max lifetime in seconds
    target_entity: Optional[int] = None  # Entity ID to track for dynamic targeting


@dataclass
class CollisionComponent:
    """Collision data"""
    radius: float = 24.0
    blocks_movement: bool = True
    
    def overlaps(self, pos1: PositionComponent, pos2: PositionComponent, other_radius: float = 24.0) -> bool:
        """Check if this entity overlaps with another"""
        distance = pos1.distance_to(pos2)
        return distance < (self.radius + other_radius)


@dataclass
class TowerComponent:
    """Tower-specific data"""
    team: int
    tier: int  # 1, 2, or 3
    attack_damage: float = 100.0
    attack_range: float = 700.0
    attack_cooldown: float = 1.0
    last_attack_time: float = -10.0
    attack_target: Optional[int] = None
    
    def can_attack(self, current_time: float) -> bool:
        return current_time >= self.last_attack_time + self.attack_cooldown


@dataclass
class CreepComponent:
    """Creep-specific data"""
    team: int
    creep_type: str  # 'melee', 'ranged', 'siege'
    gold_value: int = 40
    xp_value: int = 62
    

@dataclass
class AIComponent:
    """AI behavior component"""
    state: str = 'move_to_lane'  # 'move_to_lane', 'attack', 'defend'
    target_entity: Optional[int] = None
    aggro_range: float = 500.0
    follow_range: float = 800.0


@dataclass
class AbilityComponent:
    """Ability cooldown tracking"""
    q_cooldown: float = 0.0
    w_cooldown: float = 0.0
    e_cooldown: float = 0.0
    r_cooldown: float = 0.0
    
    q_ready: bool = True
    w_ready: bool = True
    e_ready: bool = True
    r_ready: bool = True


@dataclass
class SelectionComponent:
    """Selection state for units"""
    selected: bool = False
    selectable: bool = True