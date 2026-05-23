"""Combat system handling attacks and projectiles """
import numpy as np
from engine.ecs.entity_manager import EntityManager
from engine.ecs.components import (
    PositionComponent, ProjectileComponent, StatsComponent,
    CombatComponent, HeroComponent, CollisionComponent
)


class CombatSystem:
    """
    Handles combat mechanics:
    - Attack commands and cooldowns
    - Projectile movement
    - Collision detection
    - Damage application
    - Soul collection (Necromastery)
    - Last hits tracking
    """
    
    def __init__(self, entity_manager: EntityManager, dt: float = 1/15, game_model=None):
        self.entity_manager = entity_manager
        self.dt = dt
        self.current_time = 0.0
        self.game_model = game_model
    
    def update(self) -> None:
        """Update combat system"""
        self.current_time += self.dt
        
        # Check projectile collisions
        self._check_projectile_collisions()
        
        # Update projectiles
        self._update_projectiles()
    
    def _update_projectiles(self) -> None:
        """Move all projectiles toward their targets"""
        projectiles = self.entity_manager.get_entities_with_component('projectile')
        get = self.entity_manager.get_component  # Local caching for performance

        for proj_id in list(projectiles):
            position = get(proj_id, 'position')
            projectile = get(proj_id, 'projectile')

            if not position or not projectile:
                continue

            # Check if source entity is still alive
            source_stats = get(projectile.source_entity, 'stats')
            if source_stats and not source_stats.is_alive():
                self.entity_manager.destroy_entity(proj_id)
                continue

            # Check if target entity is still alive
            if projectile.target_entity is not None:
                target_stats = get(projectile.target_entity, 'stats')
                if target_stats and not target_stats.is_alive():
                    self.entity_manager.destroy_entity(proj_id)
                    continue
            
            # Range fail-safe: despawn if projectile exceeds max range
            if hasattr(projectile, 'max_range'):
                dx = projectile.target_x - position.x
                dy = projectile.target_y - position.y
                if dx*dx + dy*dy > projectile.max_range * projectile.max_range:
                    self.entity_manager.destroy_entity(proj_id)
                    continue
            
            # If tracking a target entity, update target position dynamically
            if projectile.target_entity is not None:
                target_pos = get(projectile.target_entity, 'position')
                if target_pos:
                    projectile.target_x = target_pos.x
                    projectile.target_y = target_pos.y

            # Calculate direction to target
            current = np.array([position.x, position.y], dtype=np.float32)
            target = np.array([projectile.target_x, projectile.target_y], dtype=np.float32)
            direction = target - current
            distance = np.linalg.norm(direction)

            # Check if reached target
            if distance < 10.0:
                self.entity_manager.destroy_entity(proj_id)
                continue

            # Move projectile
            direction = direction / distance
            move_distance = projectile.speed * self.dt

            new_pos = current + direction * move_distance
            position.x = float(new_pos[0])
            position.y = float(new_pos[1])

            # Check lifetime
            projectile.lifetime -= self.dt
            if projectile.lifetime <= 0:
                self.entity_manager.destroy_entity(proj_id)
    
    def _check_projectile_collisions(self) -> None:
        """Check for projectile-entity collisions using spatial hash for efficiency"""
        projectiles = self.entity_manager.get_entities_with_component('projectile')
        get = self.entity_manager.get_component  # Local caching for performance
        
        # Get spatial hash for efficient nearby entity lookup
        spatial_hash = getattr(self.entity_manager, 'spatial_hash', None)
        
        for proj_id in list(projectiles):
            proj_pos = get(proj_id, 'position')
            projectile = get(proj_id, 'projectile')
            
            if not proj_pos or not projectile:
                continue
            
            # Use spatial hash to find nearby potential targets
            if spatial_hash and spatial_hash.cells:
                nearby_ids = spatial_hash.query_radius(proj_pos.x, proj_pos.y, 300)  # Max relevant range
            else:
                # Fallback: get all entities
                nearby_ids = set()
                nearby_ids.update(self.entity_manager.get_entities_with_component('hero'))
                nearby_ids.update(self.entity_manager.get_entities_with_component('creep'))
                nearby_ids.update(self.entity_manager.get_entities_with_component('tower'))
            
            # Check collision with nearby entities
            for entity_id in nearby_ids:
                if entity_id == projectile.source_entity:
                    continue
                
                entity_pos = get(entity_id, 'position')
                entity_hero = get(entity_id, 'hero')
                entity_creep = get(entity_id, 'creep')
                entity_tower = get(entity_id, 'tower')
                collision = get(entity_id, 'collision')
                stats = get(entity_id, 'stats')
                
                if not entity_pos or not collision or not stats:
                    continue
                
                # Skip if already dead
                if not stats.is_alive():
                    continue
                
                # Determine entity team
                entity_team = None
                if entity_hero:
                    entity_team = entity_hero.team
                elif entity_creep:
                    entity_team = entity_creep.team
                elif entity_tower:
                    entity_team = entity_tower.team
                
                # Skip same team
                if entity_team is None or entity_team == projectile.team:
                    continue
                
                # Check distance using squared distance to avoid sqrt
                dx = entity_pos.x - proj_pos.x
                dy = entity_pos.y - proj_pos.y
                dist_sq = dx*dx + dy*dy
                
                # Use collision.radius + 50.0 squared for comparison
                min_dist_sq = (collision.radius + 50.0) ** 2
                
                if dist_sq < min_dist_sq:
                    # Hit! Apply damage
                    actual_damage = stats.take_damage(projectile.damage)
                    
                    # Destroy projectile
                    self.entity_manager.destroy_entity(proj_id)
                    
                    # Check if killed hero
                    if entity_hero and not stats.is_alive():
                        self._on_hero_killed(entity_id, projectile.source_entity)
                    
                    # Award gold/xp for kill
                    if entity_creep and not stats.is_alive():
                        self._award_kill_credit(entity_id, projectile.source_entity, entity_creep)
                    
                    break  # Projectile destroyed, move to next
    
    def _award_kill_credit(self, victim_id: int, killer_id: int, victim_creep):
        """Award gold/xp for creep kill"""
        if self.entity_manager.has_component(killer_id, 'hero'):
            from engine.systems.item_system import InventoryComponent
            inventory = self.entity_manager.get_component(killer_id, 'inventory')
            hero = self.entity_manager.get_component(killer_id, 'hero')
            victim_pos = self.entity_manager.get_component(victim_id, 'position')
            
            if inventory:
                inventory.gold += victim_creep.gold_value
            
            if hero:
                hero.last_hits += 1
                
                # Collect creep soul
                if hero.hero_id == 'shadow_fiend':
                    soul_value = 1
                    hero.souls = min(hero.souls + soul_value, 100)
                
                # Add gold popup via game model
                if self.game_model and victim_pos:
                    self.game_model.add_gold_popup(victim_pos.x, victim_pos.y, victim_creep.gold_value)
    
    def _on_hero_killed(self, killed_id: int, killer_id: int) -> None:
        """Handle hero death - collect souls"""
        killer_hero = self.entity_manager.get_component(killer_id, 'hero')
        killed_hero = self.entity_manager.get_component(killed_id, 'hero')
        
        if killer_hero and killer_hero.hero_id == 'shadow_fiend':
            old_souls = killer_hero.souls
            killer_hero.souls = min(killer_hero.souls + 1, 36)
    
    def create_attack_projectile(self, source_id: int, target_x: float, target_y: float, target_entity: int = None, check_cooldown: bool = True) -> int:
        """Create an attack projectile from source to target"""
        source_pos = self.entity_manager.get_component(source_id, 'position')
        combat = self.entity_manager.get_component(source_id, 'combat')

        # Get team (hero or creep or tower)
        hero = self.entity_manager.get_component(source_id, 'hero')
        creep = self.entity_manager.get_component(source_id, 'creep')
        tower = self.entity_manager.get_component(source_id, 'tower')

        team = -1
        if hero:
            team = hero.team
        elif creep:
            team = creep.team
        elif tower:
            team = tower.team

        if not source_pos or not combat or team == -1:
            return -1

        # Check attack cooldown (can be bypassed for AOE attacks like towers)
        if check_cooldown and not combat.can_attack(self.current_time):
            return -1

        # Update last attack time
        combat.last_attack_time = self.current_time

        # Calculate damage
        damage = combat.get_random_damage()

        # Create projectile entity
        proj_id = self.entity_manager.create_entity()

        self.entity_manager.add_component(
            proj_id, 'position',
            PositionComponent(source_pos.x, source_pos.y)
        )

        self.entity_manager.add_component(
            proj_id, 'projectile',
            ProjectileComponent(
                source_entity=source_id,
                target_x=target_x,
                target_y=target_y,
                damage=damage,
                speed=1000.0,
                team=team,
                lifetime=10.0,
                target_entity=target_entity
            )
        )

        self.entity_manager.add_component(
            proj_id, 'collision',
            CollisionComponent(radius=10.0, blocks_movement=False)
        )

        return proj_id
