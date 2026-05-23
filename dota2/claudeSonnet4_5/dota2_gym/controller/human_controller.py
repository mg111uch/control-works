import pygame

class HumanController:
    """Handles human input for controlling heroes"""
    
    def __init__(self, game_model, view):
        self.game_model = game_model
        self.view = view
        self.selected_hero_id = None
        
        # Select player's hero by default (Radiant)
        if 0 in game_model.player_heroes:
            self.selected_hero_id = game_model.player_heroes[0]
    
    def handle_event(self, event):
        """Handle a pygame event"""
        # Handle camera dragging        
        self.view.handle_mouse_drag(event)
        
        # Handle box selection:
        self.view.handle_box_selection(event)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                # Check if pause menu click
                if self.view.paused:
                    action = self.view.handle_pause_menu_click(event.pos)
                    if action == 'resume':
                        self.view.toggle_pause()
                        return 'resume'
                    elif action == 'quit':
                        return 'quit'
                
                # Check if clicking hero portrait
                if self._click_on_portrait(event.pos):
                    return
                
                # Check if shop is open and clicking on an item
                if self.view.shop_panel.is_open():
                    item_id = self.view.menu_renderer.handle_shop_click(event.pos)
                    if item_id:
                        print(f"[Controller] Purchased {item_id}")
                        return
                
                self._handle_left_click(event.pos)
            
            elif event.button == 3:  # Right click
                if not self.view.paused:
                    self._handle_right_click(event.pos)
        
        elif event.type == pygame.KEYDOWN:
            return self._handle_keypress(event.key)
        
        return None
    
    def _click_on_portrait(self, pos) -> bool:
        """Check if clicking on hero portrait"""
        x, y = pos
        port_x, port_y = 20, self.view.height - 180
        port_size = 140
        
        if port_x <= x <= port_x + port_size and port_y <= y <= port_y + port_size:
            # Select hero
            if 0 in self.game_model.player_heroes:
                self.selected_hero_id = self.game_model.player_heroes[0]
                # Center camera on hero
                em = self.game_model.entity_manager
                position = em.get_component(self.selected_hero_id, 'position')
                if position:
                    self.view.camera_x = position.x - self.view.width / 2
                    self.view.camera_y = position.y - self.view.height / 2
                    self.view.camera_x = max(0, min(self.view.map_width - self.view.width, self.view.camera_x))
                    self.view.camera_y = max(0, min(self.view.map_height - self.view.height, self.view.camera_y))
                return True
        
        return False
    
    def _handle_left_click(self, screen_pos):
        """Handle left click - select hero or attack"""
        # Check if clicking on minimap
        sx, sy = screen_pos
        if self.view.is_in_minimap(sx, sy):
             # Left-click minimap: Center camera (Dota-style)
            world_x, world_y = self.view.minimap_to_world(sx, sy)
            # Center camera
            self.view.camera_x = world_x - self.view.width / 2
            self.view.camera_y = world_y - self.view.height / 2
            self.view.camera_x = max(0, min(self.view.map_width - self.view.width, self.view.camera_x))
            self.view.camera_y = max(0, min(self.view.map_height - self.view.height, self.view.camera_y))
            return
        
        world_x, world_y = self.view.screen_to_world(sx, sy)
        
        # Check if clicked on an entity
        clicked_entity = self._get_entity_at_position(world_x, world_y)
        
        if clicked_entity is not None:
            em = self.game_model.entity_manager
            clicked_hero = em.get_component(clicked_entity, 'hero')
            selected_hero = em.get_component(self.selected_hero_id, 'hero')
            
            # Select if it's a hero
            if clicked_hero:
                # Clear all selections
                for entity_id in em.get_all_entities():
                    selection = em.get_component(entity_id, 'selection')
                    if selection:
                        selection.selected = False
                
                # Select clicked hero
                selection = em.get_component(clicked_entity, 'selection')
                if selection:
                    selection.selected = True
                    self.selected_hero_id = clicked_entity
                    print(f"[Controller] Selected hero {clicked_entity}")
            else:
                # Try to attack if enemy
                if self.selected_hero_id:
                    selected_hero = em.get_component(self.selected_hero_id, 'hero')
                    
                    # Check if enemy
                    enemy_hero = em.get_component(clicked_entity, 'hero')
                    enemy_creep = em.get_component(clicked_entity, 'creep')
                    enemy_tower = em.get_component(clicked_entity, 'tower')
                    
                    is_enemy = False
                    if enemy_hero and enemy_hero.team != selected_hero.team:
                        is_enemy = True
                    elif enemy_creep and enemy_creep.team != selected_hero.team:
                        is_enemy = True
                    elif enemy_tower and enemy_tower.team != selected_hero.team:
                        is_enemy = True
                    
                    if is_enemy:
                        self._order_attack(self.selected_hero_id, clicked_entity)
    
    def _handle_right_click(self, screen_pos):
        """Handle right click - move command or attack"""
        if self.selected_hero_id is None:
            return

        sx, sy = screen_pos
        
        # DOTA2: Right-click on MINIMAP = move command (most important change!)
        if self.view.is_in_minimap(sx, sy):
            return  # Exit - don't process as regular click
        
        world_x, world_y = self.view.screen_to_world(sx, sy)
        
        # Check if clicked on an entity
        clicked_entity = self._get_entity_at_position(world_x, world_y)
        
        if clicked_entity is not None:
            em = self.game_model.entity_manager
            selected_hero = em.get_component(self.selected_hero_id, 'hero')
            
            # Check if enemy
            enemy_hero = em.get_component(clicked_entity, 'hero')
            enemy_creep = em.get_component(clicked_entity, 'creep')
            enemy_tower = em.get_component(clicked_entity, 'tower')
            
            is_enemy = False
            if enemy_hero and enemy_hero.team != selected_hero.team:
                is_enemy = True
            elif enemy_creep and enemy_creep.team != selected_hero.team:
                is_enemy = True
            elif enemy_tower and enemy_tower.team != selected_hero.team:
                is_enemy = True
            
            if is_enemy:
                self._order_attack(self.selected_hero_id, clicked_entity)
                return
        
        # Otherwise, move to position
        self._order_move(self.selected_hero_id, world_x, world_y)
    
    def _handle_keypress(self, key):
        """Handle keyboard input"""

        # Pause (ESC)
        if key == pygame.K_ESCAPE:
            self.view.toggle_pause()
            return None
        
        # If paused, only ESC works
        if self.view.paused:
            return None
        
        # Shop (F2)
        if key == pygame.K_F2:
            self.view.toggle_shop()
            return None
        
        # Courier (F3)
        if key == pygame.K_F3:
            self.view.deliver_courier()
            return None
        
        # Number keys to select heroes
        if key == pygame.K_1:
            if 0 in self.game_model.player_heroes:
                self.selected_hero_id = self.game_model.player_heroes[0]
                em = self.game_model.entity_manager
                selection = em.get_component(self.selected_hero_id, 'selection')
                if selection:
                    selection.selected = True
        
        elif key == pygame.K_2:
            if 1 in self.game_model.player_heroes:
                self.selected_hero_id = self.game_model.player_heroes[1]
                em = self.game_model.entity_manager
                selection = em.get_component(self.selected_hero_id, 'selection')
                if selection:
                    selection.selected = True
        
        # Stop command (SPACE)
        elif key == pygame.K_SPACE:
            if self.selected_hero_id is not None:
                self.game_model.movement_system.stop_movement(self.selected_hero_id)
        
        # Ability keys (Q/W/E/R)
        elif key == pygame.K_q and self.selected_hero_id is not None:
            self._cast_ability('q')
        
        elif key == pygame.K_w and self.selected_hero_id is not None:
            self._cast_ability('w')
        
        elif key == pygame.K_e and self.selected_hero_id is not None:
            self._cast_ability('e')
        
        elif key == pygame.K_r and self.selected_hero_id is not None:
            self._cast_ability('r')
        
        # Item keys (Z/X/C/V/B/N or 3/4/5/6/7/8)
        elif key in [pygame.K_z, pygame.K_3] and self.selected_hero_id is not None:
            self._use_item(0)
        elif key in [pygame.K_x, pygame.K_4] and self.selected_hero_id is not None:
            self._use_item(1)
        elif key in [pygame.K_c, pygame.K_5] and self.selected_hero_id is not None:
            self._use_item(2)
        elif key in [pygame.K_v, pygame.K_6] and self.selected_hero_id is not None:
            self._use_item(3)
        elif key in [pygame.K_b, pygame.K_7] and self.selected_hero_id is not None:
            self._use_item(4)
        elif key in [pygame.K_n, pygame.K_8] and self.selected_hero_id is not None:
            self._use_item(5)
        
        return None
    
    def _cast_ability(self, ability_key: str):
        """Cast an ability"""
        # Check if ability system is available
        if not hasattr(self.game_model, 'ability_system'):
            print("[Controller] Ability system not available")
            return
        
        if ability_key == 'q':
            # Shadowraze near
            self.game_model.ability_system.cast_shadowraze(self.selected_hero_id, 'near')
        elif ability_key == 'w':
            # Shadowraze medium
            self.game_model.ability_system.cast_shadowraze(self.selected_hero_id, 'medium')
        elif ability_key == 'e':
            # Shadowraze far
            self.game_model.ability_system.cast_shadowraze(self.selected_hero_id, 'far')
        elif ability_key == 'r':
            # Requiem
            self.game_model.ability_system.cast_requiem(self.selected_hero_id)
    
    def _use_item(self, slot: int):
        """Use item in slot"""
        if not hasattr(self.game_model, 'item_system'):
            print("[Controller] Item system not available")
            return
        
        self.game_model.item_system.use_item(self.selected_hero_id, slot)
    
    def _order_move(self, hero_id, world_x, world_y):
        """Order hero to move to position"""
        success = self.game_model.movement_system.set_move_target(hero_id, world_x, world_y)
        
        if success:
            # Stop attacking
            em = self.game_model.entity_manager
            combat = em.get_component(hero_id, 'combat')
            if combat:
                combat.attack_target = None
        else:
            print("[Controller] Move failed")
    
    def _order_attack(self, attacker_id, target_id):
        """Order hero to attack target"""
        em = self.game_model.entity_manager
        
        attacker_pos = em.get_component(attacker_id, 'position')
        target_pos = em.get_component(target_id, 'position')
        combat = em.get_component(attacker_id, 'combat')
        
        if not attacker_pos or not target_pos or not combat:
            print("[Controller] Attack failed - missing components")
            return
        
        # Calculate distance
        dx = target_pos.x - attacker_pos.x
        dy = target_pos.y - attacker_pos.y
        distance = (dx*dx + dy*dy) ** 0.5
        
        # Check if in range
        if distance > combat.attack_range:
            # Move into range first
            self._order_move(attacker_id, target_pos.x, target_pos.y)
            combat.attack_target = target_id
        else:
            # Stop moving and attack
            self.game_model.movement_system.stop_movement(attacker_id)
            
            # Create projectile
            proj_id = self.game_model.combat_system.create_attack_projectile(
                attacker_id, target_pos.x, target_pos.y
            )
            
            if proj_id >= 0:
                pass  # Success - don't spam console
            
            combat.attack_target = target_id
    
    def _get_entity_at_position(self, world_x, world_y, radius=50):
        """Get entity at world position (within radius)"""
        em = self.game_model.entity_manager
        entities = em.get_all_entities()
        
        closest_entity = None
        closest_distance = radius
        
        for entity_id in entities:
            position = em.get_component(entity_id, 'position')
            collision = em.get_component(entity_id, 'collision')
            
            if not position:
                continue
            
            # Calculate distance
            dx = position.x - world_x
            dy = position.y - world_y
            distance = (dx*dx + dy*dy) ** 0.5
            
            # Check if within click radius
            entity_radius = collision.radius if collision else 24
            if distance < entity_radius + 10 and distance < closest_distance:
                closest_distance = distance
                closest_entity = entity_id
        
        return closest_entity