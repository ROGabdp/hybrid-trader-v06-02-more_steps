# 臨時檔案：包含完整的 generate_end_date_summary 函數
# 這個函數會被複製到主腳本中

def generate_end_date_summary(bt1, twii_df, start_date, end_date, buy_model, sell_model, 
                               feature_cols, regime_history, sell_threshold, buy_consensus_threshold, kd_threshold):
    """生成回測結束日摘要報告 (end_date_summary_YYYYMMDD_YYYYMMDD.txt)"""
    
    if len(twii_df) == 0:
        return
    
    # 最後一日資料
    last_date = twii_df.index[-1]
    last_row = twii_df.iloc[-1]
    
    # ... (函數內容會很長，讓我分步驟添加)
