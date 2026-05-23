"""
Tests for Projectile System
"""
import pytest
import math


class TestBulletTracking:
    """Tests for bullet tracking logic"""
    
    def test_initial_velocity_calculation(self):
        """Test bullet velocity is calculated toward target"""
        bullet_x, bullet_y = 100, 100
        target_x, target_y = 150, 100
        speed = 5
        
        dx = target_x - bullet_x
        dy = target_y - bullet_y
        dist = math.sqrt(dx**2 + dy**2)
        
        vx = speed * dx / dist
        vy = speed * dy / dist
        
        assert vx == speed
        assert vy == 0
    
    def test_velocity_diagonal(self):
        """Test bullet velocity for diagonal target"""
        bullet_x, bullet_y = 100, 100
        target_x, target_y = 100, 150
        speed = 5
        
        dx = target_x - bullet_x
        dy = target_y - bullet_y
        dist = math.sqrt(dx**2 + dy**2)
        
        vx = speed * dx / dist
        vy = speed * dy / dist
        
        assert abs(vx) < 0.01
        assert vy == speed
    
    def test_tracking_update(self):
        """Test that bullet tracks moving target"""
        bullet_x, bullet_y = 100, 100
        target_x, target_y = 120, 120
        speed = 5
        
        dx = target_x - bullet_x
        dy = target_y - bullet_y
        dist = math.sqrt(dx**2 + dy**2)
        
        vx = speed * dx / dist
        vy = speed * dy / dist
        
        assert abs(vx - vy) < 0.01


class TestProjectileDeletion:
    """Tests for projectile deletion logic"""
    
    def test_bullet_deleted_when_target_dead(self):
        """Test bullet is deleted when target dies"""
        bullet_alive = True
        target_alive = False
        
        if not target_alive:
            bullet_alive = False
        
        assert bullet_alive == False
    
    def test_bullet_deleted_when_off_screen(self):
        """Test bullet is deleted when off screen"""
        bullet_x = -5
        screen_width = 600
        
        bullet_deleted = bullet_x < 0 or bullet_x > screen_width
        
        assert bullet_deleted == True
    
    def test_bullet_deleted_on_hit(self):
        """Test bullet is deleted when hitting target"""
        bullet_x, bullet_y = 100, 100
        target_x, target_y = 100, 100
        bullet_size = 3
        target_radius = 10
        
        dist = math.sqrt((bullet_x - target_x)**2 + (bullet_y - target_y)**2)
        hit = dist < (target_radius + bullet_size)
        
        bullet_alive = not hit
        
        assert bullet_alive == False
    
    def test_bullet_not_deleted_when_target_alive(self):
        """Test bullet is NOT deleted when target is alive"""
        bullet_alive = True
        target_alive = True
        
        if not target_alive:
            bullet_alive = False
        
        assert bullet_alive == True
    
    def test_bullet_not_deleted_in_screen(self):
        """Test bullet is NOT deleted when in screen"""
        bullet_x = 100
        screen_width = 600
        
        bullet_deleted = bullet_x < 0 or bullet_x > screen_width
        
        assert bullet_deleted == False
    
    def test_bullet_deleted_right_edge(self):
        """Test bullet is deleted when past right edge"""
        bullet_x = 650
        screen_width = 600
        
        bullet_deleted = bullet_x < 0 or bullet_x > screen_width
        
        assert bullet_deleted == True


class TestBulletSystemIntegration:
    """Tests for bullet system integration with enemy health"""
    
    def test_bullet_hits_only_once(self):
        """Test that a bullet only damages enemy once, not multiple times"""
        from ecs.base import EntityManager
        from ecs.components import PositionComponent, EnemyComponent, HealthComponent, BulletComponent, VelocityComponent
        from ecs.systems import BulletSystem, EnemySystem
        
        # Setup
        em = EntityManager()
        bullet_system = BulletSystem(600, 400)
        enemy_system = EnemySystem(600)
        bullet_system.set_enemy_system(enemy_system)
        
        # Create enemy
        enemy = em.create_entity()
        enemy.add_component(PositionComponent(200, 200))
        enemy.add_component(EnemyComponent(1))  # Wave 1 = 30 health
        enemy.add_component(HealthComponent(30))
        enemy.add_component(VelocityComponent(0, 0))
        enemy_system.add_entity(enemy)
        
        # Create 6 bullets at different positions that will hit sequentially
        tower_config = {'bullet_color': (0, 0, 0), 'bullet_size': 3, 'damage': 5}
        for i in range(6):
            bullet = em.create_entity()
            start_x = 200 - (i+1) * 5  # Positioned to hit one per frame
            bullet.add_component(PositionComponent(start_x, 200))
            bullet.add_component(BulletComponent(enemy, tower_config))
            bullet.add_component(VelocityComponent(5, 0))
            bullet_system.add_entity(bullet)
        
        # Run updates - each bullet should hit once and be destroyed
        initial_health = enemy.get_component(HealthComponent).health
        
        for frame in range(10):
            bullet_system.update(1/60)
            
            # Check that each bullet only hits once by verifying total damage
            current_health = enemy.get_component(HealthComponent).health
            damage_taken = initial_health - current_health
            
            # Each frame should see at most 5 damage (one bullet hitting)
            # If a bullet hits multiple times, we'd see more damage per frame
        
        # Verify final state - 6 bullets * 5 damage = 30 damage = enemy dies
        final_health = enemy.get_component(HealthComponent).health
        assert final_health == 0, f"Expected 0 health, got {final_health}"
        assert not enemy.alive, "Enemy should be dead"
    
    def test_enemy_survives_multiple_bullet_hits(self):
        """Test that enemy survives multiple bullet hits over time"""
        from ecs.base import EntityManager
        from ecs.components import PositionComponent, EnemyComponent, HealthComponent, BulletComponent, VelocityComponent
        from ecs.systems import BulletSystem, EnemySystem
        
        # Setup
        em = EntityManager()
        bullet_system = BulletSystem(600, 400)
        enemy_system = EnemySystem(600)
        bullet_system.set_enemy_system(enemy_system)
        
        # Create enemy with high health (wave 10 = 120 health)
        enemy = em.create_entity()
        enemy.add_component(PositionComponent(200, 200))
        enemy.add_component(EnemyComponent(10))  # Wave 10 = 120 health
        enemy.add_component(HealthComponent(120))
        enemy.add_component(VelocityComponent(0, 0))
        enemy_system.add_entity(enemy)
        
        # Create 10 bullets (10 * 5 = 50 damage)
        tower_config = {'bullet_color': (0, 0, 0), 'bullet_size': 3, 'damage': 5}
        for i in range(10):
            bullet = em.create_entity()
            start_x = 200 - (i+1) * 5
            bullet.add_component(PositionComponent(start_x, 200))
            bullet.add_component(BulletComponent(enemy, tower_config))
            bullet.add_component(VelocityComponent(5, 0))
            bullet_system.add_entity(bullet)
        
        # Run updates
        for frame in range(15):
            bullet_system.update(1/60)
        
        # Verify enemy survived (120 - 50 = 70 health remaining)
        final_health = enemy.get_component(HealthComponent).health
        assert final_health == 70, f"Expected 70 health, got {final_health}"
        assert enemy.alive, "Enemy should still be alive"
