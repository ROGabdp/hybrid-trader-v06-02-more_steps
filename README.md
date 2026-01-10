# 🚀 Hybrid Trading System V4.1 (Hybrid Optimized) for Taiwan Stock Index (^TWII)

這是一個先進的演算法交易系統，結合了用於價格預測的 **LSTM-SSAM** (Long Short-Term Memory with Sequential Self-Attention) 以及用於交易決策的 **Pro Trader RL** (Reinforcement Learning)。

# v06-02-more_steps 重點

1. 以v06-02為基礎，增加訓練步數至10M steps。
2. 增加回測腳本，置入kd filter，預設 KD<90 AI才能買入，可得到最佳的 Calmar Ratio (報酬/回撤比)，KD 90 的數值 (0.406) 是所有測試中最優的。並且停損時連同DCA倉一起停損。

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
4. 增加Kelly Criterion (凱利公式 Fractional Kelly with Cash Constraint)

python backtest_v5_dca_hybrid_dynamic_n_kd_filter_kelly.py --enable-kelly --kelly-fraction 0.06

    指令參數說明：
    --enable-kelly: 啟用凱利公式邏輯（預設已開啟，若設為 False 則會退回到均分法）。
    --kelly-fraction: 凱利下注比例。
        0.06: 代表 Half Kelly（目前建議值）。
        0.12: 代表 Full Kelly（風險極高）。
        0.03: 代表 Quarter Kelly（更保守）。
    --kd-threshold: AI 買入的 KD 過濾門檻（預設 90）。
    --sell-threshold: 賣出訊號的信心門檻（預設 0.6）。





    

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

3. 透過調整協作參數，在保持抗跌能力的同時，改善牛市表現以超越 "Buy and Hold" 策略。

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











# v03-04-03-test2-no120-x2-buy120 重點

v4模型:
    基於 v03-04-03-test2-no120-x2 版本修改，主要修改: 

    1.buy agent訓練時，目標改為買入120天內上漲超過10%。新增 Next_120d_Max 計算 - 在 calculate_features() 中計算 120 天內最高點報酬率
    2.移除唐其安通道限制 - BuyEnvHybrid.__init__() 不再只看突破日，改為所有交易日都可買入
    3.修正測試集內樣本平衡的錯誤，先前100% 只會抽取負樣本，測試出來的分數永遠都是 -0.5
    4.修正 Next_120d_Max 的計算邏輯: 原始公式 shift(-N).rolling(N).max() 計算的是「從 T+N 往回看 N 天」，而非「從 T+1 到 T+N 這 N 天」的最高價。

    # Buy Agent 評估結果分析
    關鍵發現：

    指標	數值
    測試期間	2017-10-16 ~ 2025-12-26 (2000 天)
    買入決策	100% (2000/2000) - Agent 永遠選擇買入
    買入成功率	50.1% (1002/1999)
    Next_120d_Max_Return 平均值	12.5%
    >=10% 比例	~50% (中位數 10.0%)
    問題分析：

    Agent 永遠選擇買入 - 這說明模型沒有學會「不買」的策略，可能是因為：
    訓練樣本中正樣本比例太高 (約 47%)，加上 50/50 平衡採樣讓模型偏向買入
    買入正確的獎勵 (+2.0) 大於不買正確的獎勵 (+0.5)
    模型可能過度學習到「買就對了」的策略
    50.1% 成功率接近隨機 - 因為 120 天內有 ~47% 的機會漲超過 10%，模型永遠買入的策略只是略優於隨機

V5模型:
    
    和v4模型相同，僅修改獎勵結構如下:
    V5 獎勵結構（對稱設計）：

    情境	獎勵
    買對 (action=1, 漲幅≥10%)	+1.0
    買錯 (action=1, 漲幅<10%)	0.0
    錯過好機會 (action=0, 漲幅≥10%)	0.0
    正確迴避 (action=0, 漲幅<10%)	+1.0

    V5 Buy Agent 分析結果
    指標	       V5 (對稱獎勵)	    V4 (非對稱獎勵)
    買入決策比例	33.2% (664/2000)	100% (2000/2000)
    不買決策比例	66.8% (1336/2000)	0%
    買入成功率	    69.6% (462/664)	    50.1%
    不買正確率	    59.6% (795/1335)	N/A
    整體準確率	    62.9%	            50.1%
    買入平均信心	0.927        	    0.999
    不買平均信心	0.950	            N/A
    
    關鍵改進：
    ✅ V5 學會了「不買」 - 66.8% 的時間選擇不買（V4 永遠買入）
    ✅ 買入成功率大幅提升 - 從 50.1% 提升到 69.6%
    ✅ 整體準確率提升 - 從 50.1% 提升到 62.9%
    結論：
    對稱獎勵結構讓 Agent 學會了更謹慎的決策！它不再盲目買入，而是會在低信心度時選擇「不買」，這使得當它決定買入時，成功率更高。

針對v5模型，建立了回測腳本和每日運營腳本:

    python backtest_v5_no_filter.py
    盤後
    python backtest_v5_dca_hybrid_no_filter_fixed_lstm.py --start 2025-12-09
    python daily_ops_v5_fixed_lstm.py
    盤中
    python daily_ops_v5_intraday_fixed_lstm.py -i

修改以下腳本:
    daily_ops_v5_fixed_lstm.py：
        -v5_inference()新增 open_positions 和 close_price 參數
        -針對每筆真實持倉計算報酬率並取得 Sell Agent 決策與信心
        -報告中移除「假設情境」，改為顯示每筆持倉的 AI 判斷
    daily_ops_v5_intraday_fixed_lstm.py：
        -与上述相同的修改
    evaluate_sell_agent_performance.py(新檔案)：
        -   讀取 trades_strat2_*.csv 並計算 Sell Agent 的勝率、獲利因子、停損比例等指標

# 全面更新 backtest_v5_dca_hybrid_dynamic_filter_fixed_lstm.py，現在它：

-輸出格式完全對齊基準腳本：產生與 no_filter 版本相同的所有 CSV 和 PNG 輸出。
-包含 Strategy 1 (2x Leverage) 和 Strategy 2 (Shared Pool)：兩個策略都加入了動態濾網邏輯。
-動態濾網邏輯：
    - 熊市判定：Price < MA120 連續 3 天
    - 熊市時啟用 10 日 Donchian Filter
    - 牛市時無濾網限制

