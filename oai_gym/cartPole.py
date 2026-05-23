import gymnasium as gym
import numpy as np
import time
import random
from statistics import median, mean
from collections import Counter

'''
m,M,g,L = 1,10,10,1
# state matrix
a = g/(L*(4.0/3 - m/(m+M)))
A = np.array([[0, 1, 0, 0],
              [0, 0, a, 0],
              [0, 0, 0, 1],
              [0, 0, a, 0]])

# input matrix
b = -1/(L*(4.0/3 - m/(m+M)))
B = np.array([[0], [1/(m+M)], [0], [b]])

R = np.eye(1, dtype=int)          # choose R (weight for input)
Q = 5*np.eye(4, dtype=int)        # choose Q (weight for state)

from scipy import linalg
# solve ricatti equation
P = linalg.solve_continuous_are(A, B, Q, R)

K = np.dot(np.linalg.inv(R),
           np.dot(B.T, P))

K = np.array([[ -2.23606798, -4.46455999, -39.90999994, -10.68299034]])          

def apply_state_controller(K, x):
    u = -np.dot(K, x)   # u = -Kx    
    if u[0] > 0:
        return 1, u     # if force_dem > 0 -> move cart right
    else:
        return 0, u     # if force_dem <= 0 -> move cart left
'''	
env = gym.make('CartPole-v1',render_mode='human')

episodes = 20
goal_steps = 100
score_requirement = 30

def initial_population():
    training_data = []
    scores = []
    accepted_scores = []
    for episode in range(episodes):
        score = 0

        obs = env.reset()
        # state = obs[0]
        # state = np.array([ -2.23606798, -4.46455999, -39.90999994, -10.68299034])
        game_memory = []
        prev_observation = []

        for step in range(goal_steps):
            # env.render()

            # action, force = apply_state_controller(K, state)
            # abs_force = abs(float(np.clip(force[0], -10, 10)))    
            # env.env.force_mag = abs_force

            action = random.randrange(0,2) # env.action_space.sample()

            state, reward, terminated, truncated, info = env.step(action)
            if len(prev_observation) > 0 :
                game_memory.append([prev_observation, action])
            prev_observation = state
            score += reward
            if terminated or truncated:
                # print(f'Terminated after {i+1} iterations.')
                break
            
        if score >= score_requirement:
            print('Episode:', episode, 'Score:', score)
            accepted_scores.append(score)
            for data in game_memory:
                # convert to one-hot (this is the output layer for our neural network)
                if data[1] == 1:
                    output = [0,1]
                elif data[1] == 0:
                    output = [1,0]
                    
                # saving our training data
                training_data.append([data[0], output])

    # just in case you wanted to reference later
    # training_data_save = np.array(training_data)
    # np.save('saved.npy',training_data_save)
    
    # some stats here, to further illustrate the neural network magic!
    # if len(accepted_scores) > 0:
    #     print('Average accepted score:',mean(accepted_scores))
    #     print('Median score for accepted scores:',median(accepted_scores))
    #     print(Counter(accepted_scores))
    
    # return training_data
    print('Training data: ',training_data[0])

initial_population()