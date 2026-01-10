import pandas as pd
import numpy as np
import os

# 設定路徑
PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV = os.path.join(PROJECT_PATH, 'results_hybrid_v5', 'evaluation_kd90_range.csv')

def analyze_confidence():
    if not os.path.exists(INPUT_CSV):
        print(f"Error: {INPUT_CSV} not found.")
        return

    df = pd.read_csv(INPUT_CSV)
    
    # 只分析 Action 為 BUY 的資料
    buy_df = df[df['Action'] == 'BUY'].copy()
    
    if len(buy_df) == 0:
        print("No BUY actions found in the evaluation data.")
        return

    # 定義信心度區間
    bins = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    labels = ['50%-60%', '60%-70%', '70%-80%', '80%-90%', '90%-100%']
    
    buy_df['Confidence_Interval'] = pd.cut(buy_df['Confidence'], bins=bins, labels=labels, include_lowest=True)
    
    # 計算各區間的統計數據
    summary = buy_df.groupby('Confidence_Interval').agg(
        Total_Buy_Days=('Is_Success', 'count'),
        Successful_Buys=('Is_Success', 'sum')
    )
    
    summary['Precision'] = (summary['Successful_Buys'] / summary['Total_Buy_Days'] * 100).round(2)
    
    print("\n" + "=" * 60)
    print("📊 AI BUY Accuracy by Confidence Interval")
    print("=" * 60)
    summary_str = summary.to_string()
    print(summary_str)
    print("-" * 60)
    
    # 計算整體數據作為參考
    total_tp = buy_df['Is_Success'].sum()
    total_precision = (total_tp / len(buy_df) * 100).round(2)
    
    # 保存到檔案
    output_path = os.path.join(PROJECT_PATH, 'results_hybrid_v5', 'confidence_analysis.txt')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("📊 AI BUY Accuracy by Confidence Interval\n")
        f.write("=" * 60 + "\n")
        f.write(summary_str + "\n")
        f.write("-" * 60 + "\n")
        f.write(f"Overall Buy Precision: {total_precision}% (Base for comparison)\n")
    print(f"Results saved to {output_path}")
    print(f"Overall Buy Precision: {total_precision}% (Base for comparison)")

if __name__ == "__main__":
    analyze_confidence()
