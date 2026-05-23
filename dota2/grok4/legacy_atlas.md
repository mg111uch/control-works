# LEGACY CODE ATLAS

Generated from: `/home/manigupt/Hello/python/control/dota2/grok4/dota2_gym`

## 📂 Directory: Root
### 📄 `main.py`
- **Class:** `GameMode`
- **Function:** `create_renderer()`
- **Function:** `main()`

## 📂 Directory: assets
### 📄 `minimap.png (optional static)`

## 📂 Directory: config
### 📄 `constants.json`
- **Config Keys:** `game, fountain, runes, creeps, towers, hero, raze, requiem, buyback, ui`

## 📂 Directory: config/items
### 📄 `band_of_elven_skin.yaml`
- **Config Keys:** `name, internal_name, cost, components, stats, tooltip`

### 📄 `black_king_bar.yaml`
- **Config Keys:** `name, internal_name, cost, components, active, tooltip`

### 📄 `blink_dagger.yaml`
- **Config Keys:** `name, internal_name, cost, components, active, tooltip`

### 📄 `boots_of_speed.yaml`
- **Config Keys:** `name, internal_name, cost, components, stats, tooltip`

### 📄 `bottle.yaml`
- **Config Keys:** `name, internal_name, cost, components, active, tooltip`

### 📄 `clarity.yaml`
- **Config Keys:** `name, internal_name, cost, components, active, tooltip`

### 📄 `enchanted_mango.yaml`
- **Config Keys:** `name, internal_name, cost, components, stats, active, tooltip`

### 📄 `faerie_fire.yaml`
- **Config Keys:** `name, internal_name, cost, components, stats, active, tooltip`

### 📄 `gloves_of_haste.yaml`
- **Config Keys:** `name, internal_name, cost, components, stats, tooltip`

### 📄 `healing_salve.yaml`
- **Config Keys:** `name, internal_name, cost, components, active, tooltip`

### 📄 `magic_wand.yaml`
- **Config Keys:** `name, internal_name, cost, components, stats, active, tooltip`

### 📄 `power_treads.yaml`
- **Config Keys:** `name, internal_name, cost, components, stats, active, tooltip`

### 📄 `shadow_blade.yaml`
- **Config Keys:** `name, internal_name, cost, components, stats, active, tooltip`

### 📄 `tango.yaml`
- **Config Keys:** `name, internal_name, cost, components, active, tooltip`

### 📄 `town_portal_scroll.yaml`
- **Config Keys:** `name, internal_name, cost, components, active, tooltip`

### 📄 `wraith_band.yaml`
- **Config Keys:** `name, internal_name, cost, components, stats, attributes, tooltip, shop_category`

## 📂 Directory: config/heroes
### 📄 `shadow_fiend.yaml`
- **Config Keys:** `name, internal_name, team, base_stats, abilities, passives`

## 📂 Directory: env
### 📄 `dota_gym_env.py`
- **Class:** `DotaGymEnv`
  - Method: `__init__()`
  - Method: `reset()`
  - Method: `step()`
  - Method: `_get_obs()`
  - Method: `_compute_reward()`
  - Method: `render()`
  - Method: `close()`

### 📄 `multiagent_env.py`
- **Class:** `Dota2MultiAgentEnv`
  - Method: `__init__()`
  - Method: `reset()`
  - Method: `step()`
  - Method: `render()`
  - Method: `close()`
  - Method: `_get_obs()`
  - Method: `_get_reward()`
  - Method: `set_controller()`

## 📂 Directory: engine
## 📂 Directory: engine/view
### 📄 `pygame_view.py`
- **Class:** `PygameView`
  - Method: `__init__()`
  - Method: `init()`
  - Method: `handle_events()`
  - Method: `get_surface()`
  - Method: `flip()`
  - Method: `close()`
  - Method: `world_to_screen()`
  - Method: `render()`

### 📄 `renderer_interface.py`
- **Class:** `RendererInterface`
  - Method: `__init__()`
  - Method: `init()`
  - Method: `render()`
  - Method: `handle_events()`
  - Method: `get_surface()`
  - Method: `flip()`
  - Method: `close()`
  - Method: `world_to_screen()`
  - Method: `screen_to_world()`
  - Method: `set_camera()`
  - Method: `draw_circle()`
  - Method: `draw_line()`
  - Method: `draw_text()`
  - Method: `draw_minimap()`
  - Method: `draw_fog_of_war()`
  - Method: `on_game_start()`
  - Method: `on_game_end()`
  - Method: `on_resize()`

