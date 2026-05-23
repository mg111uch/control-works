#### Architecture – Strict Hierarchical MVC + ECS
### Tree
dota2_gym/
├── README.md
├── main.py                      # Entry point + mode selection
├── config/
│   ├── constants.json
│   ├── heroes/
│   │   └── shadow_fiend.yaml
│   └── items/
│       ├── wraith_band.yaml
│       ├── magic_wand.yaml
│       ├── bottle.yaml
│       ├── shadow_blade.yaml
│       ├── black_king_bar.yaml
│       ├── blink_dagger.yaml
│       ├── tango.yaml
│       ├── faerie_fire.yaml
│       ├── clarity.yaml
│       ├── healing_salve.yaml
│       ├── town_portal_scroll.yaml
│       ├── enchanted_mango.yaml
│       ├── boots_of_speed.yaml
│       ├── gloves_of_haste.yaml
│       ├── band_of_elven_skin.yaml
│       └── power_treads.yaml
├── engine/
│   ├── model/                   # Pure logic – NO pygame/numpy imports here
│   │   ├── ecs/                 # Components + Systems (Neural MMO 2 style)
│   │   │   └── entity.py
│   │   ├── entities/ 
│   │   │   ├── ancient.py 
│   │   │   ├── creeps.py     
│   │   │   ├── tower.py       
│   │   │   └── hero.py
│   │   ├── systems/ 
│   │   │   ├── ability_system.py 
│   │   │   ├── combat_system.py 
│   │   │   ├── creep_spawn_system.py 
│   │   │   ├── item_system.py 
│   │   │   ├── movement_system.py
│   │   │   ├── rune_system.py 
│   │   │   ├── tower_system.py 
│   │   │   ├── vision_system.py            
│   │   │   └── win_condition_system.py
│   │   ├── projectiles/            
│   │   │   ├── raze_projectile.py
│   │   │   ├── tower_projectile.py
│   │   │   └── requiem_line.py
│   │   ├── combat.py
│   │   ├── physics.py
│   │   ├── game_model.py        # Central tick(), entities list, spatial hash
│   │   ├── spatial_hash.py
│   │   └── networking.py        # Lockstep packets
│   ├── view/
│   │   ├── pygame_view.py       # Current renderer
│   │   └── renderer_interface.py
│   └── controller/
│       ├── human_controller.py
│       ├── ai_controller.py
│       └── network_controller.py
├── env/
│   ├── dota_gym_env.py          # Gymnasium + PettingZoo wrapper
│   └── multiagent_env.py
├── network/
│   ├── server.py                # Lockstep authoritative server
│   ├── client.py
│   └── observer.py
└── assets/
    └── minimap.png (optional static)
### End Tree