import os
import sys
import argparse
import io
import time as time_module

# Force unbuffered output for real-time progress display (skip under pytest)
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
except Exception:
    pass

# Add package root to path for imports
_PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, _PACKAGE_ROOT)

# Parse command line arguments
parser = argparse.ArgumentParser(description='Drift King 2D Training')
parser.add_argument('--headless', type=str, default='True',
                    choices=['True', 'False'],
                    help='Run in headless mode (default: True)')
parser.add_argument('--visualize', action='store_true',
                    help='Visualize the trained model (requires trained model)')
parser.add_argument('--num_envs', type=int, default=4,
                    help='Number of parallel environments for vectorized training')
parser.add_argument('--workers', type=int, default=None,
                    help='Agent-eval worker processes (default: cpu_count-1; 1 = serial)')
parser.add_argument('--generations', type=int, default=300,
                    help='Max generations (overrides default 300)')
parser.add_argument('--train_duration', type=int, default=None,
                    help='Max training seconds, None = run all generations')
parser.add_argument('--seed', type=int, default=42, help='RNG seed')
parser.add_argument('--model-dir', type=str, default=None,
                    help='Dir for .pth files (default: training/models/)')
parser.add_argument('--viz-seconds', type=float, default=None,
                    help='Auto-exit visualization after N seconds (None = until ESC)')
parser.add_argument('--eval-only', action='store_true',
                    help='Deterministic eval of saved model with trajectory CSV (no training)')
parser.add_argument('--eval-episodes', type=int, default=5,
                    help='Episodes for --eval-only')
parser.add_argument('--eval-noise', type=float, default=0.0,
                    help='Random-action prob for --eval-only (0.0 = true policy)')
parser.add_argument('--eval-laps', type=int, default=None,
                    help='Stop each --eval-only episode after N laps (None = full MAX_STEPS)')
parser.add_argument('--traj-out', type=str, default=None,
                    help='Trajectory CSV path (default: <model-dir>/traj_eval.csv)')
parser.add_argument('--track', type=str, default='simple_oval',
                    help='Track name for train/eval/visualize (default: simple_oval)')
parser.add_argument('--tracks', type=str, default=None,
                    help='Comma-separated training pool (default: --track value + infinity_loop + procedural)')
parser.add_argument('--proc-tracks', type=int, default=2,
                    help='Procedural tracks generated into the training pool')
parser.add_argument('--proc-seed', type=int, default=11,
                    help='Base seed for procedural training tracks')
parser.add_argument('--proc-lobes', type=int, choices=[1, 2], default=1,
                    help='Lobes per procedural pool track (1 = single loop)')
parser.add_argument('--fresh', action='store_true',
                    help='Skip lineage seeding (fresh population; needed after obs changes)')
parser.add_argument('--curriculum', action='store_true',
                    help='Start pool on --track only; add proc tracks once best clean laps >= --mastery-laps')
parser.add_argument('--mastery-laps', type=float, default=3.0,
                    help='Clean-lap threshold that expands the curriculum pool')
parser.add_argument('--resume', action='store_true',
                    help='Resume population/counters from models/checkpoint.pt (ignored with --fresh)')
parser.add_argument('--pop-size', type=int, default=35,
                    help='GA population size (min 4; small values for fast smoke runs)')
parser.add_argument('--episodes', type=int, default=10,
                    help='Noisy episodes per env per agent (small values for fast smoke runs)')
args = parser.parse_args()

HEADLESS_MODE = args.headless == 'True'
NUM_ENVS = args.num_envs
GENERATIONS_ARG = args.generations
TRAIN_DURATION = args.train_duration
_TRAINING_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_MODEL_DIR = os.path.join(_TRAINING_DIR, 'models')

def _resolve_model_dir(raw):
    """Single canonical location; abspath so relative flags are cwd-stable."""
    path = os.path.abspath(raw or _DEFAULT_MODEL_DIR)
    os.makedirs(path, exist_ok=True)
    return path

MODEL_DIR = _resolve_model_dir(args.model_dir)
MODEL_PATH = os.path.join(MODEL_DIR, 'drift_policy_model.pth')
BEST_PATH = os.path.join(MODEL_DIR, 'drift_policy_model_best.pth')

_LEGACY_DIRS = [_DEFAULT_MODEL_DIR, _TRAINING_DIR,
                os.path.join(_TRAINING_DIR, 'phase3'), _PACKAGE_ROOT]

