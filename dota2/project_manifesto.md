**PROJECT NAME:** dota2_gym  
**GOAL:** Build a complete, modular, high-performance 1v1 Shadow Fiend MOBA training environment in Python that is:
- Human-playable with authentic Dota-style controls
- Fully Gymnasium/PettingZoo compatible for RL
- Renderer-agnostic (Pygame replaceable)
- Supports online multiplayer (lockstep) + observer mode
- Uses heavy NumPy + ECS patterns inspired by Neural MMO 2

### FINAL RESOLVED SPECIFICATION (NO CONFLICTS)

#### Core Performance
- Logic & rendering: 15 ticks/FPS (66.6 ms fixed timestep)
- Headless training mode: unlimited speed (no sleep, no render)
- All entity updates 100% vectorised with NumPy + spatial hash

#### Map & World
- Exact Dota 2 map geometry (all lanes, towers, river, trees as blockers)
- Trees block movement and projectiles
- Fog of War: NumPy grid-based, updated every tick
- Vision: 1800 units circular radius per hero (no high/low ground rules)
- Two power runes (Double Damage + Haste) spawn every 2:00 at random river locations

#### Win Conditions (1v1 Fast Mode)
- Game ends immediately when:
  - First tower falls OR
  - Ancient is destroyed
- Post-game scoreboard

#### Hero – Shadow Fiend (both players)
- Abilities: Q/W/E = three separate Raze stacks (different ranges), R = Requiem of Souls
- Full Necromastery passive (souls → bonus damage + attack range)
- Max level 10, no talents
- Instant facing (no turn rate)
- Projectile-based attacks (900–1200 speed, can be dodged)
- Exact last-hit/deny gold & XP
- Buyback with standard Dota formula

#### Items (EXACT LIST – 16 items only)
1. Wraith Band          2. Magic Wand          3. Bottle             4. Shadow Blade
5. Black King Bar      6. Blink Dagger        7. Tango              8. Faerie Fire
9. Clarity            10. Healing Salve      11. Town Portal Scroll
12. Enchanted Mango   13. Boots of Speed     14. Gloves of Haste   15. Band of Elven Skin
16. Power Treads (with attribute switching)

- All items fully implemented (stats, recipes, actives, tooltips)
- Single base fountain shop only
- No starting items – 600 gold manual purchase

#### Controls & Input
- Classic Dota mouse (right-click move/attack, edge-pan, camera drag)
- Q/W/E/R abilities, 1–6 items, space = stop/hold
- Attack range circle + projectile indicator visible

#### Action Space (RL) – HYBRID
- Continuous: mouse_x, mouse_y (normalized 0–1 over map)
- Discrete: 14 buttons (Q,W,E,R, 1–6 items, Stop, Attack-Move)
→ Total hybrid space (Box(2) + Discrete(14))

#### Observation Space
- Large NumPy vector (~2000–3000 dims) containing all entities within 1800-unit vision radius:
  - Own hero state (pos, vel, facing, HP, mana, level, souls, cooldowns, items, buffs)
  - Enemy hero visible state (same but partial if in FoW)
  - All creeps/towers/projectiles in vision (type, team, pos, HP, etc.)
  - Rune states, own inventory charges, fog-of-war mask (flattened)
  - Game time, gold, K/D/A/CS

#### Networking (Lockstep)
- Server runs the only authoritative GameModel
- Clients send input packet every tick
- Server broadcasts full state snapshot every tick (or delta-compressed)
- Observer clients receive state only (no input)

#### UI (Pure Minimalist)
- Colored shapes only (easy sprite swap later)
- Classic minimap (clickable), top bar, bottom skill/inventory panel
- Health/mana bars above units + portrait
- Home screen + game over screen

#### Deliverables Required from LLM
1. Complete folder structure above
2. Fully working `main.py` that can run:
   - Local 1v1 human vs human
   - Human vs random AI
   - Headless self-play training (10 000+ ticks/sec)
   - Server + 2 clients + 1 observer
3. Complete Gymnasium environment with hybrid space
4. All 16 items + Shadow Fiend fully implemented
5. External YAML/JSON for hero & items (ready for new heroes)
