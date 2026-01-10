import sys
import os
from stable_baselines3 import PPO

sys.path.insert(0, os.getcwd())
# Force UTF-8 stdout
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

buy_path = r"models_hybrid_v5/best_tuned/buy/best_model.zip"
sell_path = r"models_hybrid_v5/best_tuned/sell/best_model.zip"

def get_steps(path, name):
    if os.path.exists(path):
        try:
            model = PPO.load(path, device="cpu")
            print(f"{name}: {model.num_timesteps}")
        except Exception as e:
            print(f"{name}: ERROR {e}")
    else:
        print(f"{name}: NOT_FOUND")

get_steps(buy_path, "BUY_STEPS")
get_steps(sell_path, "SELL_STEPS")