def _resolve_checkpoint(primary):
    """Return primary if present else first legacy copy (read-only fallback)."""
    if os.path.exists(primary):
        return primary
    name = os.path.basename(primary)
    for d in _LEGACY_DIRS:
        cand = os.path.join(d, name)
        if cand != primary and os.path.exists(cand):
            print(f"Using legacy checkpoint {cand} (canonical: {primary})", flush=True)
            return cand
    return primary
MAX_STEPS = 4000
N_ACTIONS = 9

def load_track():
    """Load track named by --track (error lists available names)."""
    from controllers.track_loader import TrackLoader
    loader = TrackLoader()
    try:
        return loader.load_track(args.track)
    except Exception:
        print(f"Unknown track '{args.track}'. Available: {loader.list_available_tracks()}")
        raise SystemExit(2)


def _base_names():
    """Handmade pool names from --tracks/--track."""
    raw = args.tracks.split(',') if args.tracks else [args.track]
    return [n.strip() for n in raw if n.strip()]


def _proc_names():
    """Procedural pool names from (proc-seed, proc-tracks)."""
    return [f'proc_{args.proc_seed + i}' for i in range(args.proc_tracks)]


def _ensure_proc_files():
    """Generate missing proc layouts into tracks/ (idempotent)."""
    import json
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import gen_track
    pdir = os.path.join(_PACKAGE_ROOT, 'tracks')
    os.makedirs(pdir, exist_ok=True)
    for name in _proc_names():
        path = os.path.join(pdir, f'{name}.json')
        if not os.path.exists(path):
            data, report = gen_track.generate(int(name.split('_')[1]),
                                              args.proc_lobes)
            with open(path, 'w') as f:
                json.dump(data, f)
            print(f'pool proc track: {path} {report}', flush=True)


def _tracks_by_names(names):
    """Load pool tracks by name (all live in tracks/, loader-visible)."""
    from controllers.track_loader import TrackLoader
    loader = TrackLoader()
    pool = []
    for n in names:
        try:
            pool.append(loader.load_track(n))
        except Exception:
            print(f"Unknown pool track '{n}'. Available: {loader.list_available_tracks()}")
            raise SystemExit(2)
    return pool


def load_pool(include_proc=True):
    """Training track pool: handmade names + procedural layouts on disk.

    Procedural tracks are written under tracks/ (single location, visible
    to TrackLoader) so runs are reproducible from (proc-seed, index).
    Returns list of Track objects.
    """
    names = _base_names()
    if include_proc:
        _ensure_proc_files()
        names = names + _proc_names()
    # NOTE: infinity_loop is excluded from training pools (not single-loop).
    pool = _tracks_by_names(names)
    print(f'training pool: {len(pool)} tracks', flush=True)
    return pool

# Enable Headless Mode (if requested)
if HEADLESS_MODE:
    os.environ["SDL_VIDEODRIVER"] = "dummy"

# Import pygame after setting SDL_VIDEODRIVER
import pygame

# Initialize pygame for event handling
try:
    pygame.init()
    pygame.display.init()
except Exception as e:
    print(f"Warning: Could not initialize pygame display: {e}")
    print("Continuing in headless mode...")
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    pygame.display.init()

import copy
import time
import random
import torch
import torch.nn as nn
import numpy as np

# Import from new structure
from controllers.game_controller import GameEnv

# Ensure reproducibility
seed = args.seed
torch.manual_seed(seed)
pd_api = __import__('random')
pd_api.seed(seed)
np.random.seed(seed)
random.seed(seed)

print("Using Genetic Algorithm (Neuroevolution) for training", flush=True)
print(f"Using {NUM_ENVS} parallel environments", flush=True)


# Define PolicyNet for the drift racing game
class PolicyNet(nn.Module):
    def __init__(self, input_size: int = 15):
        super(PolicyNet, self).__init__()
        # Input: 15 egocentric state features (speed, drift_angle,
        # sin/cos bearing to next checkpoint, dist to it, 10 ray distances)
        # Output: 9 actions (0-8, matches InputController.decode_action)
        self.fc1 = nn.Linear(input_size, 64)
        self.fc2 = nn.Linear(64, 32)
        self.fc3 = nn.Linear(32, 9)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)
        return x


