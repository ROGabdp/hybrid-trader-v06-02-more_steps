# v06-02-more_steps 重點

1. 以v06-02為基礎，增加訓練步數至10M steps。
2. 增加回測腳本，置入kd filter，預設 KD<90 AI才能買入，可得到最佳的 Calmar Ratio (報酬/回撤比)，KD 90 的數值 (0.406) 是所有測試中最優的

先前的腳本

    * 盤後
    python backtest_v5_dca_hybrid_dynamic_n.py --start 2025-12-09
    python daily_ops_v5_dynamic_n.py   
    * 盤中
    python daily_ops_v5_intraday_dynamic_n.py -i

有KD濾網的腳本

    * 盤後
    python backtest_v5_dca_hybrid_dynamic_n_kd_filter.py --start 2025-12-09
    python daily_ops_v5_dynamic_n_kd_filter.py   
    * 盤中
    python daily_ops_v5_intraday_dynamic_n_kd_filter.py -i


3. 增加strat 3策略:

    1. 資金注入與首次買入 (Yearly Capital Injection)
        資金來源：每年年初 (1月) 注入固定的年度資金 (例如 60 萬元)。
        買入行為 (Lump Sum)：資金注入當下，立即全額買入股票，建立初始倉位。這是為了模擬一般的定期定值投資人行為。
    2. 賣出機制 (AI Managed Exit)
        所有持倉 (包含年初買入的倉位和後續買回的倉位) 都受 AI Sell Agent 監控：

        賣出條件：
           AI 訊號：Sell Agent 預測 "SELL" 且信心度 > sell_threshold (預設 0.6)。
           停損 (Stop Loss)：如果持倉報酬率 < -8% (即槓桿後下跌 8%)，強制停損賣出。
        否決機制 (Consensus)：如果 AI 想賣，但 Buy Agent 同時發出強烈買入訊號 (信心 > 0.5)，則 暫緩賣出 (Hold)。
        資金去向：賣出後的資金會全數回到 yearly_pool (年度資金池)，等待再買入機會。
    3. 再買回機制 (AI Managed Re-entry)
        當資金池有閒置資金 (來自這一年賣出的股票) 時，由 AI Buy Agent 決定何時進場：

        資金分配 (Chunked Re-entry)：
        為了平滑風險，不一次買滿。
        計算方式：每筆投入金額 = 目前池中總資金 / 當年度剩餘月數。
        (這就是您先前要求改回的 "分批買回" 邏輯)。
    買入條件：
        AI 訊號：Buy Agent 預測 "BUY"。
        動態濾網 (Dynamic Filter)：確認目前不是熊市，或者有突破 Donchian 通道。
        KD 濾網：KD 值 < kd_threshold (預設 90)。
    執行：條件滿足時，買入一筆計算出的金額。
    4. 2x 槓桿機制 (Leverage Protection)
        觸發：當股價從歷史高點回落超過 8% 時，自動啟動 2x 槓桿模式。
        效果：所有持倉的報酬率波動變為 2 倍 (模擬融資或槓桿ETF效果)，目的是在超跌反彈時加速獲利。
        結束：當股價漲回觸發點時，槓桿模式結束。



# hybrid-trader-v06-02 是以 hybrid-trader-v06 作為基礎來修改的

# v06-02 重點

1. 改變訓練集和驗證集的切分時間點。

    訓練集使用以下日期期間 
    --start 2000-01-01 --end 2017-10-15
    --start 2023-10-16 --end 2025-12-31

    驗證集使用以下日期期間
    --start 2017-10-16 --end 2023-10-15

2. 將buy agent 在驗證集期間的類別平衡取消，以得到真正可以在不同市場存活的最佳模型

    📊 Agent 訓練參數總表 (train_v5_models.py) 於v06已經調整好，因此不需要修改
    階段	Agent	1. 評估回數 (n_eval_episodes)	2. 熵係數 (ent_coef)	3. 學習率 (learning_rate)	程式碼行數
    Pre-training	Buy Agent	50	0.01	0.0001 (1e-4)	L175 / L150 / L147
    Pre-training	Sell Agent	50	0.01	0.0001 (1e-4)	L210 / L150 / L147
    Fine-tuning	Buy Agent	100	0.01	0.000005 (5e-6)	L336 / L299 / L296
    Fine-tuning	Sell Agent	100	0.01	0.000005 (5e-6)	L384 / L299 / L296

    這次的訓練是成功的。
    1. 驗證了 Gap Validation：Agent 在沒有看過的市場片段 (2017-2023) 中表現穩健，沒有過擬合。
    2. 證實了 Remove Class Balancing：讓 Agent 直接面對真實數據分佈是正確的，它學會了「寧可錯過平庸機會，只抓極端好機會」的生存策略。

