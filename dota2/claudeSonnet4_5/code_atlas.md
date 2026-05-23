# 🗺️ CODEBASE ATLAS
**Generated:** 2026-02-09 17:14:09

**Quick Navigation:** This is Layer 1 (overview). For details, see children/ folder.

---

Legend: │=sep ►=internal ●=external ⚡=entry 🔴=HIGH 🟡=MED 🟢=LOW ⚪=SAFE

## Codebase size
Total files processed: 57
Total lines of code: 8737
Total tokens: 94459
## End Codebase size

Entries: F001,F002,F002:main,F006:run,F037,F037:main,F037:start,F039,F043

HighRisk: F002:main⚪,F006:run⚪,F037:main⚪,F037:start⚪,F010:world_to_screen🔴,F022:get_elevation_at_position🔴,F026:is_point_in_polygon🔴,F026:point_to_segment_distance🔴,F026:generate_stair_polygon🔴,F026:calculate_stair_progress🔴

Children: dota2_gym.md,config.md,items.md,heroes.md,view.md,dota2_view.md,engine.md,ecs.md,model.md,systems_1.md,systems_2.md,controller.md,network.md,tests_1.md,tests_2.md

## Directory Structure 
- **Project path:** `/home/manigupt/Hello/python/dota2/claudeSonnet4_5`
### FILE_MAP Tree
├── children/
│   ├── [] network.md [28 LOC, 224 tokens]
│   ├── [] ecs.md [41 LOC, 336 tokens]
│   ├── [] config.md [8 LOC, 40 tokens]
│   ├── [] systems_2.md [37 LOC, 419 tokens]
│   ├── [] controller.md [17 LOC, 166 tokens]
│   ├── [] view.md [18 LOC, 105 tokens]
│   ├── [] items.md [8 LOC, 39 tokens]
│   ├── [] tests_1.md [172 LOC, 2000 tokens]
│   ├── [] dota2_view.md [106 LOC, 1257 tokens]
│   ├── [] engine.md [19 LOC, 150 tokens]
│   ├── [] heroes.md [8 LOC, 42 tokens]
│   ├── [] systems_1.md [174 LOC, 2821 tokens]
│   ├── [] dota2_gym.md [31 LOC, 366 tokens]
│   ├── [] tests_2.md [126 LOC, 1465 tokens]
│   └── [] model.md [40 LOC, 573 tokens]
├── dota2_gym/
│   ├── config/
│   │   ├── items/
│   │   │   └── [] items.yaml [170 LOC, 1012 tokens]
│   │   ├── heroes/
│   │   │   └── [] shadow_fiend.yaml [69 LOC, 437 tokens]
│   │   ├── [] game_config.yaml [34 LOC, 290 tokens]
│   │   └── [X] map_polygons.txt [56 LOC, 1144 tokens]
│   ├── view/
│   │   ├── dota2_view/
│   │   │   ├── [] ui_inventory.py [274 LOC, 2737 tokens]
│   │   │   ├── [] ui_main.py [185 LOC, 2131 tokens]
│   │   │   ├── [] camera.py [128 LOC, 1275 tokens]
│   │   │   ├── [X] entities_projectiles.py [96 LOC, 782 tokens]
│   │   │   ├── [] draw_game_world.py [97 LOC, 1127 tokens]
│   │   │   ├── [] entities_main.py [236 LOC, 2521 tokens]
│   │   │   ├── [X] dota2_view.py [549 LOC, 5169 tokens]
│   │   │   └── [] menus.py [213 LOC, 2074 tokens]
│   │   └── [] main_menu.py [92 LOC, 693 tokens]
│   ├── engine/
│   │   ├── ecs/
│   │   │   ├── [X] components.py [193 LOC, 1392 tokens]
│   │   │   └── [X] entity_manager.py [90 LOC, 718 tokens]
│   │   ├── model/
│   │   │   └── [X] game_model.py [736 LOC, 6382 tokens]
│   │   ├── systems/
│   │   │   ├── [X] creep_system.py [482 LOC, 4255 tokens]
│   │   │   ├── [] snapshot_system.py [128 LOC, 970 tokens]
│   │   │   ├── [X] stair_geometry.py [523 LOC, 4286 tokens]
│   │   │   ├── [] vision_system.py [62 LOC, 554 tokens]
│   │   │   ├── [X] combat_system.py [273 LOC, 2079 tokens]
│   │   │   ├── [X] spatial_hash.py [66 LOC, 633 tokens]
│   │   │   ├── [] ability_system.py [248 LOC, 2067 tokens]
│   │   │   ├── [X] tower_system.py [236 LOC, 1763 tokens]
│   │   │   ├── [] rune_system.py [77 LOC, 686 tokens]
│   │   │   ├── [] item_system.py [270 LOC, 2068 tokens]
│   │   │   └── [X] movement_system.py [458 LOC, 3955 tokens]
│   │   └── [] config_loader.py [46 LOC, 380 tokens]
│   ├── controller/
│   │   └── [] human_controller.py [353 LOC, 2888 tokens]
│   ├── network/
│   │   ├── [] server.py [273 LOC, 1914 tokens]
│   │   └── [] client.py [72 LOC, 504 tokens]
│   ├── tests/
│   │   ├── [X] test_stair_integration.py [229 LOC, 2057 tokens]
│   │   ├── [] test_networking.py [44 LOC, 334 tokens]
│   │   ├── [] test_combat.py [678 LOC, 6094 tokens]
│   │   ├── [] test_ecs.py [214 LOC, 1530 tokens]
│   │   ├── [X] test_stair_waypoints.py [304 LOC, 2751 tokens]
│   │   ├── [] test_ground_elevation_display.py [167 LOC, 1221 tokens]
│   │   ├── [X] test_movement.py [177 LOC, 1538 tokens]
│   │   ├── [] test_abilities.py [85 LOC, 619 tokens]
│   │   ├── [] test_tower_asset.py [99 LOC, 932 tokens]
│   │   ├── [] test_base_asset.py [78 LOC, 744 tokens]
│   │   ├── [] test_integration.py [82 LOC, 576 tokens]
│   │   ├── [X] test_creeps.py [314 LOC, 3505 tokens]
│   │   ├── [] test_items.py [450 LOC, 3326 tokens]
│   │   ├── [X] test_s3_simple.py [115 LOC, 1233 tokens]
│   │   ├── [] test_hero_portrait.py [118 LOC, 1033 tokens]
│   │   ├── [] test_minimap.py [100 LOC, 920 tokens]
│   │   ├── [] test_config.py [101 LOC, 761 tokens]
│   │   └── [X] test_performance.py [394 LOC, 4075 tokens]
│   ├── [] dota_gym_env.py [245 LOC, 1843 tokens]
│   └── [] main.py [194 LOC, 1365 tokens]
├── [] agent_harness.md [51 LOC, 632 tokens]
├── [X] code_atlas.md [25 LOC, 343 tokens]
├── [] code_dump.txt [4263 LOC, 37893 tokens]
├── [] test_polygon_visual.py [443 LOC, 3879 tokens]
├── [] README.md [242 LOC, 1811 tokens]
├── [] project_tools.md [18 LOC, 716 tokens]
└── [] code_fixes.md [248 LOC, 1095 tokens]
### End Tree