class VectorizedEnv:
    """
    Vectorized environment for faster training.
    Runs multiple environments in parallel (sequentially for now, but structured for future parallelization).
    """
    
    def __init__(self, num_envs: int = 4, headless: bool = True, track=None, tracks=None):
        """
        Initialize vectorized environments.

        Args:
            num_envs: Number of parallel environments
            headless: Whether to run without display
            track: Shared Track object (loads default if None)
            tracks: Per-env pool (round-robin); overrides track when given
        """
        self.num_envs = num_envs
        if tracks:
            self.envs = [GameEnv(headless=headless, track=tracks[i % len(tracks)])
                         for i in range(num_envs)]
        else:
            self.envs = [GameEnv(headless=headless, track=track) for _ in range(num_envs)]
    
    def reset(self, env_idx: int = None):
        """Reset all environments or a specific one."""
        if env_idx is not None:
            return self.envs[env_idx].reset()
        return [env.reset() for env in self.envs]
    
    def step(self, actions: list):
        """
        Take steps in all environments.
        
        Args:
            actions: List of actions, one per environment
            
        Returns:
            List of (state, reward, done) tuples
        """
        results = []
        for i, (env, action) in enumerate(zip(self.envs, actions)):
            state, reward, done = env.step(action)
            if done:
                state = env.reset()
            results.append((state, reward, done))
        return results
    
    def evaluate_batch(self, model, render: bool = False, eval_noise: float = 0.6,
                         num_episodes: int = 10):
        """
        Evaluate a model across all environments.

        Args:
            model: Policy network to evaluate
            render: Whether to render
            eval_noise: Exploration noise probability (0.0-1.0), 0.6 = 60% random actions
            num_episodes: Episodes per environment (use small N for clean selection)

        Returns:
            Tuple of (list of fitness dicts, total_episodes).
            Each dict has laps/steps/deaths/reward/ticks + unique/entropy
            (action diversity of the TRUE policy: noise picks excluded).
        """
        results = []
        total_episodes = 0
        
        for env in self.envs:
            try:
                state = env.reset()
            except Exception as e:
                print(f"Error resetting env: {e}")
                continue
            
            # Run multiple episodes per environment for stable fitness estimates (8-10 episodes)
            episode_count = 0
            max_episodes = num_episodes
            
            # Accumulate stats across episodes
            total_laps = 0
            total_steps = 0
            total_deaths = 0
            total_reward = 0
            total_dist = 0.0
            drift_steps = 0
            total_substeps = 0
            max_ticks = 0
            policy_actions = {}  # action -> count, noise picks excluded
            
            while episode_count < max_episodes:
                done = False
                steps = 0
                laps_in_episode = 0
                episode_deaths = 0
                
                while not done:
                    # Only pump events if not in headless mode
                    if not HEADLESS_MODE:
                        pygame.event.pump()
                    
                    state_tensor = torch.tensor(state, dtype=torch.float32)
                    with torch.no_grad():
                        logits = model(state_tensor)
                        greedy = torch.argmax(logits).item()
                        # Use higher exploration noise (30-50%) during evaluation rollouts
                        # This helps discover driving behaviors early
                        if np.random.random() < eval_noise:  # 60% random exploration
                            action = np.random.randint(0, N_ACTIONS)
                        else:
                            action = greedy
                        policy_actions[greedy] = policy_actions.get(greedy, 0) + 1
                    
                    next_state, reward, done = env.step(action)
                    total_reward += reward
                    total_dist += env.car.speed  # px/step; parkers score 0
                    total_substeps += 1
                    try:
                        from models.game_state import MIN_DRIFT_ANGLE as _MDA
                    except Exception:
                        _MDA = 8.0
                    if env.car.drift_angle >= _MDA and env.car.speed > 0.5:
                        drift_steps += 1
                    steps += 1
                    
                    # Track laps completed in this episode
                    laps_in_episode = env.laps_completed
                    
                    # Check if this step caused off-track death or stagnation kill
                    if done and (env.off_track_death or env.stagnated) and steps < 4000:
                        episode_deaths += 1
                    
                    state = next_state
                    
                    if render:
                        env.render()
                        pygame.time.delay(1)
                    
                    # Limit steps per episode to 3000-5000 (prevent infinite drifting in place)
                    if steps > MAX_STEPS:
                        # Timeout - treat as death
                        episode_deaths += 1
                        done = True
                
                # Episode completed
                episode_count += 1
                total_episodes += 1
                
                # Track stats
                total_laps += laps_in_episode
                total_steps += steps
                total_deaths += episode_deaths
                max_ticks = max(max_ticks, env.ticks)
                
                # Reset for next episode
                state = env.reset()
            
            # Return comprehensive fitness metrics instead of just score
            tot = sum(policy_actions.values()) or 1
            entropy = -sum((c / tot) * np.log(c / tot + 1e-9) for c in policy_actions.values())
            results.append({
                'laps': total_laps / max_episodes,  # Average laps per episode
                'steps': total_steps / max_episodes,  # Average steps survived
                'deaths': total_deaths,  # Total off-track deaths
                'reward': total_reward / max_episodes,
                'ticks': max_ticks,
                'unique': len(policy_actions),
                'entropy': float(entropy),
                'dist': total_dist / max_episodes,  # avg px traveled/episode
                'drift_ratio': drift_steps / (total_substeps or 1),
                'substeps': total_substeps,  # exact env-steps (honest TPS)
            })
        
        return results, total_episodes


