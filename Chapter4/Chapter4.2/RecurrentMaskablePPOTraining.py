import time
import numpy as np
from sb3_contrib.common.wrappers import ActionMasker
from stable_baselines3.common.env_checker import check_env
import torch
from Common.InputGenerator import create_input_dataset
from MaskableRecurentPPO.ppo_mask_recurrent import RecurrentMaskablePPO
from ReinforcementLearningEnvironmentOptimized import FlexibleJobShopEnv, mask_fn

# For demonstration, we assume FlexibleJobShopEnv is already defined in the same file.
if __name__ == '__main__':

    # Initialize the FJSP environment.
    # Train on 30 orders
    problemDefinition = create_input_dataset(30)
    env = FlexibleJobShopEnv(problemDefinition)
    env = ActionMasker(env, mask_fn)

    # Optional: Check if the environment follows Gymnasium's interface.
    check_env(env, warn=True)

    if torch.cuda.is_available():
        device = "cuda"
    else:
        device = "cpu"
    print(f"Training on device: {device}")

    import datetime

    run_id = datetime.datetime.now().strftime("%H%M%S")

    steps = 500_000

    policy_kwargs = dict(
        net_arch=[256, 1024, 256],
        activation_fn=torch.nn.Tanh,
        lstm_hidden_size = 4,
        n_lstm_layers=2,
        shared_lstm = True,
        enable_critic_lstm = False,
    )

    model = RecurrentMaskablePPO(
        policy="MultiInputLstmPolicy",
        env=env,
        tensorboard_log=f"./tensorboard_logs/{len(problemDefinition.orders)}/recurrent/{run_id}/{steps}",
        policy_kwargs=policy_kwargs,
        normalize_advantage=True,
        verbose=1,
        learning_rate=1e-3,
        batch_size=256,
        n_steps=2048,
        n_epochs=10
    )

    print(model.policy)
    # Train the model for a set number of timesteps.
    model.learn( total_timesteps=steps )

    # Save the trained model.
    model.save("flexible_job_shop_recurrent_ppo_model_multi_input")

    # Evaluate the trained model.
    obs, _ = env.reset()
    mask = env.action_masks()
    done = False
    total_reward = 0
    lstm_states = None
    # Episode start signals are used to reset the lstm states
    episode_starts = np.ones((1,), dtype=bool)

    start_time = time.time()
    while not done:
        # Let the model predict an action.
        action, lstm_states = model.predict(obs, state=lstm_states, episode_start=episode_starts, deterministic=True,action_masks=mask)
        obs, reward, done, truncated, info = env.step(int(np.asarray(action).item()))
        mask = env.action_masks()
        episode_starts = done
        total_reward += reward

    end_time = time.time()

    print("Episode finished. Total reward:", total_reward)
    print(f"\nTotal simulation time: {end_time - start_time:.2f} seconds")

    # Optionally, visualize the schedule.
    env.env.render(mode='visual')
