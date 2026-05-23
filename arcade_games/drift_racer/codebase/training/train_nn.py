import os
import sys
import argparse
import io
import time as time_module

# Force unbuffered output for real-time progress display
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

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
args = parser.parse_args()

HEADLESS_MODE = args.headless == 'True'
NUM_ENVS = args.num_envs

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
import pygame

# Import from new structure
from controllers.game_controller import GameEnv

# Ensure reproducibility
seed = 42
torch.manual_seed(seed)
pd_api = __import__('random')
pd_api.seed(seed)
np.random.seed(seed)

print("Using Genetic Algorithm (Neuroevolution) for training", flush=True)
print(f"Using {NUM_ENVS} parallel environments", flush=True)


# Define PolicyNet for the drift racing game
class PolicyNet(nn.Module):
    def __init__(self, input_size: int = 15):
        super(PolicyNet, self).__init__()
        # Input: 15 state features (x, y, angle, speed, drift_angle, 10 ray distances)
        # Output: 7 actions (no action, accelerate, turn left, turn right, drift, accel+left, accel+right)
        self.fc1 = nn.Linear(input_size, 64)
        self.fc2 = nn.Linear(64, 32)
        self.fc3 = nn.Linear(32, 7)

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
    
    def __init__(self, num_envs: int = 4, headless: bool = True):
        """
        Initialize vectorized environments.
        
        Args:
            num_envs: Number of parallel environments
            headless: Whether to run without display
        """
        self.num_envs = num_envs
        self.envs = [GameEnv(headless=headless) for _ in range(num_envs)]
    
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
    
    def evaluate_batch(self, model, render: bool = False, eval_noise: float = 0.4):
        """
        Evaluate a model across all environments.
        
        Args:
            model: Policy network to evaluate
            render: Whether to render
            eval_noise: Exploration noise probability (0.0-1.0), 0.4 = 40% random actions
            
        Returns:
            Tuple of (list of fitness dicts, total_episodes)
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
            max_episodes = 10
            
            # Accumulate stats across episodes
            total_laps = 0
            total_steps = 0
            total_deaths = 0
            total_reward = 0
            max_ticks = 0
            
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
                        # Use higher exploration noise (30-50%) during evaluation rollouts
                        # This helps discover driving behaviors early
                        if np.random.random() < eval_noise:  # 40% random exploration
                            action = np.random.randint(0, 7)
                        else:
                            action = torch.argmax(logits).item()
                    
                    next_state, reward, done = env.step(action)
                    total_reward += reward
                    steps += 1
                    
                    # Track laps completed in this episode
                    laps_in_episode = env.laps_completed
                    
                    # Check if this step caused off-track death
                    if done and env.off_track_death and steps < 4000:
                        episode_deaths += 1
                    
                    state = next_state
                    
                    if render:
                        env.render()
                        pygame.time.delay(1)
                    
                    # Limit steps per episode to 3000-5000 (prevent infinite drifting in place)
                    if steps > 4000:
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
            results.append({
                'laps': total_laps / max_episodes,  # Average laps per episode
                'steps': total_steps / max_episodes,  # Average steps survived
                'deaths': total_deaths,  # Total off-track deaths
                'reward': total_reward / max_episodes,
                'ticks': max_ticks
            })
        
        return results, total_episodes


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
                action = np.random.randint(0, 7)
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
        if steps > 4000:
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


def mutate(model, noise_std=0.1):
    """Create a mutant copy of the model by adding Gaussian noise to weights."""
    new_model = copy.deepcopy(model)
    with torch.no_grad():
        for param in new_model.parameters():
            noise = torch.randn_like(param) * noise_std
            param.add_(noise)
    return new_model


def train():
    # Genetic Algorithm Parameters (Improved for Phase 1: Basic Driving)
    POP_SIZE = 35  # Increased for better diversity (30-40)
    GENERATIONS = 300
    MUTATION_RATE = 0.1  # Standard mutation noise
    ELITISM = 4  # Increased to preserve good drivers (4-5)
    RANDOM_INJECTION = 0.15  # Reduced to not kill good genes (0.1-0.2)
    EVAL_NOISE = 0.4  # 40% random actions during evaluation (30-50%)
    
    # Use vectorized environments for faster training
    vec_env = VectorizedEnv(num_envs=NUM_ENVS, headless=HEADLESS_MODE)
    
    # Initialize population with random weights
    population = [PolicyNet() for _ in range(POP_SIZE)]
    
    best_overall_fitness = {'laps': 0, 'steps': 0, 'deaths': float('inf'), 'reward': 0}
    total_episode = 0  # Track total episodes across all generations
    total_ticks = 0  # Track total game ticks across all generations
    start_time = time_module.time()
    
    for gen in range(GENERATIONS):
        gen_start_time = time_module.time()
        gen_results = []
        gen_ticks = 0  # Track ticks in this generation
        
        # Evaluate all agents in the population using vectorized environments
        for i, agent in enumerate(population):
            # Evaluate across multiple environments with exploration noise
            batch_results, episodes_run = vec_env.evaluate_batch(agent, render=(not HEADLESS_MODE), eval_noise=EVAL_NOISE)
            total_episode += episodes_run
            
            # Aggregate metrics across environments
            avg_laps = sum(r['laps'] for r in batch_results) / len(batch_results)
            avg_steps = sum(r['steps'] for r in batch_results) / len(batch_results)
            total_deaths = sum(r['deaths'] for r in batch_results)
            avg_reward = sum(r['reward'] for r in batch_results) / len(batch_results)
            max_ticks = max(r['ticks'] for r in batch_results)
            
            gen_ticks += max_ticks * 10  # Approximate total ticks for this agent (10 episodes)
            
            gen_results.append({
                'agent': agent,
                'laps': avg_laps,
                'steps': avg_steps,
                'deaths': total_deaths,
                'reward': avg_reward,
                'ticks': max_ticks
            })
            
            # Progress line every 5 agents evaluated
            if (i + 1) % 5 == 0:
                print(f"  [Gen {gen+1}] Evaluated {i+1}/{POP_SIZE} agents...", flush=True)
        
        # Sort by fitness: (laps, steps, -deaths) descending
        # Primary: laps_completed (higher = better)
        # Secondary: total steps survived (longer episodes = better)
        # Tertiary: negative penalty for off-track deaths (fewer deaths = better)
        gen_results.sort(key=lambda x: (x['laps'], x['steps'], -x['deaths']), reverse=True)
        
        best_agent_info = gen_results[0]
        current_best_fitness = {
            'laps': best_agent_info['laps'],
            'steps': best_agent_info['steps'],
            'deaths': best_agent_info['deaths'],
            'reward': best_agent_info['reward']
        }
        
        # Calculate generation stats
        avg_gen_laps = sum(r['laps'] for r in gen_results) / len(gen_results)
        avg_gen_steps = sum(r['steps'] for r in gen_results) / len(gen_results)
        avg_gen_deaths = sum(r['deaths'] for r in gen_results) / len(gen_results)
        gen_duration = time_module.time() - gen_start_time
        total_duration = time_module.time() - start_time
        total_ticks += gen_ticks
        
        # Calculate ticks per second
        tps = gen_ticks / gen_duration if gen_duration > 0 else 0
        avg_tps = total_ticks / total_duration if total_duration > 0 else 0
        
        # Show generation progress with timestamp and summary
        print(f"[{time_module.strftime('%H:%M:%S')}] "
              f"Gen {gen+1}/{GENERATIONS} | "
              f"Best: laps={current_best_fitness['laps']:.1f}, steps={current_best_fitness['steps']:.0f}, deaths={current_best_fitness['deaths']} | "
              f"Avg: laps={avg_gen_laps:.2f}, steps={avg_gen_steps:.0f}, deaths={avg_gen_deaths:.1f} | "
              f"TPS: {tps:.0f} (avg: {avg_tps:.0f}) | "
              f"Time: {gen_duration:.1f}s (total: {total_duration/60:.1f}m)",
              flush=True)
        
        # Save best model if it improves
        # Compare fitness: (laps, steps, -deaths)
        is_better = (
            current_best_fitness['laps'] > best_overall_fitness['laps'] or
            (current_best_fitness['laps'] == best_overall_fitness['laps'] and 
             current_best_fitness['steps'] > best_overall_fitness['steps']) or
            (current_best_fitness['laps'] == best_overall_fitness['laps'] and 
             current_best_fitness['steps'] == best_overall_fitness['steps'] and
             current_best_fitness['deaths'] < best_overall_fitness['deaths'])
        )
        
        if is_better:
            best_overall_fitness = current_best_fitness.copy()
            torch.save(best_agent_info['agent'].state_dict(), 'drift_policy_model.pth')
            # Also save as best copy
            torch.save(best_agent_info['agent'].state_dict(), 'drift_policy_model_best.pth')
        
        # Early stopping: Stop if best agent achieves 5+ consistent laps
        if best_agent_info['laps'] >= 5:
            print(f"\n*** MILESTONE: Best agent achieved {best_agent_info['laps']:.1f} average laps! Stopping early.", flush=True)
            break
        
        # Milestone checks: Every 20 generations, run clean evaluation of top 3
        if (gen + 1) % 20 == 0:
            print(f"\n--- Milestone Check (Gen {gen+1}): Running clean evaluation on top 3 agents ---", flush=True)
            for rank, candidate in enumerate(gen_results[:3], 1):
                # Deterministic evaluation (no noise)
                clean_results, _ = vec_env.evaluate_batch(candidate['agent'], render=False, eval_noise=0.0)
                clean_laps = sum(r['laps'] for r in clean_results) / len(clean_results)
                clean_steps = sum(r['steps'] for r in clean_results) / len(clean_results)
                clean_deaths = sum(r['deaths'] for r in clean_results)
                print(f"  Rank {rank}: laps={clean_laps:.2f}, steps={clean_steps:.0f}, deaths={clean_deaths}", flush=True)
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

    print(f"\nTraining completed!")
    print(f"Best fitness achieved: laps={best_overall_fitness['laps']:.2f}, "
          f"steps={best_overall_fitness['steps']:.0f}, deaths={best_overall_fitness['deaths']}")
    print("Model saved to drift_policy_model.pth")
    
    # Ask if user wants to visualize (only if training was headless)
    if HEADLESS_MODE:
        visualize = input("\nVisualize trained model? (y/n): ")
        if visualize.lower() == 'y':
            visualize_model()


def visualize_model():
    """Load and visualize the trained model."""
    print("\nLoading trained model...")
    
    # Check if model exists
    if not os.path.exists('drift_policy_model.pth'):
        print("Error: No trained model found. Run training first.")
        return
    
    # Load model
    model = PolicyNet()
    model.load_state_dict(torch.load('drift_policy_model.pth'))
    model.eval()
    
    # Create environment with rendering
    env = GameEnv(headless=False)
    
    print("Running autoplay... Press ESC or close window to exit.")
    
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
            
            # Get action from model
            state_tensor = torch.tensor(state, dtype=torch.float32)
            with torch.no_grad():
                logits = model(state_tensor)
                action = torch.argmax(logits).item()
            
            # Take step
            state, reward, done = env.step(action)
            
            # Render
            screen = pygame.display.get_surface()
            screen.fill((128, 128, 128))
            
            # Draw car
            env.car.draw(screen)
            
            # Draw HUD
            from views.hud_renderer import draw_score
            draw_score(env.score, env.game_time, env.laps_completed)
            
            pygame.display.flip()
            
            # Small delay for visibility
            pygame.time.delay(16)  # ~60 FPS
        
        # Check if game ended and user wants to continue
        if running:
            continue_loop = input("Run again? (y/n): ")
            if continue_loop.lower() != 'y':
                running = False
    
    pygame.quit()
    print("Visualization ended.")


if __name__ == "__main__":
    if args.visualize:
        visualize_model()
    else:
        train()
