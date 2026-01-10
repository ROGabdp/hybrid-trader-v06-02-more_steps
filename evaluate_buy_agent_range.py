# -*- coding: utf-8 -*-
"""
================================================================================
Buy Agent Performance Evaluation (Range: 2017-10-16 to 2023-10-15, K < 90)
================================================================================
分析 Buy Agent 在指定日期範圍且 K < 90 時的買入決策準確率。

準確度定義：買入後 120 天內最高價漲幅 >= 10%。
================================================================================
"""

import os
import sys
import pandas as pd
import numpy as np
from stable_baselines3 import PPO

# 加入專案路徑以載入系統模組
PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_PATH)

import ptrl_hybrid_system as hybrid

# =============================================================================
# 設定
# =============================================================================
START_DATE = '2017-10-16'
END_DATE = '2023-10-15'
KD_THRESHOLD = 90
MODEL_PATH = os.path.join(PROJECT_PATH, 'models_hybrid_v5', 'ppo_buy_twii_final.zip')
OUTPUT_CSV = os.path.join(PROJECT_PATH, 'results_hybrid_v5', 'evaluation_kd90_range.csv')

FEATURE_COLS = [
    'Norm_Close', 'Norm_Open', 'Norm_High', 'Norm_Low',
    'Norm_DC_Lower',
    'Norm_HA_Open', 'Norm_HA_High', 'Norm_HA_Low', 'Norm_HA_Close',
    'Norm_SuperTrend_1', 'Norm_SuperTrend_2',
    'Norm_RSI', 'Norm_MFI',
    'Norm_ATR_Change',
    'Norm_RS_Ratio',
    'RS_ROC_5', 'RS_ROC_10', 'RS_ROC_20', 'RS_ROC_60', 'RS_ROC_120',
    'Feat_MA20_Slope',   # 短期趨勢動能
    'Feat_Trend_Gap',    # MA20 vs MA240 市場體制
    'Feat_Bias_MA20',    # 短期乖離
    'Feat_Dist_MA60',    # 季線支撐距離
    'Feat_Dist_MA240',   # 年線生命線位置
    'Feat_Vol_Ratio',    # 相對成交量突波
    'Norm_K',            # Stochastic K(9,3) / 100
    'Norm_D',            # Stochastic D(9,3) / 100
    'Norm_DIF',          # MACD DIF(12,26) / Close
    'Norm_MACD',         # MACD Signal(9) / Close
    'Norm_OSC',          # MACD OSC (DIF - MACD) / Close
]

def main():
    print("=" * 60)
    print(f"Buy Agent Evaluation (Range: {START_DATE} ~ {END_DATE}, K < {KD_THRESHOLD})")
    print("=" * 60)

    # 1. 載入資料
    print("\n[Data] Loading ^TWII data...")
    raw_twii = hybrid._load_local_twii_data(start_date="2000-01-01")
    full_df = hybrid.calculate_features(raw_twii, raw_twii, ticker="^TWII", use_cache=True)
    
    # 計算 Ground Truth (Next 120d Max High >= 10%)
    # 這裡使用 calculate_features 已經算好的 Next_120d_Max
    full_df['Is_Success'] = full_df['Next_120d_Max'] >= 0.10

    # 2. 過濾範圍與條件
    print(f"[Filter] Filtering for {START_DATE} ~ {END_DATE} and K < {KD_THRESHOLD}...")
    mask = (full_df.index >= pd.Timestamp(START_DATE)) & \
           (full_df.index <= pd.Timestamp(END_DATE)) & \
           (full_df['K_raw'] < KD_THRESHOLD)
    
    eval_df = full_df[mask].copy()
    if len(eval_df) == 0:
        print("[Error] No data found for the given criteria.")
        return

    print(f"  - Found {len(eval_df)} days matching criteria.")

    # 3. 載入模型
    print(f"\n[Model] Loading Buy Agent from {MODEL_PATH}...")
    if not os.path.exists(MODEL_PATH):
        print(f"[Error] Model file not found: {MODEL_PATH}")
        return
    model = PPO.load(MODEL_PATH)

    # 4. 執行推論
    print("[Inference] Analyzing daily decisions...")
    results = []
    features_matrix = eval_df[FEATURE_COLS].values.astype(np.float32)
    
    for i in range(len(eval_df)):
        obs = np.nan_to_num(features_matrix[i], nan=0.0, posinf=1.0, neginf=-1.0).reshape(1, -1)
        action, _ = model.predict(obs, deterministic=True)
        
        # 獲取信心度 (Probabilities)
        obs_tensor = model.policy.obs_to_tensor(obs)[0]
        dist = model.policy.get_distribution(obs_tensor).distribution
        probs = dist.probs.detach().cpu().numpy()[0]
        confidence = float(probs[1]) if action[0] == 1 else float(probs[0])
        
        date = eval_df.index[i]
        is_success = eval_df['Is_Success'].iloc[i]
        max_ret_120d = eval_df['Next_120d_Max'].iloc[i]
        k_value = eval_df['K_raw'].iloc[i]
        
        results.append({
            'Date': date.strftime('%Y-%m-%d'),
            'Action': 'BUY' if action[0] == 1 else 'HOLD',
            'Confidence': confidence,
            'K_Value': k_value,
            'Next_120d_Max_Ret': max_ret_120d,
            'Is_Success': is_success
        })

    # 5. 計算指標
    res_df = pd.DataFrame(results)
    
    total_days = len(res_df)
    buy_days = res_df[res_df['Action'] == 'BUY']
    hold_days = res_df[res_df['Action'] == 'HOLD']
    
    tp = len(buy_days[buy_days['Is_Success'] == True])  # True Positive
    fp = len(buy_days[buy_days['Is_Success'] == False]) # False Positive
    tn = len(hold_days[hold_days['Is_Success'] == False])# True Negative
    fn = len(hold_days[hold_days['Is_Success'] == True]) # False Negative
    
    precision = tp / len(buy_days) if len(buy_days) > 0 else 0
    hold_accuracy = tn / len(hold_days) if len(hold_days) > 0 else 0
    overall_accuracy = (tp + tn) / total_days
    base_rate = res_df['Is_Success'].mean()
    
    # 6. 顯示總結
    print("\n" + "=" * 60)
    print("📊 Evaluation Summary")
    print("=" * 60)
    print(f"Total Days Analyzed:      {total_days}")
    print(f"Buy Decisions:            {len(buy_days)} ({len(buy_days)/total_days*100:.1f}%)")
    print(f"Hold Decisions:           {len(hold_days)} ({len(hold_days)/total_days*100:.1f}%)")
    print("-" * 60)
    print(f"Buy Success (Precision):  {precision*100:.2f}% (Market Base Rate: {base_rate*100:.2f}%)")
    print(f"Hold Accuracy:            {hold_accuracy*100:.2f}%")
    print(f"Overall Accuracy:         {overall_accuracy*100:.2f}%")
    print("=" * 60)
    
    # 7. 儲存結果
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    res_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    print(f"\n[Done] Detailed results saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