-關於 ptrl_hybrid_system.py 的 MA120 改動：
    - ✅ 已確認安全：MA120 未加入 FEATURE_COLS，不會影響模型訓練或其他回測腳本。

# 針對v5模型，搭配了牛熊MA120濾網，建立了回測腳本和每日運營腳本:

    * 盤後
    python backtest_v5_dca_hybrid_dynamic_filter_fixed_lstm.py --start 2025-12-09
    python daily_ops_v5_dynamic_filter_fixed_lstm.py   
    * 盤中
    python daily_ops_v5_intraday_dynamic_filter_fixed_lstm.py -i


# v03-04-03-test2-no120-x2 重點

基於 v03-04-03-test2-no120 版本修改，主要新增兩大功能：

## 1. ✨ 動態資金配置 (Dynamic Fund Allocation) - Strat 1 & 2

**問題**：原始 Shared Pool 模式中，AI 賣出的資金只是回到 `internal_cash`，不會增加後續的 DCA/AI 買入金額，導致年底有閒置資金。

**解決方案**：每月買入金額動態計算 (適用於 Strat 1 & 2)

```python
# 每年初注入資金
yearly_pool += yearly_capital  # 60 萬

# AI 賣出時
yearly_pool += leveraged_value  # 收益回到池中

# 每月初計算買入金額
remaining_months = 13 - month  # 1月=12個月, 12月=1個月
dynamic_chunk_amount = yearly_pool / remaining_months
```

**效果**：
| 時間點 | Pool 金額 | 每倉金額 | 說明 |
|--------|-----------|----------|------|
| 2020 年初 | $600,000 | $50,000 | 標準配置 |
| 2022 年初 | $1,091,762 | **$90,980** | AI 賣出累積資金 |
| 2024 年初 | $1,091,085 | **$90,924** | 複利效應 |

---

## 2. ⚡ 大跌時 2x 槓桿 (Strat 1 Only)

**觸發條件**：當大盤從歷史高點下跌超過 **8%** (與停損點一致)

**運作邏輯**：
- 進入 2x 模式後，**所有新買入的倉位** (DCA + AI) 漲跌幅以 2 倍計算
- 當大盤**漲回到啟動 2x 時的價格**，退出槓桿模式
- 已買入的 2x 倉位**維持槓桿直到賣出**

```python
LEVERAGE_THRESHOLD = 0.08  # 下跌 8% 啟動槓桿

# 觸發條件
if price < peak_price * (1 - LEVERAGE_THRESHOLD):
    leveraged_mode = True
    leverage_trigger_price = price

# 退出條件
if price >= leverage_trigger_price:
    leveraged_mode = False
```

**槓桿事件統計** (2020-2025)：共 12 次啟動

| 啟動日期 | 結束日期 | 觸發價格 | 跌幅 |
|----------|----------|----------|------|
| 2020-03-02 | 2020-03-03 | 11,170 | -8.3% |
| 2020-03-12 (COVID) | 2020-04-15 | 10,422 | -9.5% |
| 2022-09-23 | 2022-11-14 | 14,118 | -8.7% |
| ... | ... | ... | ... |

---

## 3. 🎯 Benchmark 校準 (Pure DCA Optimization)

**問題**：Pure DCA 每月固定買入 $50,000，會因為股價無法整除而產生零頭 (e.g. 剩 $6,000)，長期累積導致總投入金額比 Yearly Lump 少了約 15%。

**解決方案**：
- 每年 12 月底，自動將累積的零頭現金一次買入。
- **效果**：與 Yearly Lump 的總投入差距縮小至 **0.25%**，比較基礎更公平。

---

## 4. 📊 最終績效對比 (2020-2025)

**所有策略資金運用效率一致化**：總投入皆為 ~$3.6M

| 策略 | 投入資金 | 最終市值 | **總報酬率** | 年化報酬 | Max DD |
|------|----------|----------|-------------|----------|--------|
| **Strat 1 (Dynamic + 2x)** | **$3,600,000** | **$7,094,794** 🏆 | **+97.08%** | **12.02%** | -29.8% |
| Strat 2 (Shared Pool) | **$3,600,000** | $6,107,058 | +69.64% | 9.25% | -27.3% |
| Yearly Lump | $3,553,882 | $6,249,220 | +75.84% | 9.91% | -31.6% |
| Pure DCA | $3,544,895 | $5,967,723 | +68.35% | 9.11% | -25.2% |

### 🏆 關鍵結論

1. **Strat 1 大勝 Yearly Lump**：
   - 最終市值高出 **$84.5 萬** (+13.5%)
   - 雖然 Max DD 略高，但報酬率完全補償了風險。
   
2. **槓桿效果顯著**：
   - Strat 1 (有槓桿) 比 Strat 2 (無槓桿) 多賺了 **$98.7 萬**，這完全歸功於 12 次的大跌 2x 抄底操作。

---

## 4. 修改的檔案

| 檔案 | 修改內容 |
|------|----------|
| `backtest_v4_dca_hybrid_with_filter_fixed_lstm.py` | 新增 `LeveragedSharedPoolBacktester` 類別取代 `DCAHybridBacktester` |

**主要程式碼變更**：
- 第 347-670 行：新的 `LeveragedSharedPoolBacktester` 類別
- 動態資金配置：`yearly_pool` 變數取代 `external_limit + internal_cash`
- 槓桿追蹤：`leverage_events`, `leverage_periods` 記錄
- 新增輸出檔案：`leverage_events_strat1_*.csv`, `daily_action_strat1_*.csv`

---

## 5. 使用方式

```bash
# 執行回測（預設從 2020-01-01 開始）
python backtest_v4_dca_hybrid_with_filter_fixed_lstm.py --start 2020-01-01

# 指定結束日期
python backtest_v4_dca_hybrid_with_filter_fixed_lstm.py --start 2020-01-01 --end 2024-12-31
```

**輸出檔案**：
```
results_backtest_v4_dca_hybrid_with_filter_fixed_lstm/
├── metrics_comparison_*.csv          # 策略績效對比
├── leverage_events_strat1_*.csv      # 槓桿啟動/結束事件
├── daily_action_strat1_*.csv         # 每日操作 (含槓桿狀態)
├── daily_timeline_strat1_*.png       # 時間線圖 (標示 2x 期間)
└── backtest_comparison_*.png         # 權益曲線對比圖
```

