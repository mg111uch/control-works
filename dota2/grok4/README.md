# dota2_gym – Minimalist 1v1 Shadow Fiend MOBA + RL Environment

A fast, modular, Gymnasium-compatible 1v1 Dota 2 training environment built from the ground up with:

- Exact map layout & creep waves
- Full Shadow Fiend (3× Raze + Requiem + Necromastery)
- 16 real items with actives
- Hybrid action space (continuous mouse + discrete keys)
- Lockstep online multiplayer + observer mode
- Renderer-agnostic MVC + Neural MMO 2 style ECS
- 15 FPS human play – unlimited speed headless training

## Activate Conda environment
```command
cd python/control/dota2/grok4/dota2_gym && eval "$(conda shell.bash hook)" && conda activate myenv
```

## Quick Start

```bash
pip install -r requirements.txt

# Local 1v1 (human vs human)
python main.py --mode local

# Human vs random AI
python main.py --mode ai

# Headless self-play (for RL training)
python main.py --mode headless --episodes 1000

# Headless training (fastest)
python main.py --mode headless --episodes 10000

# Start server
python network/server.py

# Connect clients
python main.py --mode client --host 127.0.0.1

# Observer
python main.py --mode observer --host 127.0.0.1

# Online client (no window)
python main.py --mode client --render none

# Record video (rgb_array → save frames)
python main.py --mode ai --render rgb_array
```

## RL Usage
```python
from env.dota_gym_env import DotaGymEnv
env = DotaGymEnv()
obs, info = env.reset()
action = env.action_space.sample()   # {'mouse': [0.5, 0.5], 'buttons': 2}
obs, reward, done, truncated, info = env.step(action)
```
## To upgrade later:
Replace this file with a trained policy (e.g., PPO from Stable-Baselines3) that calls:
```python
self.current_input = agent.predict(obs)
```
Drop this file into engine/controller/ai_controller.py
Now python main.py --mode ai gives you a fully playable human vs random AI match.

## Network Controller Use
### How to use it (server side):
```python

# In network/server.py or your lockstep server
controller = NetworkController(model, player_id=0)
model.register_controller(0, controller)

# When receiving packet:
packet = json.loads(data)
controller.apply_input_packet(packet, current_server_tick)
```
### Client-side packet example (sent every frame or on change):
```json
{
  "tick": 1540,
  "move": [8200.5, 7100.0],
  "attack_move": false,
  "raze": "medium",
  "requiem": false,
  "item": null,
  "stop": false
}
```
This controller completes the full online multiplayer stack:
- Lockstep deterministic
- Zero prediction needed
- Works with observer mode
- Ready for tournaments or cloud training

## Multiagent environment
**Train with any MARL framework**
```python
from stable_baselines3 import PPO
env = Dota2MultiAgentEnv()
model = PPO("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=1_000_000)
```

## Requirements
```txt
pygame>=2.5.0
numpy>=1.24.0
pyyaml>=6.0
gymnasium>=0.29.0
pettingzoo>=1.24.0
websockets>=12.0