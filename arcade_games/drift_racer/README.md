# Drift Racer 2D

A racing game with drifting mechanics, refactored into MVC architecture.

## Quick Start

```bash
cd python/control/arcade_games/drift_racer
conda run -n myenv python main.py
```

## Game Commands

### Run Game
```bash
# Default track
python main.py
# Specific track                    
python main.py --track simple_oval       
# List available tracks
python main.py --list-tracks      
```

### Run Training
```bash
# Headless training (default, fast)
python train_nn.py 
# With visualization               
python train_nn.py --headless=False 
# Visualize trained model 
python train_nn.py --visualize
# Use 8 parallel environments    
python train_nn.py --num_envs 8
```

### Run Tests
```bash
# From the parent directory (Hello):
cd /home/manigupt/Hello/python/control/arcade_games/drift_racer/codebase 
conda run -n myenv python -m pytest tests/ -v
```

## Game Controls

| Key | Action |
|-----|--------|
| UP | Accelerate |
| DOWN | Brake |
| LEFT | Turn left |
| RIGHT | Turn right |
| SPACE | Drift |
| R | Restart game |

## Actions (AI Training)

| Code | Action |
|------|--------|
| 0 | No action |
| 1 | Accelerate |
| 2 | Turn left |
| 3 | Turn right |
| 4 | Drift |
| 5 | Accelerate + Turn left |
| 6 | Accelerate + Turn right |
| 7 | Brake |
| 8 | Engine brake |

## AI Training Features

### Observation Space (15 dimensions)
- **Car State (5)**: x, y, angle, speed, drift_angle (all normalized 0-1)
- **Ray Distances (10)**: Distances to track boundaries in 10 directions

### Reward System
The AI agent learns through a shaped reward function:

| Component | Formula | Purpose |
|-----------|---------|---------|
| Forward Progress | `delta_distance × 10.0` | Primary reward - encourages forward movement |
| Living Penalty | `-0.1` per step | Encourages speed and efficiency |
| Drift Reward | `sin(drift_angle) × speed² × 0.5 × combo` | Rewards controlled drifting |
| Lap Bonus | `+750` | Completing a lap |
| Off-Track Penalty | `-1000` + episode end | Discourages leaving the track |

### Combo Multiplier System
- Grows with consecutive drift ticks (max 5x)
- Resets when not drifting or braking
- Multiplies drift reward for sustained drifting

### Drift Detection
- Drift angle = angle between velocity vector and car heading
- Minimum drift angle threshold: 10 degrees
- Real-time calculation during gameplay

### Vectorized Training
- Multiple parallel environments for faster training
- Configurable via `--num_envs` parameter
- Averages results across environments for stable learning