## 6. 👁️ 盤中/盤後監控升級 (Daily/Intraday Ops)

**功能**：在盤後 (`daily_ops_v4_fixed_lstm.py`) 與盤中 (`daily_ops_v4_intraday_fixed_lstm.py`) 報告中，同步顯示 Strategy 1 的 2x 槓桿狀態。

**顯示資訊**：
- **槓桿狀態**：`🔥 ON (2x)` 或 `❄️ OFF (1x)`
- **歷史高點 (Peak)**：目前追蹤的最高價 (Strategy 1 邏輯)
- **觸發/退出點位**：
  - 未啟動時：顯示觸發價 (Peak * 92%) 與距離
  - 已啟動時：顯示退出價 (Peak) 與距離

**範例輸出**：
```text
⚡ [2x 槓桿監控] (Strategy 1)
   狀態: 🔥 ON (2倍槓桿)
   高點: 28,400.73 | 目前跌幅: -10.50%
   退出: 28,400.73 (回到高點即退出)
```


# v03-04-03-test2-no120 重點

基於 v03-04-03-test2 版本修改，主要變更：**移除 120 天強制賣出限制** + **重新設計 Sell Agent 獎勵機制**。

## 1. 移除 120 天強制賣出限制

**問題**：原始 Sell Agent 會在持有 120 天後強制賣出，不論 AI 判斷或市場狀況。

**修改內容**：從所有回測腳本中移除 `hold_days >= 120` 條件：

| 檔案 | 修改位置 |
|------|----------|
| `backtest_v4_dca_hybrid_with_filter_rolling_lstm.py` | 第 300, 494 行 |
| `backtest_v4_dca_hybrid_with_filter_fixed_lstm.py` | 第 436, 638 行 |
| `backtest_v4_with_filter.py` | 第 160-177 行 |
| `backtest_v4_with_filter_rolling_lstm.py` | 第 254-271 行 |
| `backtest_v4_dca_hybrid_no_filter.py` | 第 198, 368 行 |
| `backtest_v4_dca_hybrid_no_filter_rolling_lstm.py` | 第 296, 480 行 |
| `backtest_v4_no_filter.py` | 第 151-168 行 |
| `backtest_v4_no_filter_rolling_lstm.py` | 第 261-276 行 |
| `ptrl_hybrid_system.py` (`HybridBacktester`) | 第 1032 行 |

**修改後**：Sell Agent 只會在以下條件賣出：
- AI 判斷賣出 (`action[0] == 1`)
- 停損 -8% (`current_return < 0.92`)

---

## 2. Sell Agent 獎勵機制重新設計 (Plan C)

**問題**：原始獎勵機制導致 Agent 學會「永遠不賣」。

**新的獎勵邏輯** (`SellEnvHybrid.step()`)：

```python
if action == 1 or self.day >= 119:  # 賣出
    # 1. 基礎獎勵：當前報酬 (獲利 10% = +1.0)
    base_reward = (current_return - 1.0) * 10
    
    # 2. 錯過高點懲罰 / 賣在高點獎勵
    if future_max > current_return + 0.01:  # 未來還會漲 >1%
        penalty = (future_max - current_return) * 2
    else:
        penalty = -0.5  # 賣在高點！獎勵
    
    # 3. 躲過大跌獎勵
    if future_min < current_return - 0.05:  # 未來會跌 >5%
        bonus = (current_return - future_min) * 5
    else:
        bonus = 0
    
    reward = base_reward - penalty + bonus

else:  # 持有
    # 動態持有懲罰（溫和版）
    if current_return >= 1.10:    # 已獲利 ≥10%
        reward = -0.01            # 輕微懲罰
    elif current_return >= 1.05:  # 獲利 5-10%
        reward = -0.002           # 非常輕微
    else:                          # <5% 或虧損
        reward = 0.0              # 不懲罰
```

**設計目標**：
- ✅ 賣在高點：錯過漲幅會被懲罰，賣在最高點有額外獎勵
- ✅ 躲過大跌：賣出後股價大跌會獲得額外獎勵
- ✅ 動態持有成本：獲利越多，持有懲罰越重，鼓勵適時賣出

---

## 3. 績效表現 (backtest_v4_with_filter)

| 指標 | 數值 | 評價 |
|------|------|------|
| 總交易次數 | 7 筆 | ✅ 合理 |
| 平均持有天數 | **77 天** | ✅ 能抓住波段 |
| 平均報酬率 | **+10.36%** | ✅ 優秀 |
| 勝率 | **85.7%** (6/7) | ✅ 非常好 |

**交易明細**：
| 買入日 | 賣出日 | 報酬率 | 持有天數 |
|--------|--------|--------|---------|
| 2023-01-09 | 2024-04-08 | +38.4% 🌟 | 294 |
| 2024-04-09 | 2024-06-18 | +9.4% | 48 |
| 2024-08-19 | 2024-08-20 | +0.09% | 1 |
| 2024-09-19 | 2024-10-21 | +6.8% | 19 |
| 2024-12-04 | 2025-03-31 | -11.0% ❌ | 74 |
| 2025-04-28 | 2025-09-15 | +26.6% 🌟 | 98 |
| 2025-09-16 | 2025-09-24 | +2.2% | 6 |

---

## 4. 訓練設定

```python
PRETRAIN_SELL_STEPS = 500_000
FINETUNE_SELL_STEPS = 500_000  # 最佳點約在 450K
```

**TensorBoard 觀察**：
- Fine-tune eval 在 ~450K 達到峰值後下降 (過擬合)
- EvalCallback 已保存最佳模型

---

# v03-04-03-test2重點 (目前績效最好版本)

沿用:
- 由前一版 v03-04-03 升級，沿用較積極的buy agent，是追求獲利的版本。 
- 沿用先前的 fixed_lstm 每日回測和盤中觀測AI可能交易模式，並臨摹之。

更新
- 獨立 Agent 檢查：Buy 和 Sell 模型分開檢查是否存在
- 使用最佳模型：訓練結束後複製 best_model.zip 為 base.zip / final.zip
- 這個版本主要 增加 KD/ MACD 到RL的訓練當中，並移除T+20和其信心 特徵