## 📂 Directory: engine/model
### 📄 `combat.py`
- **Class:** `CombatSystem`
  - Method: `__init__()`
  - Method: `update()`
  - Method: `_update_hero_attack()`
  - Method: `_launch_attack_projectile()`
  - Method: `_apply_attack_damage()`
  - Method: `_handle_kill()`

### 📄 `game_model.py`
- **Class:** `GameModel`
  - Method: `__init__()`
  - Method: `_load_map_bounds()`
  - Method: `_spawn_heroes()`
  - Method: `_spawn_towers_and_ancient()`
  - Method: `register_controller()`
  - Method: `update()`
  - Method: `get_state_snapshot()`
  - Method: `reset()`

### 📄 `networking.py`
- **Class:** `PacketType`
- **Function:** `serialize_input_packet()`
- **Function:** `deserialize_input_packet()`
- **Function:** `serialize_snapshot()`
- **Function:** `compress_fog_of_war()`
- **Function:** `decompress_fog_of_war()`
- **Function:** `create_join_packet()`
- **Function:** `create_observe_packet()`
- **Function:** `create_ping_packet()`
- **Function:** `parse_packet_header()`
- **Function:** `create_delta_snapshot()`

### 📄 `physics.py`
- **Class:** `PhysicsSystem`
  - Method: `__init__()`
  - Method: `update()`
  - Method: `_integrate_velocities()`
  - Method: `_resolve_unit_collisions()`
  - Method: `_resolve_world_collisions()`
  - Method: `_update_projectiles()`
  - Method: `_apply_friction()`
- **Function:** `generate_passable_grid()`

### 📄 `spatial_hash.py`
- **Class:** `SpatialHash`
  - Method: `__init__()`
  - Method: `_get_cell()`
  - Method: `insert()`
  - Method: `clear()`
  - Method: `query_radius()`
  - Method: `query_rectangle()`

## 📂 Directory: engine/model/projectiles
### 📄 `raze_projectile.py`
- **Class:** `Projectile`
  - Method: `__init__()`
- **Class:** `Damage`
  - Method: `__init__()`
- **Class:** `AreaOfEffect`
  - Method: `__init__()`
- **Class:** `RazeProjectile`
  - Method: `__init__()`
  - Method: `update()`
  - Method: `explode()`

### 📄 `requiem_line.py`
- **Class:** `RequiemLine`
  - Method: `__init__()`
  - Method: `update()`

### 📄 `tower_projectile.py`
- **Class:** `TowerProjectile`
  - Method: `__init__()`
  - Method: `update()`

## 📂 Directory: engine/model/ecs
### 📄 `entity.py`
- **Class:** `Component`
  - Method: `__init__()`
- **Class:** `Entity`
  - Method: `__init__()`
  - Method: `add_component()`
  - Method: `get_component()`
  - Method: `has_component()`
  - Method: `remove_component()`
  - Method: `serialize()`
  - Method: `__repr__()`
- **Class:** `EntityManager`
  - Method: `__init__()`
  - Method: `add()`
  - Method: `remove()`
  - Method: `all()`
  - Method: `of_type()`
  - Method: `find_by_id()`

## 📂 Directory: engine/model/entities
### 📄 `ancient.py`
- **Class:** `AncientHealth`
  - Method: `__init__()`
- **Class:** `Ancient`
  - Method: `__init__()`
  - Method: `serialize()`

### 📄 `creep.py`
- **Class:** `Creep`
  - Method: `__init__()`
  - Method: `update()`

### 📄 `hero.py`
- **Class:** `Position`
  - Method: `__init__()`
- **Class:** `Velocity`
  - Method: `__init__()`
- **Class:** `Facing`
  - Method: `__init__()`
- **Class:** `Health`
  - Method: `__init__()`
- **Class:** `Mana`
  - Method: `__init__()`
- **Class:** `Stats`
  - Method: `__init__()`
- **Class:** `Inventory`
  - Method: `__init__()`
- **Class:** `Souls`
  - Method: `__init__()`
