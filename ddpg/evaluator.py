import numpy as np
import matplotlib.pyplot as plt
import pickle

from .util import *

class Evaluator(object):

    def __init__(self, env, num_episodes, interval, save_path=''):
        self.num_episodes = num_episodes
        self.interval = interval
        self.save_path = save_path
        self.results = np.array([]).reshape(num_episodes,0)
        self.env = env

    def __call__(self, policy, debug=False, visualize=False, save=True):
        observation = None
        result = []
        env = self.env

        for episode in range(self.num_episodes):

            # reset at the start of episode
            observation = env.reset()
            episode_steps = 0
            episode_reward = 0.
                
            assert observation is not None

            # start episode
            done = False
            while not done:
                # basic operation, action ,reward, blablabla ...
                action = policy(observation)

                observation, reward, done, info = env.step(action)
                
                if visualize:
                    env.render(mode='human')

                # update
                episode_reward += reward
                episode_steps += 1

            if debug: prYellow('[Evaluate] #Episode{}: episode_reward:{}'.format(episode,episode_reward))
            result.append(episode_reward)

        result = np.array(result).reshape(-1,1)
        self.results = np.hstack([self.results, result])

        if save:
            self.save_results('{}/validate_reward'.format(self.save_path))
        return np.mean(result)

    def save_results(self, fn):

        y = np.mean(self.results, axis=0)
        error=np.std(self.results, axis=0)
                    
        x = range(0,self.results.shape[1]*self.interval,self.interval)
        fig, ax = plt.subplots(1, 1, figsize=(6, 5))
        plt.xlabel('Timestep')
        plt.ylabel('Average Reward')
        ax.errorbar(x, y, yerr=error, fmt='-o')
        plt.savefig(fn+'.png')
        pickle.dump({'reward':self.results}, open(fn+'.pkl', 'wb'))
