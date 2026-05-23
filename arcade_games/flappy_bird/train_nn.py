import os

# 1. Enable Headless Mode
# This must be done BEFORE importing pygame (which happens in flappy_bird)
os.environ["SDL_VIDEODRIVER"] = "dummy"

import copy
import time
import torch
import torch.nn as nn
import numpy as np
import random
import pygame
from flappy_bird import GameEnv

# Ensure reproducibility
seed = 42
torch.manual_seed(seed)
np.random.seed(seed)
random.seed(seed)

print("Using Genetic Algorithm (Neuroevolution) for training")

# Define PolicyNet exactly as in flappy_bird.py to ensure compatibility
class PolicyNet(nn.Module):
    def __init__(self):
        super(PolicyNet, self).__init__()
        self.fc1 = nn.Linear(4, 64)
        self.fc2 = nn.Linear(64, 32)
        self.fc3 = nn.Linear(32, 2)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)
        return x

def evaluate(model, env):
    """Run one episode with the given model and return metrics."""
    state = env.reset()
    total_reward = 0
    steps = 0
    done = False
    
    while not done:
        # Pump events to keep the window responsive (if visible)
        pygame.event.pump()
        
        state_tensor = torch.tensor(state, dtype=torch.float32)
        with torch.no_grad():
            logits = model(state_tensor)
            # Action 1 if logits[1] > logits[0] (equivalent to probs[1] > 0.5)
            action = torch.argmax(logits).item()
        
        next_state, reward, done = env.step(action)
        total_reward += reward
        steps += 1
        state = next_state
        
        # Safety break to prevent infinite loops if the model is perfect
        if steps > 5000:
            break
            
    return env.score, total_reward, steps

def mutate(model, noise_std=0.02):
    """Create a mutant copy of the model by adding Gaussian noise to weights."""
    new_model = copy.deepcopy(model)
    with torch.no_grad():
        for param in new_model.parameters():
            noise = torch.randn_like(param) * noise_std
            param.add_(noise)
    return new_model

def train():
    start_time = time.time()
    
    # Genetic Algorithm Parameters
    POP_SIZE = 20
    GENERATIONS = 50  # 20 * 50 = 1000 episodes total
    MUTATION_RATE = 0.02
    ELITISM = 2  # Keep the top 2 unchanged
    
    env = GameEnv()
    
    # Initialize population with random weights
    population = [PolicyNet() for _ in range(POP_SIZE)]
    
    best_overall_score = 0
    
    for gen in range(GENERATIONS):
        gen_results = []
        
        # Evaluate all agents in the population
        for i, agent in enumerate(population):
            score, reward, steps = evaluate(agent, env)
            gen_results.append({
                'agent': agent,
                'score': score,
                'reward': reward,
                'steps': steps
            })
        
        # Sort by Score (primary) and Reward (secondary)
        # Higher is better
        gen_results.sort(key=lambda x: (x['score'], x['reward']), reverse=True)
        
        best_agent_info = gen_results[0]
        current_best_score = best_agent_info['score']
        
        print(f"Gen {gen+1}/{GENERATIONS} | "
              f"Best Score: {current_best_score} | "
              f"Reward: {best_agent_info['reward']:.2f} | "
              f"Steps: {best_agent_info['steps']}")
        
        # Save best model if it improves
        if current_best_score >= best_overall_score:
            best_overall_score = current_best_score
            torch.save(best_agent_info['agent'].state_dict(), 'policy_model.pth')
            # Also save as best copy to avoid overwrite by later generations if they degrade slightly
            torch.save(best_agent_info['agent'].state_dict(), 'policy_model_best.pth')
            
            if best_overall_score >= 100:
                print(f"Target score of 100 reached! Stopping early.")
                break
        
        # Create next generation
        new_pop = []
        
        # 1. Elitism: Keep best models
        for i in range(ELITISM):
            new_pop.append(gen_results[i]['agent'])
            
        # 2. Selection & Mutation
        # Select parents from the top 50% of the population
        survivors = gen_results[:POP_SIZE//2]
        
        while len(new_pop) < POP_SIZE:
            # Pick a random parent from survivors
            parent = random.choice(survivors)['agent']
            # Create a mutated child
            child = mutate(parent, noise_std=MUTATION_RATE)
            new_pop.append(child)
            
        population = new_pop

    print(f"\nTraining completed in {time.time() - start_time:.2f} seconds")
    print(f"Best score achieved: {best_overall_score}")
    print("Model saved to policy_model.pth")

if __name__ == "__main__":
    train()