3. 調整協作參數，在保持抗跌能力的同時，改善牛市表現以超越 "Buy and Hold" 策略。

    最佳參數組合
    建議將策略參數調整為：
    1. Sell Threshold: 0.6 (原 0.5) —— 提高賣出難度，避免過早離場。
    2. Buy Consensus Threshold: 0.5 (原 0.8) —— 增強 Buy Agent 的話語權，充當趨勢濾網。
    
    策略特性總結:
    1. 抗跌是核心優勢: 本策略最大價值在於避開如 2020 疫情與 2022 熊市的深幅下跌。
    2. 牛市仍需優化: 單純調整閾值雖有幫助，但未能完全解決「賣飛後不敢買回」的問題。這可能需要針對 Buy Agent 的獎勵機制做進一步訓練 (如: 錯過漲幅的懲罰)。

        






# hybrid-trader-v06 是以 hybrid-trader-v03-04-03-test2-no120-x2-buy120 作為基礎來修改的

# v06 重點

1. 移除 LSTM 特徵 (由35個特徵，降至31 個特徵)
2. 強制 CPU 訓練 (在train_v5_models.py中)
3. 調整sell agent的學習目標
4. 調整訓練和驗證的超參數設定，讓評估更穩定，且最終選出的模型會更有代表性。
5. 導入代理人共識機制


# 針對v5模型，搭配了牛熊MA120濾網，更新了回測腳本和每日運營腳本:

    * 盤後
    python backtest_v5_dca_hybrid_dynamic_filter_fixed_lstm.py --start 2025-12-09
    python daily_ops_v5_dynamic_filter_fixed_lstm.py   
    * 盤中
    python daily_ops_v5_intraday_dynamic_filter_fixed_lstm.py -i

# 移除LSTM之後，sell agent的賣出判斷變差，因此我們對sell agent的學習目標進行調整。

完成 ptrl_hybrid_system.py 中 SellEnvHybrid 的修改：

變更摘要：

1. 隨機化 Episode 長度：reset() 時隨機選擇 60~250 天作為本回合結束點。
2. 解耦獎勵視窗 (Lookahead)：無論在哪一天結算，系統都會往後看固定 60 天來計算「錯過高點」及「躲過大跌」的獎勵/懲罰。即使被隨機踢出局，也無法免於被評價後續走勢。
3. 資料切片擴大：每個 Episode 的資料從 120 天增加到 310 天，以容納最長 250 天的 Episode 加上 60 天的 Lookahead。
4. 核心獎勵公式（基礎報酬、錯失高點懲罰、躲過大跌獎勵）維持不變，只修改了計算所用的時間視窗。
5. 導入代理人共識機制

# evl 時不知道為什麼，一開始分數都會飆高，導致雖然跑了 1M steps，但最後存下來的model 卻是前面沒跑幾步的模型。 

調整 train_v5_models.py 的參數，讓評估更穩定，且最終選出的模型會更有代表性。

1. 增加評估回數 (n_eval_episodes)：
從 30 改為 100。
更多的樣本數能消除運氣成分，只有「真的強」的模型才能在 100 次測試中拿下高分。
2. 增加熵係數 (ent_coef)：
Fine-tune 目前是 0.005，建議改回 0.01（與 Pre-train 相同）。
TensorBoard 顯示 entropy 下降很快（Agent 太快變自信）。提高這個係數可以強迫 Agent 保持「好奇心」，不要太早鎖死在「死抱不賣」這個局部最佳解。
3. 降低學習率 (learning_rate)：
目前是 1e-5，可以降為 5e-6。讓 Fine-tune 的步伐更慢、更穩，避免破壞 Pre-train 學到的知識，也能減少訓練過程的震盪。

# 導入代理人共識機制 (Agent Consensus)

為了解決 Sell Agent 在強勢牛市中過早賣出 (Churning) 的問題，我們引入了「買方否決權」機制。

**核心邏輯：**
在賣出決策執行前，加入 Buy Agent 的信心確認。
*   如果 `Buy_Conf > 0.8` (Consensus Threshold)，表示 AI 極度看好後市，此時即使 Sell Agent 發出賣訊 (Confidence > 0.5)，也會被**否決 (Veto)**，強制持倉。
*   唯一例外：硬性停損 (觸發 -8% 或 槓桿後 < 0.92) 擁有最高優先級，無視共識機制直接賣出。

**驗證結果 (2023-2026 牛市)：**
*   **交易次數**：從 17 次大幅降至 4 次，有效減少磨損。
*   **平均持有天數**：從 17 天增加至 146 天，成功抱住主升段。
*   **報酬率**：驗證回測顯示報酬率從 +74.4% 提升至 +88.9%。
*   **熊市表現**：在 2022 熊市中，因 Buy Agent 信心低，不會觸發否決，Sell Agent 仍能正常發揮防守功能。

**已更新檔案：**
*   回測腳本：`backtest_v5_no_filter.py`, `backtest_v5_dca_hybrid_no_filter_fixed_lstm.py`, `backtest_v5_dca_hybrid_dynamic_filter_fixed_lstm.py`
*   實戰腳本：`daily_ops_v5_dynamic_filter_fixed_lstm.py`, `daily_ops_v5_intraday_dynamic_filter_fixed_lstm.py`
