import numpy as np
import torch


def evaluate(actor_critic, eval_env, env_normalizer, eval_log_dir, device):
    eval_episode_rewards = []
    total_rewards = [0.0] * eval_env.num_envs

    obs = eval_env.reset()
    obs = env_normalizer.normalize_obs(obs)
    eval_recurrent_hidden_states = torch.zeros(
        eval_env.num_envs, actor_critic.recurrent_hidden_state_size, device=device)
    eval_masks = torch.zeros(eval_env.num_envs, 1, device=device)

    while len(eval_episode_rewards) < 10:
        with torch.no_grad():
            obs = torch.as_tensor(obs, dtype = torch.float32, device = device)
            _, action, _, eval_recurrent_hidden_states = actor_critic.act(
                obs,
                eval_recurrent_hidden_states,
                eval_masks,
                deterministic=True)

        action = action.detach().cpu().numpy()
        obs, reward, done, infos = eval_env.step(action)
        obs = env_normalizer.normalize_obs(obs)

        for i in range(eval_env.num_envs):
            total_rewards[i] += reward[i]
            if done[i]:
                eval_episode_rewards.append(total_rewards[i])
                total_rewards[i] = 0

        eval_masks = torch.tensor(
            [[0.0] if done_ else [1.0] for done_ in done],
            dtype=torch.float32,
            device=device)
        eval_env.render()

    print(" Evaluation using {} episodes: mean reward {:.5f}\n".format(
        len(eval_episode_rewards), np.mean(eval_episode_rewards)))
