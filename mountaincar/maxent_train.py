import gym
import pylab
import numpy as np

from algorithms import maxent

n_states = 400 # position - 20, velocity - 20
n_actions = 3
one_feature = 20 # number of state per one feature

feature_matrix = np.eye((n_states)) # (400, 400)
q_table = np.zeros((n_states, n_actions)) # (400, 3)

gamma = 0.9
q_learning_rate = 0.03
epochs = 10
theta_learning_rate = 0.01

def idx_trajectories(env, one_feature):
    env_low = env.observation_space.low     
    env_high = env.observation_space.high   
    env_distance = (env_high - env_low) / one_feature  

    raw_traj = np.load(file="make_expert/expert_trajectories.npy")
    trajectories = np.zeros((len(raw_traj), len(raw_traj[0]), 3))

    for x in range(len(raw_traj)):
        for y in range(len(raw_traj[0])):
            position_idx = int((raw_traj[x][y][0] - env_low[0]) / env_distance[0])
            velocity_idx = int((raw_traj[x][y][1] - env_low[1]) / env_distance[1])
            state_idx = position_idx + velocity_idx * one_feature

            trajectories[x][y][0] = state_idx
            trajectories[x][y][1] = raw_traj[x][y][2] 
            trajectories[x][y][2] = raw_traj[x][y][3] 
            
    return trajectories

def idx_to_state(env, state):
    env_low = env.observation_space.low
    env_high = env.observation_space.high 
    env_distance = (env_high - env_low) / one_feature 
    position_idx = int((state[0] - env_low[0]) / env_distance[0])
    velocity_idx = int((state[1] - env_low[1]) / env_distance[1])
    state_idx = position_idx + velocity_idx * one_feature
    return state_idx

def update_q_table(state, action, reward, next_state):
    q_1 = q_table[state][action]
    q_2 = reward + gamma * max(q_table[next_state])
    q_table[state][action] += q_learning_rate * (q_2 - q_1)

def find_policy():
    return q_table


def main():
    env = gym.make('MountainCar-v0')
    trajectories = idx_trajectories(env, one_feature)

    episodes, scores = [], []
    
    for episode in range(1000000):
        state = env.reset()
        score = 0

        if episode % 100 == 0 and episode != 0:
            irl_rewards = maxent.maxent_irl(feature_matrix, n_actions, gamma, 
                                                trajectories, epochs, theta_learning_rate)

        while True:
            # env.render()
            state_idx = idx_to_state(env, state)
            action = np.argmax(q_table[state_idx])
            next_state, reward, done, _ = env.step(action)
            
            next_state_idx = idx_to_state(env, next_state)
            if episode > 100:
                irl_reward = irl_rewards[next_state_idx]
                update_q_table(state_idx, action, irl_reward, next_state_idx)
                score += irl_reward
            else:
                update_q_table(state_idx, action, reward, next_state_idx)      
                score += reward
            
            state = next_state
            
            if done:
                scores.append(score)
                episodes.append(episode)
                pylab.plot(episodes, scores, 'b')
                pylab.savefig("./learning_curves/maxent_q_learning.png")
                break

        if episode % 30 == 0:
            print('{} episode | score : {:.1f}'.format(episode, score))
            np.save("maxent_q_table", arr=q_table)

if __name__ == '__main__':
    main()