def _agg(batch_results):
    """Mean-aggregate one evaluate_batch output across envs."""
    n = len(batch_results) or 1
    return {
        'laps': sum(r['laps'] for r in batch_results) / n,
        'min_laps': min(r['laps'] for r in batch_results) if batch_results else 0.0,
        'steps': sum(r['steps'] for r in batch_results) / n,
        'deaths': sum(r['deaths'] for r in batch_results),
        'reward': sum(r['reward'] for r in batch_results) / n,
        'ticks': max(r['ticks'] for r in batch_results),
        'unique': min(r.get('unique', 1) for r in batch_results),
        'entropy': sum(r.get('entropy', 0.0) for r in batch_results) / n,
        'dist': sum(r.get('dist', 0.0) for r in batch_results) / n,
        'drift_ratio': sum(r.get('drift_ratio', 0.0) for r in batch_results) / n,
        'substeps': sum(r.get('substeps', 0) for r in batch_results),
    }


def _fit_key(f):
    """Rank: worst-track laps, mean laps, shaped reward, coverage, survival, STYLE.
    min_laps first so generalists outrank oval specialists that pad the mean
    on one track and fail the rest. Death forfeit makes reward death-aware
    (fatal drift nets negative), so reward outranks raw death counts —
    otherwise parkers (0 reward, 1 death) beat movers that die trying.
    Drift still only a late tiebreak."""
    return (f.get('min_laps', 0.0), f['laps'], f.get('reward', 0.0),
            f.get('dist', 0.0), f['steps'], -f['deaths'],
            round(f.get('drift_ratio', 0.0), 3),
            min(f.get('unique', 1), 3), f.get('entropy', 0.0))


EARLY_STOP_LAPS = 8  # Phase-2: don't stop before style develops


_WORKER_ENVS = {}

def _worker_init():
    """One torch thread per process avoids oversubscription."""
    import torch as _t
    _t.set_num_threads(1)


def _worker_env(names):
    """Per-pool-signature env cache; rebuilt when curriculum expands."""
    key = tuple(names)
    env = _WORKER_ENVS.get(key)
    if env is None:
        from controllers.track_loader import TrackLoader
        loader = TrackLoader()
        env = VectorizedEnv(num_envs=NUM_ENVS, headless=HEADLESS_MODE,
                            tracks=[loader.load_track(n) for n in key])
        _WORKER_ENVS[key] = env
    return env


def _eval_task(payload):
    """Roll out one agent in the worker's env pool. Deterministic per seed.

    NOTE: per-agent seeds replace the old single global RNG stream — numeric
    trajectories differ from serial runs but stay reproducible for a fixed
    (seed, gen, agent) triple, with independent noise per agent.
    """
    import random as _r
    import numpy as _np
    import torch as _t
    state_dict, seed, eval_noise, num_episodes, pool_names = payload
    _r.seed(seed)
    _np.random.seed(seed % (2 ** 32))
    _t.manual_seed(seed % (2 ** 32))
    agent = PolicyNet()
    agent.load_state_dict(state_dict)
    agent.eval()
    return _worker_env(pool_names).evaluate_batch(
        agent, render=False, eval_noise=eval_noise, num_episodes=num_episodes)


def evaluate(model, env, render=False, eval_noise=0.0):
    """
    Run one episode with the given model and return metrics.
    
    Args:
        model: Policy network
        env: Game environment
        render: Whether to render
        eval_noise: Exploration noise probability (0.0 = deterministic for best model visualization)
    """
    state = env.reset()
    total_reward = 0
    steps = 0
    laps_completed = 0
    done = False
    off_track_deaths = 0
    
    while not done:
        # Pump events to keep the window responsive (if visible)
        pygame.event.pump()
        
        state_tensor = torch.tensor(state, dtype=torch.float32)
        with torch.no_grad():
            logits = model(state_tensor)
            # Use epsilon-greedy for exploration during evaluation
            if np.random.random() < eval_noise:  # Configurable exploration
                action = np.random.randint(0, N_ACTIONS)
            else:
                # Select action with highest logit
                action = torch.argmax(logits).item()
        
        next_state, reward, done = env.step(action)
        total_reward += reward
        steps += 1
        laps_completed = env.laps_completed
        state = next_state
        
        # Render if visualization is enabled
        if render:
            env.render()
            pygame.time.delay(1)  # Small delay for visibility
        
        # Safety break to prevent infinite loops if the model is perfect
        # Limit max steps per episode to 3000-5000
        if steps > MAX_STEPS:
            # Timeout - treat as death (negative reward)
            off_track_deaths += 1
            break
            
    # Return comprehensive metrics: laps, steps, deaths, reward, ticks
    return {
        'laps': laps_completed,
        'steps': steps,
        'deaths': off_track_deaths,
        'reward': total_reward,
        'ticks': env.ticks
    }