績效  (以backtest_v4_with_filter回測 V03-04-03-test2):
核心績效指標
指標	    V4 With Filter	   Buy & Hold	   優勢
總報酬率	+103.9%	            +93.6%	     ✅ +10.3%
年化報酬率	27.3%	            25.1%	       ✅ +2.2%
夏普比率	1.84	              1.17	       ✅ +57% 風險調整報酬
最大回撤	-13.4%	            -28.7%	     ✅ 回撤減少 53%

📈 交易統計
指標	           數值
交易次數	       5 筆
勝率	          100% (5/5)
平均報酬	      +17.7%
平均持有天數	  120 天
被過濾次數	    68 次

📊 三版本績效比較 (V03-03 → V03-04-03 → V03-04-03-test2)

指標	   V03-03	  V03-04-03	V03-04-03-test2	   最佳版本
總報酬率	+66.2%	+74.7%	   +103.9%	  🏆 V03-04-03-test2  
年化報酬率	18.8%	 20.9%	   27.3%	    🏆 V03-04-03-test2
夏普比率	 1.25	   1.48	     1.84	      🏆 V03-04-03-test2
最大回撤	-17.1%	-17.3%	  -13.4%	    🏆 V03-04-03-test2
勝率	     80%	  80%	      100%  	    🏆 V03-04-03-test2
平均報酬	 +12.9%	+14.4%	  +17.7%	    🏆 V03-04-03-test2
平均持有天數	106	  111	     120	        -
被過濾次數	 15	    64	       68	        -

📈 版本演進趨勢
總報酬率：66.2% → 74.7% → 103.9%  (持續上升 ↑)
夏普比率：1.25 → 1.48 → 1.84     (持續上升 ↑)
最大回撤：-17.1% → -17.3% → -13.4% (第三版明顯改善)
勝率：   80% → 80% → 100%        (第三版突破)

✨ 關鍵改進分析
版本升級	主要改進	報酬增加
V03-03 → V03-04-03	更積極的 Buy Agent & 	新增 KD/MACD 特徵 +8.5%
V03-04-03 → V03-04-03-test2	移除T+20和其信心 特徵	+29.2%
累計改進		+37.7%

🎯 結論
V03-04-03-test2 是目前最佳版本：

報酬最高 (+103.9%)
風險最低 (回撤 -13.4%)
勝率最高 (100%)
每筆交易賺最多 (+17.7%)

移除T+20和其信心 特徵的效果非常顯著，讓buy agent不會過度保守，帶來了約 30% 的報酬提升！

Note:
- V4: 訓練步數設定
PRETRAIN_BUY_STEPS = 1_000_000
PRETRAIN_SELL_STEPS = 500_000
FINETUNE_BUY_STEPS = 1_000_000
FINETUNE_SELL_STEPS = 500_000

- 最佳模型步數: 以下是從 TensorBoard 事件檔案中讀取的 精確最佳步數
buy: 184萬步
sell: 92萬步

Agent	 階段	      最佳步數	 最佳 Reward	 評估次數
Buy	   Pre-train	560,000	  0.36	        12 次
Buy	   Fine-tune	1,280,000	0.03	        25 次
Sell	 Pre-train	160,000	  53.50	        6 次
Sell	 Fine-tune	320,000	  51.30	        12 次

根據以上數據，最佳模型出現的位置：
Agent	 階段	       建議設定
Buy	   Pre-train	 600,000 (最佳在 560K)
Buy	   Fine-tune	 300,000 (最佳在 Fine-tune 第 280K)
Sell	 Pre-train	 200,000 (最佳在 160K)
Sell	 Fine-tune	 350,000 (最佳在 320K)

- 正規化方式
特徵	       正規化方法	   最終命名
K (9,3)	     / 100.0	   Norm_K
D (9,3)	     / 100.0	   Norm_D
DIF (12-26)	 / Close	   Norm_DIF
MACD9	      / Close	     Norm_MACD
OSC	        / Close	     Norm_OSC



# 沿用 v03-04 可以讀取 回測持倉狀態 的 盤中daily_ops_v4_intraday_fixed_lstm.py，且採用了固定的LSTM  backtest_v4_dca_hybrid_with_filter_fixed_lstm.py 以確保每日回測的結果一致。因此建議的操作流程簡化如下:
      📅 每日例行公事
      🌙 盤後（收盤後執行）
      
      # Step 1: 執行回測 (更新持倉到今天)
      python backtest_v4_dca_hybrid_with_filter_fixed_lstm.py --start 2025-12-09
      
      這會：
      下載最新股價資料
      用固定 LSTM 執行回測
      輸出今日的持倉狀態和操作建議
      更新 open_positions_strat2_*.csv（你的 AI 持倉明細）

      # Step 2: 執行 daily_ops_盤後 (基於最新持倉判斷)
      (自動選擇最新的回測檔案)
      python daily_ops_v4_fixed_lstm.py
      
      🎯 如何指定特定回測？
      方法 1：使用互動模式
      python daily_ops_v4_fixed_lstm.py --interactive

      方法 2：指定回測開始日期
      python daily_ops_v4_fixed_lstm.py --backtest-start 2025-12-09

      
      ☀️ 隔天盤中（開盤後任意時間）
      
      # Step 3: 執行 daily_ops_盤中 (互動選取要用的回測)
      python daily_ops_v4_intraday_fixed_lstm.py -i
      
      這會：
      抓取盤中即時價格
      用相同的固定 LSTM 計算預測
      顯示每筆 AI 持倉的即時報酬率
      告訴你今天是否應該買/賣

      Fixed LSTM 盤中腳本保留了完全相同的功能：
      # 方式 1: 互動式選擇 (用方向鍵)
      python daily_ops_v4_intraday_fixed_lstm.py -i
      # 方式 2: 指定回測起始日
      python daily_ops_v4_intraday_fixed_lstm.py --backtest-start 2025-12-09
      # 方式 3: 使用最新 (預設)
      python daily_ops_v4_intraday_fixed_lstm.py

      NOTE: ✅ 已實作！現在 daily_ops_v4_intraday_fixed_lstm.py 會自動匹配對應的 LSTM 模型：選擇哪個 CSV，就會自動載入對應日期的 Fixed LSTM 模型！這樣你可以並行測試不同時期的策略，每個都使用各自最適合的模型。



    

