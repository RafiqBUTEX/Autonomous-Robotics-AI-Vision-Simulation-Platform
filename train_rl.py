import sys
import os
sys.path.insert(0, os.path.expanduser('~/crr_ws/src/car_perception/car_perception'))

from rl_env import GazeboCarEnv
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor

env = GazeboCarEnv()
env = Monitor(env)

model = PPO(
    "MlpPolicy",
    env,
    verbose=1,
    learning_rate=3e-4,
    n_steps=512,
    batch_size=64,
    tensorboard_log=os.path.expanduser("~/crr_ws/rl_logs")
)

TOTAL_TIMESTEPS = 20000

print("Starting training...")
model.learn(total_timesteps=TOTAL_TIMESTEPS)
model.save(os.path.expanduser("~/crr_ws/rl_lidar_avoidance"))
print("Training complete, model saved to ~/crr_ws/rl_lidar_avoidance.zip")

env.close()
