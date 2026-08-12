import sys
import os
sys.path.insert(0, os.path.expanduser('~/crr_ws/src/car_perception/car_perception'))

from rl_env import GazeboCarEnv
from stable_baselines3 import PPO

env = GazeboCarEnv()
model = PPO.load(os.path.expanduser("~/crr_ws/rl_lidar_avoidance"))

obs, _ = env.reset()
print("Running trained policy... Ctrl+C to stop")

try:
    while True:
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, _ = env.step(action)
        if terminated or truncated:
            print(f"Episode ended (reward={reward:.2f}), resetting...")
            obs, _ = env.reset()
except KeyboardInterrupt:
    pass
finally:
    env.close()