## ✨ 核心特色 (Key Features)

| 特色 | 說明 |
|---------|-------------|
| **本地資料整合** | TWII 歷史資料採本地 CSV 管理 (`twii_data_from_2000_01_01.csv`)，確保成交量單位 (億元) 正確，並具備自動更新機制 |
| **嚴謹訓練流程** | **Data Leakage Prevention**: LSTM 模型訓練時的資料縮放 (Scaling) 嚴格限制在訓練集內，防止 Look-ahead Bias |
| **LSTM-SSAM 預測** | T+1 與 T+5 價格預測，並使用 MC Dropout 進行不確定性估計 |
| **遷移學習 (Transfer Learning)** | 使用全球指數進行預訓練 (Pre-train) → 針對 ^TWII 進行微調 (Fine-tune) |
| **特徵融合 (Feature Fusion)** | 整合 30 種特徵，包含 LSTM 預測、信心分數與 6 種均線趨勢特徵 (Trend/Regime/Bias) |
| **PPO Agent** | 分離的買入 (Buy) 與賣出 (Sell) 代理人，並具備類別平衡機制 |
| **回測 (Backtesting)** | 完整的模擬回測，包含停損機制與績效指標計算 |

## 📊 績效結果 (2023-Present)

| 指標 (Metric) | 數值 (Value) | 備註 |
|--------|-------|------|
| **總報酬率 (Total Return)** | **+47.38%** | Strategy 2 (Shared Pool) |
| **年化報酬率 (Annualized)** | **14.09%** | 穩健成長 |
| **夏普值 (Sharpe Ratio)** | **2.32** 👑 | 極佳的風險調整回報 |
| **最大回撤 (Max Drawdown)** | **-27.8%** | 優於重壓單一策略 |
| **勝率 (Win Rate)** | **77.8%** | AI 交易 45 次 (高信心) |

## 🏗️ 系統架構 (Architecture)

```
┌─────────────────────────────────────────────────────────────────┐
│                     HYBRID TRADING SYSTEM                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  LSTM T+1    │    │  LSTM T+5    │    │  LSTM T+20   │      │
│  │   預測模型    │    │  + MC Dropout│    │  + MC Dropout│      │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘      │
│         │                   │                   │              │
│         └───────────────────┼───────────────────┼──────────────┘      │
│                             │                                    │
│                    ┌────────▼────────┐                          │
│                    │    23 特徵融合   │                          │
│                    │  (Feature Fusion)│                         │
│                    └────────┬────────┘                          │
│                             │                                    │
│         ┌───────────────────┴───────────────────┐               │
│         │                                       │               │
│  ┌──────▼──────┐                        ┌──────▼──────┐        │
│  │  Buy Agent  │                        │  Sell Agent │        │
│  │    (PPO)    │                        │    (PPO)    │        │
│  └──────┬──────┘                        └──────┬──────┘        │
│         │                                      │                │
│         └──────────────────┬───────────────────┘                │
│                            │                                     │
│                   ┌────────▼────────┐                           │
│                   │    交易訊號      │                           │
│                   └─────────────────┘                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 專案結構 (Project Structure)

```
hybrid-trader-v03-04/
├── ptrl_hybrid_system.py        # 核心系統 (資料載入/特徵計算/訓練邏輯)
├── update_twii_data.py          # 資料更新腳本 (自動抓取最新 TWII 數據)
├── twii_data_from_2000_01_01.csv # 本地 TWII 歷史資料庫 (Volume: 億元)
├── train_v3_models.py           # V3 訓練腳本 (Lightweight)
├── train_v4_models.py           # V4 訓練腳本 (Standard)
│
├── # --- 每日維運腳本 ---
├── daily_ops_v4.py              # 盤後分析 (V4)
├── daily_ops_v4_intraday.py     # 盤中分析 (Rolling LSTM, 每次重訓)
├── daily_ops_v4_intraday_fixed_lstm.py  # ⭐ 盤中分析 (Fixed LSTM, 無重訓)
├── daily_ops_dual.py            # 雙策略比較 (V3+V4)
│
├── # --- 回測腳本 ---
├── backtest_v4_no_filter.py     # V4 無濾網回測
├── backtest_v4_with_filter.py   # V4 有濾網回測
├── backtest_v4_dca_hybrid_no_filter.py  # DCA 混合無濾網
├── backtest_v4_dca_hybrid_with_filter_rolling_lstm.py  # DCA+濾網+Rolling LSTM
├── backtest_v4_dca_hybrid_with_filter_fixed_lstm.py    # ⭐ DCA+濾網+Fixed LSTM (推薦)
│
└── # --- 輸出目錄 ---
    ├── results_backtest_v4_dca_hybrid_with_filter_fixed_lstm/  # Fixed LSTM 回測結果
    ├── intraday_runs_v4_fixed/                                  # Fixed LSTM 盤中報告
    └── saved_models_*/                                          # LSTM 模型儲存
```

## 🛠️ 安裝說明 (Installation)

### 建議使用虛擬環境 (Virtual Environment)
在 Windows 上使用虛擬環境可以避免套件版本衝突，強烈建議使用。

**方法一：使用自動腳本 (推薦)**
```powershell
.\setup_env.ps1
```

**方法二：手動設定**
```powershell
# 1. 建立虛擬環境
python -m venv venv

# 2. 啟動虛擬環境
.\venv\Scripts\Activate.ps1

# 3. 安裝套件
pip install -r requirements.txt
```

### ⚡ GPU 加速設定 (重要)
本專案建議使用 NVIDIA 顯卡進行訓練加速。

**方法一：使用 setup_env.ps1 (自動)**
腳本會自動安裝支援 CUDA 11.8 的 PyTorch 版本。

**方法二：手動安裝**
若您手動執行 `pip install -r requirements.txt`，預設會安裝 CPU 版本。請執行以下指令將其替換為 GPU 版本：

```powershell
# 1. 移除 CPU 版本
pip uninstall torch torchvision torchaudio -y

# 2. 安裝 GPU 版本 (CUDA 11.8)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 系統需求 (Dependencies)