- **Class:** `Hero`
  - Method: `__init__()`
  - Method: `_calc_max_hp()`
  - Method: `_calc_max_mana()`
  - Method: `get_move_speed()`
  - Method: `get_attack_damage()`
  - Method: `get_attack_range()`
  - Method: `cast_raze()`
  - Method: `cast_requiem()`
  - Method: `update_cooldowns()`
  - Method: `serialize()`
  - Method: `get_total_stats()`

### 📄 `tower.py`
- **Class:** `TowerHealth`
  - Method: `__init__()`
- **Class:** `TowerAttack`
  - Method: `__init__()`
- **Class:** `Tower`
  - Method: `__init__()`
  - Method: `serialize()`

## 📂 Directory: engine/model/systems
### 📄 `ability_system.py`
- **Class:** `AbilitySystem`
  - Method: `__init__()`
  - Method: `update()`
  - Method: `cast_shadow_raze()`
  - Method: `cast_requiem_of_souls()`
  - Method: `_update_necromastery()`
  - Method: `handle_ability_input()`

### 📄 `combat_system.py`
- **Class:** `CombatSystem`
  - Method: `__init__()`
  - Method: `update()`
  - Method: `_update_projectiles()`
  - Method: `_handle_hero_auto_attacks()`
  - Method: `_find_attack_target()`
  - Method: `_launch_attack()`
  - Method: `_apply_damage()`
  - Method: `_handle_death()`
  - Method: `register_projectile()`

### 📄 `creep_spawn_system.py`
- **Class:** `CreepSpawnSystem`
  - Method: `__init__()`
  - Method: `update()`
  - Method: `_spawn_wave()`
  - Method: `get_bounty()`

### 📄 `item_system.py`
- **Class:** `Item`
  - Method: `__init__()`
  - Method: `apply_passive()`
  - Method: `remove_passive()`
  - Method: `use_active()`
- **Class:** `ItemSystem`
  - Method: `__init__()`
  - Method: `_load_items_db()`
  - Method: `update()`
  - Method: `buy_item()`
  - Method: `_has_component()`
  - Method: `_remove_component()`
  - Method: `_check_recipes()`

### 📄 `movement_system.py`
- **Class:** `MovementSystem`
  - Method: `__init__()`
  - Method: `update()`

### 📄 `rune_system.py`
- **Class:** `Rune`
  - Method: `__init__()`
  - Method: `serialize()`
- **Class:** `RuneSystem`
  - Method: `__init__()`
  - Method: `update()`
  - Method: `_spawn_power_runes()`
  - Method: `_check_rune_pickups()`
  - Method: `_apply_rune_effect()`
- **Function:** `update_rune_buffs()`

### 📄 `tower_system.py`
- **Class:** `TowerSystem`
  - Method: `__init__()`
  - Method: `update()`
  - Method: `_update_tower_attack()`

### 📄 `vision_system.py`
- **Class:** `VisionSystem`
  - Method: `__init__()`
  - Method: `_precompute_circle_mask()`
  - Method: `update()`
  - Method: `_rasterize_vision_circle()`
  - Method: `get_visible_entities()`
  - Method: `is_position_visible()`

### 📄 `win_condition_system.py`
- **Class:** `WinConditionSystem`
  - Method: `__init__()`
  - Method: `update()`
  - Method: `_trigger_post_game()`
  - Method: `can_buyback()`
  - Method: `perform_buyback()`

## 📂 Directory: engine/controller
### 📄 `ai_controller.py`
- **Class:** `RandomAIController`
  - Method: `__init__()`
  - Method: `find_hero()`
  - Method: `update()`
  - Method: `get_current_input()`

### 📄 `human_controller.py`
- **Class:** `HumanController`
  - Method: `__init__()`
  - Method: `find_hero()`
  - Method: `handle_event()`
  - Method: `screen_to_world()`
  - Method: `update()`

### 📄 `network_controller.py`
- **Class:** `NetworkController`
  - Method: `__init__()`
  - Method: `find_hero()`
  - Method: `apply_input_packet()`
  - Method: `update()`

## 📂 Directory: network
### 📄 `client.py`
- **Class:** `NetworkClient`
  - Method: `__init__()`
  - Method: `_build_input_packet()`
  - Method: `_apply_snapshot()`

### 📄 `observer.py`
- **Class:** `NetworkObserver`
  - Method: `__init__()`

### 📄 `server.py`
