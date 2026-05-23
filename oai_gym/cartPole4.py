import gymnasium as gym
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import random
from collections import deque
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv
import multiprocessing as mp
import time

# Hyperparameters
GAMMA = 0.99    # Discounts future rewards.
EPSILON_START = 1.0
EPSILON_END = 0.01
EPSILON_DECAY = 0.995   # Gradually reduces exploration.
LEARNING_RATE = 0.001
BATCH_SIZE = 64     # Balances learning stability and speed.
MEMORY_SIZE = 100000
TARGET_UPDATE = 10      # Controls target network refresh rate.
EPISODES = 100
NUM_ENVS = 2          # Uses parallel vectorized environments for fast training
REWARD_THRESHOLD = 25

# Neural Network for Q-function
class DQN(nn.Module):
    def __init__(self, state_size, action_size):
        super(DQN, self).__init__()
        self.fc1 = nn.Linear(state_size, 128)
        self.fc2 = nn.Linear(128, 128)
        self.fc3 = nn.Linear(128, action_size)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        return self.fc3(x)

" The ReplayBuffer stores experiences (state, action, reward, next_state, done) in a deque with a capacity of 100,000, enabling experience replay for stable learning. "
class ReplayBuffer:
    def __init__(self, capacity):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        state, action, reward, next_state, done = zip(*random.sample(self.buffer, batch_size))
        return (np.array(state), action, reward, np.array(next_state), done)

    def __len__(self):
        return len(self.buffer)

# Agent
class DQNAgent:
    '''Sets up Q-network and target network (identical initially) on GPU if available, with an Adam optimizer (learning rate 0.001). The replay buffer and epsilon (for exploration) are initialized.'''
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size
        self.epsilon = EPSILON_START
        self.memory = ReplayBuffer(MEMORY_SIZE)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        self.q_network = DQN(state_size, action_size).to(self.device)
        self.target_network = DQN(state_size, action_size).to(self.device)
        self.target_network.load_state_dict(self.q_network.state_dict())
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=LEARNING_RATE)

    '''Uses epsilon-greedy policy—random action with probability ε, else the action with highest Q-value. Epsilon decays from 1.0 to 0.01.'''
    def select_action(self, states, num_envs, training=True):
        actions = np.zeros(num_envs, dtype=int)
        for i in range(num_envs):
            if training and random.random() < self.epsilon:
                actions[i] = random.randrange(self.action_size)
            else:
                state = torch.FloatTensor(states[i]).to(self.device)
                with torch.no_grad():
                    q_values = self.q_network(state)
                actions[i] = q_values.argmax().item()
        return actions
    
    '''Stores transitions in the replay buffer.'''
    def store_experience(self, states, actions, rewards, next_states, dones):
        for i in range(len(states)):
            self.memory.push(states[i], actions[i], rewards[i], next_states[i], dones[i])

    '''Every 10 episodes, copies Q-network weights to the target network to stabilize training.'''
    def update_epsilon(self):
        self.epsilon = max(EPSILON_END, self.epsilon * EPSILON_DECAY)

    ''' Samples a batch (size 64) from the buffer. Computes Q-values for current states and actions, and target Q-values using the target network (reward + γ * max(next_Q) for non-terminal states, γ = 0.99). Minimizes mean squared error loss to update the Q-network.'''
    def train(self):
        if len(self.memory) < BATCH_SIZE:
            return
        states, actions, rewards, next_states, dones = self.memory.sample(BATCH_SIZE)
        
        states = torch.FloatTensor(states).to(self.device)
        actions = torch.LongTensor(actions).to(self.device)
        rewards = torch.FloatTensor(rewards).to(self.device)
        next_states = torch.FloatTensor(next_states).to(self.device)
        dones = torch.FloatTensor(dones).to(self.device)

        q_values = self.q_network(states).gather(1, actions.unsqueeze(1)).squeeze(1)
        with torch.no_grad():
            next_q_values = self.target_network(next_states).max(1)[0]
            targets = rewards + (1 - dones) * GAMMA * next_q_values

        loss = nn.MSELoss()(q_values, targets)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

    def evaluate(self, env, render=True):
        state, _ = env.reset()
        total_reward = 0
        done = False
        while not done:
            state_tensor = torch.FloatTensor(state).to(self.device)
            with torch.no_grad():
                q_values = self.q_network(state_tensor)
            action = q_values.argmax().item()
            next_state, reward, done, truncated, _ = env.step(action)
            done = done or truncated
            total_reward += reward
            state = next_state
            if render:
                env.render()
                time.sleep(0.02)  # Slow down for visibility
        return total_reward

# Vectorized Environment Setup
def make_env():
    def _init():
        env = gym.make("CartPole-v1")
        env.reset()
        return env
    return _init

# Use DummyVecEnv to avoid IPC issues; switch to SubprocVecEnv after testing
try:
    vec_env = DummyVecEnv([make_env() for _ in range(NUM_ENVS)])
    # vec_env = SubprocVecEnv([make_env() for _ in range(NUM_ENVS)], start_method="spawn")
except Exception as e:
    print(f"Vectorized env failed: {e}")
    raise

state_size = vec_env.observation_space.shape[0]
action_size = vec_env.action_space.n
agent = DQNAgent(state_size, action_size)
episode_rewards = []

# Single environment for rendering
render_env = gym.make("CartPole-v1", render_mode="human")

'''
The training loop runs for 500 episodes. Each episode:

# Resets the environment.
# Selects actions, steps through the environment, and stores experiences.
# Trains the network if enough experiences are available.
# Tracks total rewards and updates epsilon.
# Prints progress every 10 episodes.
'''
# Training Loop
try:
    for episode in range(EPISODES):
        states = vec_env.reset()
        total_rewards = np.zeros(NUM_ENVS)
        done = [False] * NUM_ENVS
        step = 0
        
        while not all(done):
            actions = agent.select_action(states, NUM_ENVS, training=True)
            next_states, rewards, dones, infos = vec_env.step(actions)
            
            agent.store_experience(states, actions, rewards, next_states, dones)
            agent.train()
            
            states = next_states
            total_rewards += rewards
            done = dones
            step += 1
            
            for i in range(NUM_ENVS):
                if dones[i]:
                    episode_rewards.append(total_rewards[i])
                    total_rewards[i] = 0
        
        agent.update_epsilon()
        
        if episode % TARGET_UPDATE == 0:
            agent.target_network.load_state_dict(agent.q_network.state_dict())
        
        if episode % 10 == 0:
            avg_reward = np.mean(episode_rewards[-NUM_ENVS * 10:] if episode_rewards else [0])
            print(f"Episode {episode}, Avg Reward: {avg_reward:.2f}, Epsilon: {agent.epsilon:.3f}")
            
            # Check if reward threshold is met
            if avg_reward > REWARD_THRESHOLD and episode_rewards:
                print(f"Reward > {REWARD_THRESHOLD}, evaluating policy with rendering...")
                eval_reward = agent.evaluate(render_env, render=True)
                print(f"Evaluation Reward: {eval_reward:.2f}")
                render_env.close()
                break  # Optionally stop training

except Exception as e:
    print(f"Training failed: {e}")
finally:
    vec_env.close()
    render_env.close()

# Print average reward of last 100 episodes
print(f"Average reward (last 100): {np.mean(episode_rewards[-100:]):.2f}")