```
tensorflow>=2.10
stable-baselines3>=2.0
gymnasium
yfinance
pandas
numpy>=2.0 (V4 Models Compatibility)
ta
torch
tqdm
matplotlib
psutil
```

## 🚀 快速開始 (Quick Start)

### 1. 訓練 LSTM 模型 (長週期)

```bash
python train_lstm_models.py
```

### 2. 訓練 RL 模型 (V3 vs V4)

本專案提供兩個版本的 RL 訓練腳本，請依需求選擇：

| 特性 | V3 (Lightweight) | V4 (Standard) |
|------|------------------|---------------|
| **用途** | 輕量版，適合快速實驗 | 標準版，適合完整訓練 |
| **Buy Fine-tune** | 200,000 步 | 1,000,000 步 |
| **Sell Fine-tune** | 100,000 步 | 300,000 步 |
| **指令** | `python train_v3_models.py` | `python train_v4_models.py` |
| **輸出目錄** | `models_hybrid_v3/` | `models_hybrid_v4/` |

### 3. 每日維運 (Daily Operations)

自動化腳本能完成「LSTM 載入/訓練 → 特徵工程 → RL 推論 → 報告生成」全流程。

#### ⭐ 推薦工作流程：Fixed LSTM (結果一致)

使用固定 LSTM 模型，確保回測與盤中分析使用相同模型，結果完全可重現。

**Step 1: 盤後執行回測**
```bash
python backtest_v4_dca_hybrid_with_filter_fixed_lstm.py --start 2025-01-02
```
- 首次執行：訓練並儲存 `_fixed` 後綴的 LSTM 模型
- 後續執行：自動使用現有 `_fixed` 模型，無需重訓
- 輸出：`lstm_info_*.json`、`open_positions_strat2_*.csv`

**Step 2: 盤中即時分析**
```bash
python daily_ops_v4_intraday_fixed_lstm.py        # 使用最新回測結果
python daily_ops_v4_intraday_fixed_lstm.py -i     # 互動選擇回測 CSV
python daily_ops_v4_intraday_fixed_lstm.py --backtest-start 2025-01-02  # 指定起始日
```
- 讀取 `lstm_info_*.json`，載入與回測相同的 LSTM 模型
- 根據選擇的 CSV 自動匹配對應的 LSTM 模型
- 顯示每筆 AI 持倉的即時報酬率與停損/停利預測

**輸出目錄**：
```
results_backtest_v4_dca_hybrid_with_filter_fixed_lstm/
├── daily_action_strat2_*.csv     # 每日操作摘要
├── open_positions_strat2_*.csv   # 未平倉 AI 持倉
└── lstm_info_*.json              # 使用的 LSTM 模型路徑

intraday_runs_v4_fixed/YYYY-MM-DD_HHMMSS/
└── reports/
    ├── intraday_summary.txt
    └── intraday_summary.json
```

---

#### 📌 傳統工作流程 (Rolling LSTM)

每次執行都重新訓練 LSTM，適合需要最新模型的情境。

- **盤後分析**:
  ```bash
  python daily_ops_v4.py           # V4 單策略
  python daily_ops_dual.py         # V3+V4 雙策略比較
  ```

- **盤中即時分析** (每次重訓 LSTM，約 20-40 分鐘):
  ```bash
  python daily_ops_v4_intraday.py    # V4 專用 (含 T+20/T+5/T+1)
  python daily_ops_dual_intraday.py  # 雙策略比較版 
  ```

**流程說明：**
1. 從**證交所盤中 API** (`mis.twse.com.tw`) 下載當日即時 OHLC
2. 使用 CSV 前 5 日成交量平均作為當日預估成交量
3. 使用上述資料完整訓練 LSTM 模型 (T+20, T+5, T+1)
4. 進行 RL 推論並輸出報告

---

**功能特點：**
- **全時推論模式**: 無論 Donchian 濾網狀態，AI 都會執行預測並顯示意圖
- **濾網狀態標記**: `BUY`, `WAIT`, `FILTERED (AI: BUY)`, `FILTERED (AI: WAIT)`
- **情境分析**: Sell Agent 針對三種持倉情境 (成本區/獲利+10%/虧損-5%) 提供建議
- **持倉明細**: 顯示每筆 AI 持倉的買入價格、當前報酬率、停損/停利狀態
- 輸出 JSON 與 TXT 戰情報告

### 4. 策略回測 (Backtesting)

本系統提供兩種 V4 策略回測模式，方便評估濾網效益：

#### A. 無濾網模式 (Aggressive)
測試 AI 在**每天都可進場** (無 Donchian 濾網限制) 的績效，評估 AI 本身的判斷能力。
```bash
python backtest_v4_no_filter.py
```

#### B. 有濾網模式 (Strict)
測試 AI 在**嚴格遵守濾網** (僅 Donchian 通道突破日) 下的績效，評估濾網過濾雜訊的效果。
```bash
python backtest_v4_with_filter.py
```

**✨ 回測系統特色：**

| 功能 | 說明 |
|------|------|
| **信心度可視化** | 圖表上直接標註 AI 買賣點的信心度數值 (%) |
| **每日信心記錄** | 輸出 `daily_confidence_*.csv`，完整記錄每日 AI 信心與決策 |
| **自訂日期範圍** | 透過 `--start` 和 `--end` 參數指定回測期間 |
| **動態檔名** | 輸出檔案自動包含日期範圍，避免覆蓋 |
| **Benchmark 比較** | 策略績效 vs Buy & Hold 並排顯示 |

### 5. DCA + AI 混合策略回測

測試「定期定額 + AI 自由操作」混合策略的績效。

#### ⭐ 推薦：Fixed LSTM 版本 (結果一致)

```bash
python backtest_v4_dca_hybrid_with_filter_fixed_lstm.py --start 2025-01-02
```

- 使用固定 LSTM 模型，每次執行結果完全一致
- 首次執行訓練並儲存 `_fixed` 模型，後續自動使用
- 輸出 `lstm_info_*.json` 供盤中腳本讀取
- 輸出 `open_positions_strat2_*.csv` 記錄 AI 持倉明細

#### Rolling LSTM 版本 (每次重訓)

