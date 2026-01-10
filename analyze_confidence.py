
import pandas as pd
import numpy as np

# Load daily actions file (contains buy confidence for every day)
daily_path = r'd:\000-github-repositories\hybrid-trader-v06-02-more_steps\results_backtest_v5_dca_hybrid_dynamic_n_kd_filter\daily_action_strat1_20171016_20231013.csv'
df = pd.read_csv(daily_path)

# Filter for ACTUAL BUY actions (where AI executed a buy)
# Note: 'ai_action' column has 'BUY', 'HOLD', 'SELL', 'FILTERED'
buy_actions = df[df['ai_action'] == 'BUY'].copy()

# 'ai_buy_conf' contains the confidence for the buy side
confidence_scores = buy_actions['ai_buy_conf']

print("-" * 30)
print(f"Total AI Buy Executions: {len(buy_actions)}")
print("-" * 30)
print(f"Min Confidence:  {confidence_scores.min():.4f}")
print(f"25% Quantile:    {confidence_scores.quantile(0.25):.4f}")
print(f"Median (50%):    {confidence_scores.median():.4f}")
print(f"75% Quantile:    {confidence_scores.quantile(0.75):.4f}")
print(f"Max Confidence:  {confidence_scores.max():.4f}")
print(f"Mean Confidence: {confidence_scores.mean():.4f}")
print("-" * 30)

# Binning to see distribution density
bins = [0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.98, 1.0]
labels = ['0.5-0.6', '0.6-0.7', '0.7-0.8', '0.8-0.9', '0.9-0.95', '0.95-0.98', '0.98-1.0']
binned = pd.cut(confidence_scores, bins=bins, labels=labels)
distribution = binned.value_counts().sort_index()

print("Confidence Distribution:")
for label, count in distribution.items():
    pct = count / len(buy_actions) if len(buy_actions) > 0 else 0
    print(f"  {label}: {count} ({pct:.1%})")
