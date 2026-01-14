import os
import subprocess
import pandas as pd
import glob
from itertools import product

# Parameters to test
activations = [0.10, 0.15, 0.20]
callbacks = [0.05, 0.08, 0.10]
high_profit_thr = 0.25 # Keep constant fer simplicity, or maybe 0.30? Let's stick to 0.25

start_date = "2017-10-16"
end_date = "2023-10-15"
# Get the directory of the current script
base_dir = os.path.dirname(os.path.abspath(__file__))
script_path = os.path.join(base_dir, "backtest_v5_dca_hybrid_dynamic_n_kd_filter_next_tp.py")
results_dir = os.path.join(base_dir, "results_backtest_v5_dca_hybrid_dynamic_n_kd_filter_next_tp")

results = []

print("="*60)
print("🚀 Starting Trailing Profit Sensitivity Analysis")
print("="*60)
print(f"Combinations: {len(activations)} x {len(callbacks)} = {len(activations)*len(callbacks)}")

run_count = 0
for act, cb in product(activations, callbacks):
    run_count += 1
    print(f"\n[{run_count}/{len(activations)*len(callbacks)}] Testing Activation={act:.2f}, Callback={cb:.2f}...")
    
    # Run the backtest script
    cmd = [
        "python", script_path,
        "--start", start_date,
        "--end", end_date,
        "--tp-activation", str(act),
        "--tp-callback-base", str(cb),
        "--tp-callback-high", str(cb + 0.03), # Dynamic high callback = base + 3%? Or fixed? 
        # Plan says: Call 5 -> High 8. So maybe High = Base + 0.03 is a good heuristic.
        # Or better yet, let's just test Base Callback, and set High Callback relative to it.
        # Current logic: Base=0.05, High=0.08. 
        # If Base=0.08, High=0.10? 
        # Let's keep High Callback = Base + 0.03 for now, max 0.12.
        "--tp-high-profit-thr", str(high_profit_thr)
    ]
    
    # Adjust High Callback
    high_cb = min(cb + 0.03, 0.15)
    cmd[cmd.index("--tp-callback-high") + 1] = str(high_cb)
    
    # Run command
    # Use subprocess.run to wait for completion
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) # Suppress output to keep clean
    except subprocess.CalledProcessError as e:
        print(f"Error running backtest: {e}")
        continue
        
    # Parse Result
    # Filename: metrics_comparison_20171016_20231013.csv (Note: date handling might adjust end date to Friday?)
    # The backtest script adjusts end date. 2023-10-15 is Sunday, likely 2023-10-13 (Friday).
    # Let's use glob to find the latest generated metrics file.
    
    # Wait, the script overwrites the same filename for the same date range?
    # Yes, unless we change output dir. But output dir is fixed in script.
    # So we must parse it immediately after run.
    
    # Search for metrics file
    pattern = os.path.join(results_dir, "metrics_comparison_*.csv")
    files = glob.glob(pattern)
    # Get the most recently modified file (in case there are multiple, though unlikely if we clean up)
    if not files:
        print("Error: No metrics file found!")
        continue
        
    latest_file = max(files, key=os.path.getmtime)
    
    try:
        df = pd.read_csv(latest_file)
        # Columns: Metric, Strat1_Split, Strat2_Shared, Pure_DCA, Yearly_Lump
        # We focus on Strat 1
        
        # Transpose or extract
        # Need: Total Return, Sharpe, Max Drawdown
        
        # Metric Names in CSV: Total_Return_Pct, Sharpe_Ratio, Max_Drawdown_Pct
        total_ret = float(df[df['Metric'] == 'Total_Return_Pct']['Strat1_Split'].values[0])
        sharpe = float(df[df['Metric'] == 'Sharpe_Ratio']['Strat1_Split'].values[0])
        max_dd = float(df[df['Metric'] == 'Max_Drawdown_Pct']['Strat1_Split'].values[0])
        
        results.append({
            'Activation': act,
            'Callback_Base': cb,
            'Callback_High': high_cb,
            'Total_Return_Pct': total_ret,
            'Sharpe_Ratio': sharpe,
            'Max_Drawdown_Pct': max_dd
        })
        print(f"  -> Return: {total_ret:.2f}%, Sharpe: {sharpe:.2f}, MaxDD: {max_dd:.2f}%")
        
    except Exception as e:
        print(f"Error parsing results: {e}")

# Save Summary
if results:
    summary_df = pd.read_json(pd.DataFrame(results).to_json()) # Normalize types
    summary_path = os.path.join(base_dir, "sensitivity_analysis_tp_results.csv")
    summary_df.to_csv(summary_path, index=False)
    
    print("\n" + "="*60)
    print("🏆 Sensitivity Analysis Complete")
    print("="*60)
    print(summary_df.sort_values(by='Total_Return_Pct', ascending=False).to_string(index=False))
    print(f"\nSaved to: {summary_path}")
else:
    print("No results collected.")