```bash
python backtest_v4_dca_hybrid_with_filter_rolling_lstm.py --start 2025-01-02  # 有濾網
python backtest_v4_dca_hybrid_no_filter.py                                     # 無濾網
```

**策略說明：**
1. **Strategy 1: Split 50/50 (資金對半分配)**
   - 每年年初獲得額度 (External Limit) 60 萬。
   - 額度對半拆分: DCA 30 萬 (每月2.5萬)，AI 30 萬。
   - **AI All-in**: 當 AI 決定買入時，會投入 **100%** 的可用資金。

2. **Strategy 2: Shared Pool (資金池共享)** - **Recommended**
   - 每年年初獲得 60 萬額度，由 DCA 與 AI 共享。
   - **優先順序**: 每月 DCA (5萬) 優先使用內部現金或額度，剩餘資金供 AI (每次5萬) 使用。
   - **資金循環**: AI 賣出後資金回流至內部現金池，可供 DCA 或 AI 再次使用。

**比較基準：**
1. 純定期定額：每月 5 萬元 (Pure DCA)
2. 年初一次投入：每年 60 萬 Buy & Hold (Yearly Lump Sum)

**輸出檔案 (v3.1 更新)：**
```
results_backtest_v4_dca_hybrid_no_filter/
├── backtest_comparison_*.png (策略比較圖表)
├── metrics_comparison_*.csv (績效指標比較表)
├── trades_strat1_*.csv (Strategy 1 AI 交易紀錄)
├── trades_strat2_*.csv (Strategy 2 AI 交易紀錄)
├── daily_confidence_strat1_*.csv (S1 每日信心與 Action)
└── daily_confidence_strat2_*.csv (S2 每日信心與 Action)
```
*註：`daily_confidence` 檔案包含 `action` 欄位 (BUY/SELL/hold/wait) 供詳細檢視 AI 決策。*

### 🔍 回測腳本功能比較

| 功能 | `no_filter` | `with_filter` | `dca_hybrid_no_filter` | `dca_hybrid_fixed_lstm` ⭐ |
|------|:---:|:---:|:---:|:---:|
| 自訂日期範圍 | ✅ | ✅ | ✅ | ✅ |
| DCA + AI 混合 | ❌ | ❌ | ✅ | ✅ |
| Donchian 濾網 | ❌ | ✅ | ❌ | ✅ |
| **Fixed LSTM** | ❌ | ❌ | ❌ | ✅ |
| AI 持倉明細輸出 | ❌ | ❌ | ❌ | ✅ |
| 盤中腳本整合 | ❌ | ❌ | ❌ | ✅ |

> [!IMPORTANT]
> **推薦使用 Fixed LSTM 版本**：`backtest_v4_dca_hybrid_with_filter_fixed_lstm.py` 可確保回測與盤中分析使用相同 LSTM 模型，結果完全一致。

## 📈 訓練流程 (Training Pipeline)

### Phase 1: 數據整合 (Unified Data Source)
- **本地數據**: ^TWII 使用本地 `twii_data_from_2000_01_01.csv`，確保成交量單位正確 (億元)。
- **自動更新**: 系統自動檢查並透過 `update_twii_data.py` 補齊最新交易日資料。
- **國際指數**: 下載 4 個全球指數：^GSPC, ^IXIC, ^SOX, ^DJI (from yfinance)
- **影響範圍**: 涵蓋 V3/V4 訓練、所有回測腳本以及每日維運腳本 (Daily Ops)。

### Phase 2: 特徵工程 (Feature Engineering)
- 包含 24 種特徵 (v3.0 更新)：
  - 標準化 OHLC 價格
  - 唐奇安通道 (Donchian Channel)、超級趨勢 (SuperTrend)
  - 平均K線 (Heikin-Ashi) 型態
  - RSI, MFI, ATR 指標
  - 相對強度 (Relative Strength) 指標
  - **LSTM_Pred_1d**: T+1 預測漲幅
  - **LSTM_Conf_1d**: T+1 信心度 (MC Dropout) ✨ NEW
  - **LSTM_Pred_5d**: T+5 預測漲幅
  - **LSTM_Conf_5d**: T+5 信心度 (MC Dropout)
  - **LSTM_Pred_20d**: T+20 預測漲幅 (New!)
  - **LSTM_Conf_20d**: T+20 信心度 (MC Dropout) (New!)
  - **[V4.1] 顯性特徵 (Explicit Features)**:
    - `MA20_Slope`: 短期趨勢動能
    - `Trend_Gap`: 市場體制 (短長線乖離)
    - `Bias_MA20`: 短線乖離率
    - `Dist_MA60`: 季線支撐距離
    - `Dist_MA240`: 年線生命線位置
    - `Vol_Ratio`: 相對量能 (RVol)

### Phase 3: 預訓練 (Pre-training)
- Buy Agent: 1,000,000 步 (類別平衡採樣)
- Sell Agent: 500,000 步

### Phase 4: 微調與回測 (Fine-tuning & Backtesting)
- 微調：針對 ^TWII (2000-2022) 進行訓練，Learning Rate = 1e-5
- 回測：驗證數據集 (2023-Present)

### ⚠️ 資料紀律 (Data Discipline)

> [!IMPORTANT]
> **防止資料洩漏 (Data Leakage Prevention)**
> 
> 本系統採用嚴格的時間切分策略，確保模型在訓練時不會看到驗證期的資料。

| 階段 | 資料範圍 | 說明 |
|------|----------|------|
| **LSTM 訓練** | 2000-01-01 ~ 2022-12-31 | 使用 `train_lstm_models.py` 設定的 `TRAIN_END` |
| **RL 預訓練** | 2000-01-01 ~ 2022-12-31 | 全球指數 (^TWII, ^GSPC, ^IXIC, ^SOX, ^DJI) 截止於 `SPLIT_DATE` |
| **RL 微調** | ^TWII < 2023-01-01 | 只用 `SPLIT_DATE` 之前的 TWII 資料 |
| **RL 驗證/回測** | ^TWII >= 2023-01-01 | 模型完全沒見過的資料 |

> [!NOTE]
> **T+20 訓練集切分策略 (Adaptive Split)**
> T+20 模型為了捕捉最新的市場趨勢，預設使用 **99%** 的歷史資料進行訓練。
> 若 99% 切分導致驗證集不足 (因為 T+20 需要未來標籤)，系統會自動調整策略，**強制保留最後 20 筆資料**作為驗證集，而不是回退到傳統的 80/20 切分。這確保了模型能學習到最完整的近期走勢。

