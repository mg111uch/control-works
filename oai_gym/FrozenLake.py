import numpy as np
import gymnasium as gym
import random
# from gymnasium import envs
# print('\n'.join([str(env) for env in envs.registry]))

env = gym.make('FrozenLake-v1', is_slippery=False, render_mode='human')

action_size=env.action_space.n
state_size=env.observation_space.n
# qtable=np.zeros((state_size,action_size))
qtable = np.array([[0.53,0.59,0.59,0.53],
                    [0.53,0.  ,0.66,0.59],
                    [0.59,0.73,0.59,0.66],
                    [0.66,0.  ,0.59,0.59],
                    [0.59,0.66,0.  ,0.53],
                    [0.  ,0.  ,0.  ,0.  ],
                    [0.  ,0.81,0.  ,0.66],
                    [0.  ,0.  ,0.  ,0.  ],
                    [0.66,0.  ,0.73,0.59],
                    [0.66,0.81,0.81,0.  ],
                    [0.73,0.9 ,0.  ,0.73],
                    [0.  ,0.  ,0.  ,0.  ],
                    [0.  ,0.  ,0.  ,0.  ],
                    [0.  ,0.81,0.9 ,0.73],
                    [0.81,0.9 ,1.  ,0.81],
                    [0.  ,0.  ,0.  ,0.  ]])

# episodes = 10000
goal_steps = 50
# episode_rewards = []

# for episode in range(episodes):
#     state, *_ =env.reset()
#     total_rewards = 0
#     for step in range(goal_steps):
#         action=env.action_space.sample()
#         new_state,reward,done,*_=env.step(action)
#         qtable[state,action]+=0.1*(reward+0.9*np.max(qtable[new_state,:]) -qtable[state,action])
#         state=new_state
#         total_rewards+=reward
#     episode_rewards.append(total_rewards)
# print(np.array2string(qtable, precision=3, separator=','))

env.reset()
for episode in range(1):
    state, *_=env.reset()
    step=0
    done=False
    print("-----------------------")
    print("Episode",episode)
    for step in range(goal_steps):
        env.render()
        action=np.argmax(qtable[state,:])
        print(action)
        new_state,reward,done,*_=env.step(action)
        if done:
            print("Number of Steps",step+1)
            break
        state=new_state
env.close()