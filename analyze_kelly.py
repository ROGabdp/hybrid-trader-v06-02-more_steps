
import pandas as pd
import numpy as np

# Load the trades file
trades_path = r'd:\000-github-repositories\hybrid-trader-v06-02-more_steps\results_backtest_v5_dca_hybrid_dynamic_n_kd_filter\trades_strat1_20171016_20231013.csv'
df = pd.read_csv(trades_path)

# Filter for AI trades only (Strategy 1 AI)
ai_trades = df[df['type'] == 'AI_S1'].copy()

# Calculate Metrics
total_trades = len(ai_trades)
winning_trades = ai_trades[ai_trades['profit'] > 0]
losing_trades = ai_trades[ai_trades['profit'] <= 0]

win_count = len(winning_trades)
loss_count = len(losing_trades)

win_rate = win_count / total_trades if total_trades > 0 else 0
loss_rate = 1 - win_rate

avg_win = winning_trades['profit'].mean() if win_count > 0 else 0
avg_loss = abs(losing_trades['profit'].mean()) if loss_count > 0 else 0

# Odds (b)
b = avg_win / avg_loss if avg_loss > 0 else 0

# Kelly Percentage (f*)
# f = p - q/b  (where p=win_rate, q=loss_rate, b=odds)
kelly_fraction = win_rate - (loss_rate / b) if b > 0 else 0

print("-" * 30)
print(f"Total AI Trades: {total_trades}")
print(f"Win Rate (p):    {win_rate:.2%}")
print(f"Avg Win:         ${avg_win:,.2f}")
print(f"Avg Loss:        ${avg_loss:,.2f}")
print(f"Profit Factor (b): {b:.2f}")
print("-" * 30)
print(f"Full Kelly (f*): {kelly_fraction:.2%}")
print(f"Half Kelly:      {kelly_fraction/2:.2%}")
print(f"Quarter Kelly:   {kelly_fraction/4:.2%}")
print("-" * 30)

# ROI (Return on Investment) based estimates (using 'return' column)
avg_win_pct = winning_trades['return'].mean()
avg_loss_pct = abs(losing_trades['return'].mean())
b_pct = avg_win_pct / avg_loss_pct if avg_loss_pct > 0 else 0
kelly_fraction_return = win_rate - (loss_rate / b_pct) if b_pct > 0 else 0

print(f"Avg Win %:       {avg_win_pct:.2%}")
print(f"Avg Loss %:      {avg_loss_pct:.2%}")
print(f"Odds (Return):   {b_pct:.2f}")
print(f"Full Kelly (Ret):{kelly_fraction_return:.2%}")