**關鍵設定 (2025-12-11 更新)：**
```python
# train_lstm_models.py
TRAIN_END = "2022-12-31"

# train_v3_models.py / train_v4_models.py
SPLIT_DATE = '2023-01-01'
raw_data = hybrid.fetch_index_data(DATA_PATH, start_date="2000-01-01", end_date=SPLIT_DATE)
```

**時間線視覺化：**
```
LSTM 訓練期:      2000 ─────────────────────── 2022-12-31
RL 訓練/微調期:   2000 ─────────────────────── 2022-12-31
                                                     │
RL 驗證/回測期:                                2023-01-01 ─────── 今天
                                               (模型未見過)
```

### Phase 5: 訓練監控 (Training Monitoring)
本系統整合了 **TensorBoard** 進行訓練過程的即時監控。

**自動記錄的指標：**
- `rollout/ep_rew_mean`: 平均獎勵
- `train/loss`: 總損失
- `train/policy_gradient_loss`: 策略梯度損失
- `train/value_loss`: 價值函數損失
- `train/entropy_loss`: 熵損失
- `eval/mean_reward`: 驗證集平均獎勵 (EvalCallback)

**如何使用 TensorBoard：**
```powershell
# 在專案目錄下執行
tensorboard --logdir ./tensorboard_logs/

# 然後開啟瀏覽器前往
# http://localhost:6006
```

**日誌存放位置：**
- `./tensorboard_logs/`: TensorBoard 日誌
- `./logs/`: EvalCallback 評估結果
- `models_hybrid/best_tuned/`: 驗證集最佳模型

---

## 📊 輸出結果 (Output)

執行 `ptrl_hybrid_system.py` 後，您將獲得：

- `models_hybrid/ppo_buy_twii_final.zip`: 微調後的 Buy Model
- `models_hybrid/ppo_sell_twii_final.zip`: 微調後的 Sell Model
- `results_hybrid/final_performance.png`: 績效圖表
- `tensorboard_logs/`: 訓練過程日誌 (可用 TensorBoard 查看)

## 🔧 V3 vs V4 版本比較

| 項目 | V3 (Lightweight) | V4 (Standard) | 原始版 (ptrl_hybrid_system.py) |
|-----|------------------|-----------------|--------------------------------|
| **Pre-train Buy** | 1,000,000 | 1,000,000 | 1,000,000 |
| **Pre-train Sell** | 500,000 | 500,000 | 500,000 |
| **Fine-tune Buy** | **200,000** | **1,000,000** | 1,000,000 |
| **Fine-tune Sell** | **100,000** | **300,000** | 300,000 |
| **信心度門檻** | [0.001, 0.010] v2.5 | [0.001, 0.010] v2.5 | [0.005, 0.015] (舊版) |
| **特徵快取** | 強制清除 | 強制清除 | 使用快取 (需手動清除) |
| **模型路徑** | `models_hybrid_v3` | `models_hybrid_v4` | `models_hybrid` |

---

## 🔮 LSTM 信心度解讀指南 (Confidence Interpretation)

### 計算原理 (Methodology)
信心度 (`LSTM_Conf_1d`, `LSTM_Conf_5d`) 是基於 **蒙地卡羅 Dropout (MC Dropout)** 計算的：
1. 對同一筆資料進行 30 次預測（每次 Dropout 隨機遮蔽不同神經元）
2. 計算這 30 次預測的**變異係數 (CV)** = 標準差 ÷ 平均值
3. CV 越小 → 模型越穩定 → 信心度越高

### 門檻設定 (v3.0)

| 模型 | threshold_high | threshold_low | 說明 |
|------|----------------|---------------|------|
| **T+1** | 0.008 (0.8%) | 0.040 (4.0%) | 範圍較寬，適應較高的 CV 分佈 |
| **T+5** | 0.001 (0.1%) | 0.010 (1.0%) | 範圍較窄，模型本身較穩定 |
| **T+20**| 0.010 (1.0%) | 0.030 (3.0%) | 長週期不確定性高，門檻適度放寬 |

```python
# ptrl_hybrid_system.py add_lstm_features()
# T+1 信心度
score_1d = 1.0 - (cv - 0.008) / (0.040 - 0.008)
conf_1d = np.clip(score_1d, 0.0, 1.0)

# T+5 信心度
score_5d = 1.0 - (cv - 0.001) / (0.010 - 0.001)
conf_5d = np.clip(score_5d, 0.0, 1.0)

# T+20 信心度
score_20d = 1.0 - (cv - 0.010) / (0.030 - 0.010)
conf_20d = np.clip(score_20d, 0.0, 1.0)
```

### 分數對照表

| 信心度 | 解讀 | 建議 |
|--------|------|------|
| **0.8+** | 🟢 **高信心** - 模型非常確定 | 預測可靠度高，可作為主要參考 |
| **0.6-0.8** | 🟡 **中等偏高** - 正常水準 | 預測可參考，但需結合其他指標 |
| **0.4-0.6** | 🟡 **中等** - 略有不確定性 | 預測僅供輔助參考 |
| **< 0.4** | 🔴 **低信心** - 模型不確定 | 預測不穩定，謹慎採信 |

### 實際應用建議
1. **信心度 0.8+**：可以更積極地參考 LSTM 的漲跌預測
2. **信心度 0.6-0.8**：預測方向可參考，但點位預估需打折扣
3. **信心度 0.4-0.6**：預測僅供輔助參考，建議搭配其他技術指標
4. **信心度 < 0.4**：模型對當天的判斷較不確定，可能是因為市場處於異常波動期

---

## 📚 參考文獻 (References)

- **Pro Trader RL**: [Paper Implementation](https://arxiv.org/abs/xxxx)
- **LSTM-SSAM**: Sequential Self-Attention for time series prediction
- **MC Dropout**: Uncertainty estimation via Monte Carlo Dropout

## 📄 授權 (License)

MIT License

## 👤 作者 (Author)

Phil Liang

---

*Built with Python, TensorFlow, Stable-Baselines3, and ❤️*