def mutate(model, noise_std=0.15):
    """Create a mutant copy of the model by adding Gaussian noise to weights."""
    new_model = copy.deepcopy(model)
    with torch.no_grad():
        for param in new_model.parameters():
            noise = torch.randn_like(param) * noise_std
            param.add_(noise)
    return new_model


def train():
    # Genetic Algorithm Parameters (Improved for Phase 1: Basic Driving)
    POP_SIZE = max(4, args.pop_size)  # floor keeps elitism/selection valid
    GENERATIONS = GENERATIONS_ARG
    MUTATION_RATE = 0.15  # Elevated mutation noise for diversity (uniq stuck at 1-2)
    ELITISM = min(4, max(1, POP_SIZE // 2))  # scale down for smoke pops
    N_SELECT = min(8, POP_SIZE)  # clean re-eval shortlist
    CLEAN_EPS = min(3, args.episodes)  # clean episodes per env
    RANDOM_INJECTION = 0.15  # Reduced to not kill good genes (0.1-0.2)
    EVAL_NOISE = 0.6  # 60% random actions during evaluation (raised for diversity)
    
    # Curriculum pool: oval-only until mastery, then full pool. Workers key
    # envs by pool signature, so expansion propagates without restarts.
    CKPT_PATH = os.path.join(MODEL_DIR, 'checkpoint.pt')
    _expanded = not args.curriculum
    pool_names = _base_names() + (_proc_names() if _expanded else [])
    if _expanded:
        _ensure_proc_files()

    # Use vectorized environments for faster training (one track per env)
    vec_env = VectorizedEnv(num_envs=NUM_ENVS, headless=HEADLESS_MODE,
                            tracks=_tracks_by_names(pool_names))
    print(f'training pool: {pool_names}', flush=True)

    # Initialize population with random weights
    population = [PolicyNet() for _ in range(POP_SIZE)]
    # Lineage: seed from best unless --fresh (obs/arch changes need fresh).
    # Champion kept intact; rest are its mutants + fresh blood for diversity.
    if not args.fresh:
        _seed_src = _resolve_checkpoint(BEST_PATH)
        if os.path.exists(_seed_src):
            try:
                champ = PolicyNet()
                champ.load_state_dict(torch.load(_seed_src, map_location='cpu', weights_only=True))
                champ.eval()
                population[0] = champ
                for i in range(1, POP_SIZE):
                    if random.random() < 0.7:
                        population[i] = mutate(champ, noise_std=MUTATION_RATE * 2)
                print(f"Seeded population from {_seed_src} (champion + mutants)", flush=True)
            except Exception as e:
                print(f"Could not seed from {_seed_src}: {e}; random init", flush=True)

    best_overall_fitness = {'laps': 0, 'steps': 0, 'deaths': float('inf'), 'reward': 0}
    _saved_any = False  # True once a strict-improvement save fires
    total_episode = 0  # Track total episodes across all generations
    total_ticks = 0  # Track total game ticks across all generations
    start_gen = 0
    # Resume: population/counters/curriculum stage from last checkpoint.
    if args.resume and not args.fresh and os.path.exists(CKPT_PATH):
        try:
            ck = torch.load(CKPT_PATH, map_location='cpu', weights_only=True)
            population = []
            for sd in ck['population']:
                agent = PolicyNet()
                agent.load_state_dict(sd)
                population.append(agent)
            best_overall_fitness = ck['best_overall']
            total_episode = ck.get('total_episode', 0)
            total_ticks = ck.get('total_ticks', 0)
            start_gen = ck.get('next_gen', 0)
            if ck.get('expanded'):
                _expanded = True
                _ensure_proc_files()
                pool_names = _base_names() + _proc_names()
                vec_env = VectorizedEnv(
                    num_envs=NUM_ENVS, headless=HEADLESS_MODE,
                    tracks=_tracks_by_names(pool_names))
            print(f"Resumed from {CKPT_PATH} at gen {start_gen + 1} "
                  f"(pool: {pool_names})", flush=True)
        except Exception as e:
            print(f"Could not resume from {CKPT_PATH}: {e}; starting over", flush=True)
    start_time = time_module.time()

    # Agent rollouts are embarrassingly parallel: one process per core, each
    # with its own env pool. Serial fallback for --workers 1 / visual runs.
    _workers = 1
    if HEADLESS_MODE and (args.workers is None or args.workers > 1):
        _workers = args.workers or max(1, (os.cpu_count() or 2) - 1)
    _pool = None
    if _workers > 1:
        import concurrent.futures as _cf
        _pool = _cf.ProcessPoolExecutor(max_workers=_workers,
                                        initializer=_worker_init)
        print(f"Workers: {_workers} processes x {NUM_ENVS} envs", flush=True)
    
    for gen in range(start_gen, GENERATIONS):
        if TRAIN_DURATION is not None and (time_module.time() - start_time) >= TRAIN_DURATION:
            print(f"\nTraining duration limit ({TRAIN_DURATION}s) reached at generation {gen}. Stopping early.", flush=True)
            break
        gen_start_time = time_module.time()
        gen_results = []
        gen_ticks = 0  # Track ticks in this generation
        
        # Evaluate all agents in the population using vectorized environments
        # Noisy rollouts explore; SELECTION uses clean eval (noise=0) below.
        if _pool is not None:
            _base = (args.seed * 1000003 + gen * 1000033) % (2 ** 31)
            _tasks = [(a.state_dict(), _base + i, EVAL_NOISE, args.episodes,
                       tuple(pool_names)) for i, a in enumerate(population)]
            for i, (_batch, _run) in enumerate(_pool.map(_eval_task, _tasks)):
                total_episode += _run
                agg = _agg(_batch)
                gen_ticks += agg['substeps']  # exact env-steps this agent
                gen_results.append({'agent': population[i], 'noisy': agg})

                # Progress line every 5 agents evaluated
                if (i + 1) % 5 == 0:
                    print(f"  [Gen {gen+1}] Evaluated {i+1}/{POP_SIZE} agents...", flush=True)
        else:
            for i, agent in enumerate(population):
                # Evaluate across multiple environments with exploration noise
                batch_results, episodes_run = vec_env.evaluate_batch(agent, render=(not HEADLESS_MODE), eval_noise=EVAL_NOISE, num_episodes=args.episodes)
                total_episode += episodes_run
                agg = _agg(batch_results)
                gen_ticks += agg['substeps']  # exact env-steps this agent
                gen_results.append({'agent': agent, 'noisy': agg})

                # Progress line every 5 agents evaluated
                if (i + 1) % 5 == 0:
                    print(f"  [Gen {gen+1}] Evaluated {i+1}/{POP_SIZE} agents...", flush=True)

        # Clean-eval selection: re-rank top candidates deterministically.
        # Noisy fitness finds candidates; TRUE policy quality decides.
        gen_results.sort(key=lambda x: _fit_key(x['noisy']), reverse=True)
        if _pool is not None:
            _cbase = (args.seed * 2000003 + gen * 2000033) % (2 ** 31)
            _ctasks = [(c['agent'].state_dict(), _cbase + i, 0.0, CLEAN_EPS,
                        tuple(pool_names))
                       for i, c in enumerate(gen_results[:N_SELECT])]
            for cand, (_cbatch, _ceps) in zip(gen_results[:N_SELECT],
                                              _pool.map(_eval_task, _ctasks)):
                total_episode += _ceps
                cand['clean'] = _agg(_cbatch)
        else:
            for cand in gen_results[:N_SELECT]:
                clean_batch, eps = vec_env.evaluate_batch(
                    cand['agent'], render=False, eval_noise=0.0, num_episodes=CLEAN_EPS)
                total_episode += eps
                cand['clean'] = _agg(clean_batch)
        for cand in gen_results[N_SELECT:]:
            cand['clean'] = cand['noisy']  # not re-evaluated; rank by noisy only
        gen_results.sort(key=lambda x: _fit_key(x['clean']), reverse=True)
        
        best_agent_info = gen_results[0]
        current_best_fitness = best_agent_info['clean']
        
        # Calculate generation stats (clean)
        avg_gen_laps = sum(r['clean']['laps'] for r in gen_results) / len(gen_results)
        avg_gen_steps = sum(r['clean']['steps'] for r in gen_results) / len(gen_results)
        avg_gen_deaths = sum(r['clean']['deaths'] for r in gen_results) / len(gen_results)
        gen_duration = time_module.time() - gen_start_time
        total_duration = time_module.time() - start_time
        total_ticks += gen_ticks
        
        # Calculate ticks per second
        tps = gen_ticks / gen_duration if gen_duration > 0 else 0
        avg_tps = total_ticks / total_duration if total_duration > 0 else 0
        
        # Show generation progress with timestamp and summary (clean fitness)
        cb = current_best_fitness
        print(f"[{time_module.strftime('%H:%M:%S')}] "
              f"Gen {gen+1}/{GENERATIONS} | "
              f"Best(clean): laps={cb['laps']:.1f}, minlap={cb.get('min_laps', 0):.1f}, steps={cb['steps']:.0f}, deaths={cb['deaths']}, "
              f"drift={cb.get('drift_ratio', 0):.2f}, "
              f"uniq={cb.get('unique', '?')}, ent={cb.get('entropy', 0):.2f} | "
              f"Avg(clean): laps={avg_gen_laps:.2f}, steps={avg_gen_steps:.0f}, deaths={avg_gen_deaths:.1f} | "
              f"TPS: {tps:.0f} (avg: {avg_tps:.0f}) | "
              f"Time: {gen_duration:.1f}s (total: {total_duration/60:.1f}m)",
              flush=True)
        
        # Save best model if clean fitness improves (diversity breaks ties)
        is_better = _fit_key(current_best_fitness) > _fit_key(best_overall_fitness)
        
        if is_better:
            best_overall_fitness = current_best_fitness.copy()
            torch.save(best_agent_info['agent'].state_dict(), MODEL_PATH)
            # Also save as best copy
            torch.save(best_agent_info['agent'].state_dict(), BEST_PATH)
            _saved_any = True

        # Curriculum: expand to the full pool once oval mastery is shown.
        if (args.curriculum and not _expanded
                and best_overall_fitness.get('laps', 0) >= args.mastery_laps):
            _expanded = True
            _ensure_proc_files()
            pool_names = _base_names() + _proc_names()
            if _pool is None:
                vec_env = VectorizedEnv(
                    num_envs=NUM_ENVS, headless=HEADLESS_MODE,
                    tracks=_tracks_by_names(pool_names))
            print(f"CURRICULUM expanded pool: {pool_names}", flush=True)
        
        # Early stopping: Stop if best agent achieves EARLY_STOP_LAPS+ consistent CLEAN laps
        if best_agent_info['clean']['laps'] >= EARLY_STOP_LAPS:
            print(f"\n*** MILESTONE: Best agent achieved {best_agent_info['clean']['laps']:.1f} clean average laps! Stopping early.", flush=True)
            break
        
        # Milestone checks: Every 20 generations, show clean fitness of top 3
        # (already clean-evaluated every generation; just report)
        if (gen + 1) % 20 == 0:
            print(f"\n--- Milestone Check (Gen {gen+1}): top 3 clean fitness ---", flush=True)
            for rank, candidate in enumerate(gen_results[:3], 1):
                c = candidate['clean']
                print(f"  Rank {rank}: laps={c['laps']:.2f}, steps={c['steps']:.0f}, "
                      f"deaths={c['deaths']}, uniq={c.get('unique', '?')}, ent={c.get('entropy', 0):.2f}", flush=True)
            print("-" * 60, flush=True)
        
        # Create next generation
        new_pop = []
        
        # 1. Elitism: Keep best models unchanged
        for i in range(ELITISM):
            new_pop.append(gen_results[i]['agent'])
        
        # 2. Selection & Mutation
        # Select parents from the top 50% of the population
        survivors = gen_results[:POP_SIZE//2]
        
        while len(new_pop) < POP_SIZE:
            # Reduced chance to create completely new random agent
            if random.random() < RANDOM_INJECTION:
                new_pop.append(PolicyNet())
            else:
                # Pick a random parent from survivors
                parent = random.choice(survivors)['agent']
                # Create a mutated child with small Gaussian noise
                child = mutate(parent, noise_std=MUTATION_RATE)
                new_pop.append(child)
        
        population = new_pop

        # Pause point: full state to resume with --resume (same MODEL_DIR).
        try:
            torch.save({'next_gen': gen + 1,
                        'population': [a.state_dict() for a in population],
                        'best_overall': best_overall_fitness,
                        'total_episode': total_episode,
                        'total_ticks': total_ticks,
                        'expanded': _expanded}, CKPT_PATH)
        except Exception as e:
            print(f"Checkpoint save failed: {e}", flush=True)

    if _pool is not None:
        _pool.shutdown()

    print(f"\nTraining completed!")
    print(f"Best fitness achieved: laps={best_overall_fitness['laps']:.2f}, "
          f"steps={best_overall_fitness['steps']:.0f}, deaths={best_overall_fitness['deaths']}")
    if _saved_any:
        print(f"Model saved to {MODEL_PATH}")
    else:
        print(f"No strict improvement over initial policy — no model saved to {MODEL_PATH}")
    if HEADLESS_MODE:
        print("Run with --visualize to autoplay (no prompt, CI-safe).")


def eval_with_trajectory():
    """Deterministic eval of saved model; writes per-step CSV + crash summary."""
    import csv
    traj_path = args.traj_out or os.path.join(MODEL_DIR, 'traj_eval.csv')
    _model_src = _resolve_checkpoint(MODEL_PATH)
    if not os.path.exists(_model_src):
        print(f"Error: No trained model at {MODEL_PATH}. Run training first.")
        return
    model = PolicyNet()
    model.load_state_dict(torch.load(_model_src, map_location='cpu', weights_only=True))
    model.eval()
    env = GameEnv(headless=True, track=load_track())
    print(f"Eval {args.eval_episodes} eps, noise={args.eval_noise}, model={MODEL_PATH}, track={args.track}", flush=True)
    with open(traj_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['episode', 'step', 'x', 'y', 'angle', 'speed', 'drift_angle',
                    'action', 'reward', 'laps', 'done', 'offtrack_death'])
        for ep in range(args.eval_episodes):
            state = env.reset()
            done, steps = False, 0
            lap_cap = args.eval_laps
            while not done and steps < MAX_STEPS and (lap_cap is None or env.laps_completed < lap_cap):
                state_tensor = torch.tensor(state, dtype=torch.float32)
                with torch.no_grad():
                    logits = model(state_tensor)
                    if np.random.random() < args.eval_noise:
                        action = np.random.randint(0, N_ACTIONS)
                    else:
                        action = torch.argmax(logits).item()
                next_state, reward, done = env.step(action)
                steps += 1
                car = env.car
                w.writerow([ep, steps, f"{car.x:.1f}", f"{car.y:.1f}",
                            f"{car.angle:.1f}", f"{car.speed:.2f}",
                            f"{car.drift_angle:.1f}", action, f"{reward:.2f}",
                            env.laps_completed, int(done), int(env.off_track_death)])
                state = next_state
            print(f"  ep{ep}: laps={env.laps_completed} steps={steps} "
                  f"crash=({env.car.x:.0f},{env.car.y:.0f}) offtrack={env.off_track_death}", flush=True)
    print(f"Trajectory saved to {traj_path}")


def visualize_model():
    """Load and visualize the trained model (single run, no prompts)."""
    print("\nLoading trained model...")
    
    # Check if model exists
    _model_src = _resolve_checkpoint(MODEL_PATH)
    if not os.path.exists(_model_src):
        print(f"Error: No trained model at {MODEL_PATH}. Run training first.")
        return
    
    # Load model
    model = PolicyNet()
    model.load_state_dict(torch.load(_model_src, map_location='cpu', weights_only=True))
    model.eval()
    
    # Create environment with rendering
    env = GameEnv(headless=False, track=load_track())
    print(f"Visualizing on track '{args.track}'. Press ESC or close window to exit.")
    
    viz_deadline = None
    if args.viz_seconds is not None:
        import time as _t
        viz_deadline = _t.time() + args.viz_seconds
    
    running = True
    while running:
        state = env.reset()
        done = False
        
        while not done:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
            
            if not running:
                break

            if viz_deadline is not None:
                import time as _t2
                if _t2.time() >= viz_deadline:
                    running = False
                    break
            
            # Get action from model
            state_tensor = torch.tensor(state, dtype=torch.float32)
            with torch.no_grad():
                logits = model(state_tensor)
                action = torch.argmax(logits).item()
            
            # Take step
            state, reward, done = env.step(action)
            
            # Render full scene (track + car + HUD) via controller
            env.render()
            
            # Small delay for visibility
            pygame.time.delay(16)  # ~60 FPS
        
    pygame.quit()
    print("Visualization ended.")


if __name__ == "__main__":
    if args.eval_only:
        eval_with_trajectory()
    elif args.visualize:
        visualize_model()
    else:
        train()
