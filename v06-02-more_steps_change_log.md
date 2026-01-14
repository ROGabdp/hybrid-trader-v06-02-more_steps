
# 每天執行這4個

    * 盤中 (大倉位預測)

    python daily_ops_v5_intraday_dynamic_n_kd_filter.py -i

    * 盤後 (大倉位確認 - 當日買賣)

    python backtest_v5_dca_hybrid_dynamic_n_kd_filter.py --start 2024-01-01  
    
    * 盤後 (大倉位確認和2x槓桿確認 - 隔日買賣，所有時期都稍微優於當日買賣)

    python backtest_v5_dca_hybrid_dynamic_n_kd_filter_next.py --start 2024-01-01  

    python backtest_v5_2x_god_fuse.py --start 2026-01-08

# v06-02-more_steps 重點

1. 以v06-02為基礎，增加訓練步數至10M steps。
2. 增加回測腳本，置入kd filter，預設 KD<90 AI才能買入，可得到最佳的 Calmar Ratio (報酬/回撤比)，KD 90 的數值 (0.406) 是所有測試中最優的。並且停損時連同DCA倉一起停損。 

**先前的腳本**

    盤後
    python backtest_v5_dca_hybrid_no_filter_fixed_lstm.py --start 2025-12-09
    python daily_ops_v5_fixed_lstm.py
    盤中
    python daily_ops_v5_intraday_fixed_lstm.py -i

**有KD濾網的腳本**
 **修改了回測和daily_ops的腳本，增加剩餘資金與倉位價值計算**

=======================================

**盤後會直接輸出報告，不需要跑daily_ops**

    python backtest_v5_dca_hybrid_dynamic_n_kd_filter.py --start 2024-01-01  

    * 盤中
    python daily_ops_v5_intraday_dynamic_n_kd_filter.py -i

=======================================

2. 增加完全用兩倍槓桿操作的腳本 (會產出最後一天的總結報告，做明日開盤買賣的參考)

**兩倍槓桿盤後**

    python backtest_v5_2x_god.py 

**兩倍槓桿加上保險盤後 (最終優化後的 Fuse 參數配置：CB_TRIGGER_THRESHOLD = -0.15 (觸發：-15% 回撤)CB_COOLDOWN_DAYS = 10 (冷卻：10 天)DELEVERAGE_RATIO = 0.50 (減倉：50%))**

=======================================

**會直接輸出報告，不需要跑daily_ops**
    
    python backtest_v5_2x_god_fuse.py --start 2026-01-08

=======================================


**God Mode 回測結果 (2017/10/16 - 2023/10/15)：**
    總報酬 (Total Return)：暴增至 +82.95% (淨利約 348萬)。遠勝大盤標竿 (+35.81%) 兩倍以上。相較於上一版 (+31.05%) 更是巨大的飛躍。

    這份 God Mode (上帝模式) 操盤策略的核心邏輯是：「利用 2 倍槓桿資產的波動，並在資金無上限的狀態下，透過複利與動態停利最大化獲利。」

    以下是策略的四大支柱總結：

    1. 交易標的：2倍槓桿合成資產
    槓桿效應：模擬一個追蹤加權指數 (TWII) 每日漲跌幅 200% 的資產。
    特性：漲的時候翻倍漲，跌的時候也翻倍跌，因此需要極強的風控與進場過濾。
    2. 進場規則：雙重濾網 (趨勢 + AI)
    趨勢濾網 (MA60)：收盤價必須站在 60日均線 之上才允許買進，確保只在多頭波段操作，避開大跌段。
    AI 強力推薦：AI 買入信心度必須大於 90% 才會觸發。
    動態加碼：
    信心度 > 95%：投入剩餘現金的 25%。
    信心度 90~95%：投入剩餘現金的 15%。
    God Mode 特色：單筆金額上限大幅放寬至 1000 萬，讓資金能隨資產成長持續複利滾動。
    3. 出場規則：動態移動停利 (Dynamic Trailing Stop)
    硬性停損：進場後若虧損達 -20% 立即砍倉 (防禦極端波動)。
    動態回檔機制：
    獲利達 +20% 時啟動移動停利。
    一般狀況：自糕點回檔 10% 則止盈出場。
    大賺擴張 (50% 門檻)：當波段獲利超過 50% 時，回檔容忍度放寬至 15%，避免在強勢噴發行情中被小碎步回檔掃出場，確保能吃到最長的大肥肉。
    4. 戰略優勢
    複利爆發：與受限的舊版不同，God Mode 在多頭市場中會隨著部位滾大而產生指數型增長，這也是其總報酬能衝上 +82.9% 的主因。
    風險管理：雖然是槓桿操作，但因為只在 MA60 以上交易，並配備移動停利，回測顯示最大回撤 (-24%) 依然低於大盤 (1x 指數) 的回撤 (-31%)。
    
    一句話總結：這是一個「漲時重錘出擊、大賺時放長線、跌時精準閃避」的 2x 槓桿複利策略。

**增加fuse機制**
    -15% 是最佳平衡點：
    Max DD 壓低至 -24.6% (遠低於大盤 -31.6%)
    總報酬依然保持最高 +183.4%
    Sharpe Ratio 最優 1.01
    假設驗證：
    ✅ -15% 確實能有效控制 Max DD 在 -25% 以內
    ❌ -20%/-30%/-35% 無法阻止 2024 閃崩 (DD 均超 -32%)
    ✅ 更嚴格的門檻 → 更低 DD，但犧牲的報酬並不明顯
    
    10 天冷卻期最佳：
    最高報酬 +188.5% (比 20 天多賺 ~28 萬)
    最佳 Sharpe Ratio 1.021
    Max DD 僅微幅增加 0.07% (可忽略)
    假設驗證：
    ✅ 10 天確實能更靈活抓到 V 轉，獲利明顯更高
    ❌ 40/60 天過於保守，Max DD 反而更差 (-27.7%)
    💡 過長的冷卻期會讓系統錯過反彈初段，導致 V 轉行情時還在防禦模式
    交易次數觀察：
    10 天：640 筆 (最頻繁交易，但勝率也最高 51.6%)
    60 天：442 筆 (減少交易但勝率下降至 41.2%)
    🎯 建議
    採用 10 天冷卻期 (--cb-cooldown 10) 作為預設值：

    風險差異極小 (-24.68% vs -24.61%)
    報酬明顯更優 (+188.5% vs +183.4%)
    Sharpe Ratio 最佳

    

**增加strat 3策略:**

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


5. 增加兩個腳本，測試隔日開盤要比今天還低才能買入，結果效果不佳

backtest_v5_2x_god_fuse_drop.py
backtest_v5_dca_hybrid_dynamic_n_kd_filter_drop.py

6. 增加一個腳本，執行 Queue and Wait Buy Logic，買入信號產生後，若不滿足買入條件，不是取消，而是進入 Queue 等待日線收跌才買入

backtest_v5_dca_hybrid_dynamic_n_kd_filter_queue.py

7. 增加一個腳本，隔日才做買賣，方便跟單。結果績效優於當日買賣

backtest_v5_dca_hybrid_dynamic_n_kd_filter_next.py
