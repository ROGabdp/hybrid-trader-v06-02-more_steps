
def generate_end_date_summary(bt1, twii_df, start_date, end_date, buy_model, sell_model, 
                               feature_cols, regime_history, sell_threshold, buy_consensus_threshold, kd_threshold):
    """生成回測結束日摘要報告 (end_date_summary_YYYYMMDD_YYYYMMDD.txt)"""
    import numpy as np
    from datetime import datetime
    
    if len(twii_df) == 0:
        return
    
    # 最後一日資料
    last_date = twii_df.index[-1]
    last_row = twii_df.iloc[-1]
    
    # 基本行情
    open_price = last_row['Open']
    high_price = last_row['High']
    low_price = last_row['Low']
    close_price = last_row['Close']
    volume = last_row['Volume']
    
    # 技術指標
    ma20 = last_row.get('MA20', np.nan)
    ma60 = last_row.get('MA60', np.nan)
    ma120 = last_row.get('MA120', np.nan)
    ma240 = last_row.get('MA240', np.nan)
    k_value = last_row.get('K_raw', np.nan)
    
    # 體制狀態
    if regime_history and len(regime_history) > 0:
        last_regime = regime_history[-1]
        regime_mode = last_regime['regime']
        regime_ma120 = last_regime['ma120']
    else:
        regime_mode = 'BULL' if close_price >= ma120 else 'BEAR'
        regime_ma120 = ma120
    
    # 槓桿狀態
    leveraged_mode = bt1.equity_curve[-1].get('leveraged_mode', False) if bt1.equity_curve else False
    
    # 計算當前跌幅和觸發點
    peak_price = close_price
    if bt1.leverage_events:
        for event in bt1.leverage_events:
            if event['event'] == 'START':
                peak_price = event.get('peak_price', close_price)
    
    current_drawdown = (peak_price - close_price) / peak_price * 100 if peak_price > 0 else 0
    trigger_price = peak_price * (1 - bt1.LEVERAGE_THRESHOLD)
    distance_to_trigger = ((close_price - trigger_price) / close_price * 100) if not leveraged_mode else 0
    
    # AI 預測 (最後一日)
    last_features = twii_df[feature_cols].iloc[-1].values.astype(np.float32)
    obs = np.nan_to_num(last_features, nan=0.0, posinf=1.0, neginf=-1.0).reshape(1, -1)
    
    buy_action_pred, _ = buy_model.predict(obs, deterministic=True)
    buy_probs = buy_model.policy.get_distribution(buy_model.policy.obs_to_tensor(obs)[0]).distribution.probs.detach().cpu().numpy()[0]
    buy_conf = float(buy_probs[1]) if buy_action_pred[0] == 1 else float(buy_probs[0])
    buy_signal = "BUY" if buy_action_pred[0] == 1 else "WAIT"
    
    # KD 濾網檢查
    kd_pass = k_value < kd_threshold if not np.isnan(k_value) else True
    
    # 持倉計算
    ai_positions = bt1.open_positions
    dca_positions = bt1.dca_open_positions if hasattr(bt1, 'dca_open_positions') else []
    
    # 計算持倉價值
    ai_total_cost = sum(pos['cost'] for pos in ai_positions)
    ai_total_shares = sum(pos['shares'] for pos in ai_positions)
    ai_current_value = sum(
        pos['cost'] * (1 + (close_price / pos['buy_price'] - 1) * pos.get('leverage', 1))
        for pos in ai_positions
    )
    
    dca_total_cost = sum(pos['cost'] for pos in dca_positions)
    dca_total_shares = sum(pos['shares'] for pos in dca_positions)
    dca_current_value = sum(
        pos['cost'] * (1 + (close_price / pos['buy_price'] - 1) * pos.get('leverage', 1))
        for pos in dca_positions
    )
    
    total_cost = ai_total_cost + dca_total_cost
    total_current_value = ai_current_value + dca_current_value
    unrealized_profit = total_current_value - total_cost
    unrealized_pct = (unrealized_profit / total_cost * 100) if total_cost > 0 else 0
    
    remaining_cash = bt1.remaining_cash if hasattr(bt1, 'remaining_cash') else 0
    total_assets = total_current_value + remaining_cash
    
    # 2x 倉位統計
    ai_2x_count = sum(1 for pos in ai_positions if pos.get('leverage', 1) > 1)
    dca_2x_count = sum(1 for pos in dca_positions if pos.get('leverage', 1) > 1)
    total_2x = ai_2x_count + dca_2x_count
    
    # 關鍵特徵計算
    ma20_momentum = ((ma20 / twii_df.iloc[-5]['MA20'] - 1) * 100) if len(twii_df) >= 5 and not np.isnan(ma20) else 0
    regime_score = ((close_price / ma120 - 1) * 100) if not np.isnan(ma120) else 0
    short_divergence = ((close_price / ma20 - 1) * 100) if not np.isnan(ma20) else 0
    quarterly_distance = ((close_price / ma60 - 1) * 100) if not np.isnan(ma60) else 0
    yearly_position = ((close_price / ma240 - 1) * 100) if not np.isnan(ma240) else 0
    relative_volume = last_row.get('Volume_Ratio', 1.0)
    
    # ===== 計算當日交易金額 (新功能) =====
    today_buy_1x_count = 0
    today_buy_1x_amount = 0
    today_buy_2x_count = 0
    today_buy_2x_amount = 0
    today_sell_1x_count = 0
    today_sell_1x_amount = 0
    today_sell_2x_count = 0
    today_sell_2x_amount = 0
    
    # 統計當日買入
    for signal in bt1.ai_buy_signals:
        if signal['date'] == last_date:
            if signal.get('leverage', 1) > 1:
                today_buy_2x_count += 1
                today_buy_2x_amount += signal.get('cost', 0)
            else:
                today_buy_1x_count += 1
                today_buy_1x_amount += signal.get('cost', 0)
    
    # 統計當日賣出
    for signal in bt1.ai_sell_signals:
        if signal['date'] == last_date:
            if signal.get('leverage', 1) > 1:
                today_sell_2x_count += 1
                today_sell_2x_amount += signal.get('cost', 0)  # 用原始成本
            else:
                today_sell_1x_count += 1
                today_sell_1x_amount += signal.get('cost', 0)
    
    # 生成報告
    current_time = datetime.now().strftime('%H:%M:%S')
    
    lines = []
    lines.append("=" * 50)
    lines.append(f"📅 V5 回測結束日摘要 - {last_date.strftime('%Y-%m-%d')}")
    lines.append(f"⏰ 生成時間: {current_time}")
    lines.append("=" * 50)
    lines.append(f"📊 Open:  {open_price:,.2f}")
    lines.append(f"📈 High:  {high_price:,.2f}")
    lines.append(f"📉 Low:   {low_price:,.2f}")
    lines.append(f"💰 Close: {close_price:,.2f} (收盤)")
    lines.append(f"📦 Volume: {volume:.2f} 億元")
    lines.append("-" * 50)
    
    # 市場體制監控
    lines.append("📊 [市場體制監控] (MA120 動態濾網)")
    regime_icon = "🐂" if regime_mode == "BULL" else "🐻"
    lines.append(f"   體制: {regime_icon} {regime_mode} Mode")
    lines.append(f"   MA120: {regime_ma120:,.2f} | 收盤價: {close_price:,.2f}")
    
    if regime_mode == "BULL":
        lines.append("   濾網狀態: 🟢 未啟用 (牛市自由模式)")
        lines.append("   ℹ️ AI 可自由判斷買賣，無濾網限制")
    else:
        lines.append("   濾網狀態: 🔴 已啟用 (熊市防守模式)")
        lines.append("   ⚠️ AI 買入需突破 10 日高點 (Donchian Filter)")
    
    lines.append("-" * 30)
    kd_status = "✅ 通過" if kd_pass else f"❌ 未通過 (K={k_value:.1f} >= {kd_threshold})"
    lines.append(f"   [KD 濾網] K(9,3): {k_value:.1f} | {kd_status}")
    lines.append("-" * 50)
    
    # 槓桿監控
    lines.append("⚡ [2x 槓桿監控] (Strategy 1)")
    lev_status = "🔥 ON (2倍槓桿)" if leveraged_mode else "❄️ OFF (1倍槓桿)"
    lines.append(f"   狀態: {lev_status}")
    lines.append(f"   高點: {peak_price:,.2f} | 目前跌幅: {current_drawdown:.2f}%")
    if not leveraged_mode:
        lines.append(f"   觸發: {trigger_price:,.2f} (距離: {distance_to_trigger:.2f}%)")
    lines.append("-" * 50)
    
    # 關鍵特徵
    lines.append("📐 [關鍵特徵]")
    lines.append(f"   MA20 動能: {ma20_momentum:+.2f}%  (>0 轉強)")
    lines.append(f"   市場體制: {regime_score:+.2f}%  (>0 多頭結構)")
    lines.append(f"   短線乖離: {short_divergence:+.2f}%")
    lines.append(f"   季線距離: {quarterly_distance:+.2f}%")
    lines.append(f"   年線位置: {yearly_position:+.2f}%  (>0 長多)")
    lines.append(f"   相對量能: {relative_volume:.2f}x   (>1.0 放量)")
    lines.append("-" * 50)
    
    # 操盤手 V5
    lines.append("🤖 [操盤手 V5] (對稱獎勵 + 動態濾網)")
    buy_icon = "🚀" if buy_signal == "BUY" else "⏸️"
    lines.append(f"   🛒 買入訊號: {buy_icon} {buy_signal} ({buy_conf*100:.1f}%)")
    lines.append("-" * 50)
    
    # 盤後建議
    if buy_signal == "BUY" and regime_mode == "BULL" and kd_pass:
        suggestion = "⭐⭐ V5 強力買進 (Strong Buy) ⭐⭐"
    elif buy_signal == "BUY" and kd_pass:
        suggestion = "⭐ V5 買進 (Buy)"
    elif buy_signal == "BUY" and not kd_pass:
        suggestion = "⚠️ AI建議買進，但 KD 過熱 (需觀察)"
    else:
        suggestion = "⏸️ V5 等待 (Wait)"
    
    lines.append(f"💡 盤後建議: {suggestion} [{regime_icon}{regime_mode}]")
    lines.append("-" * 50)
    
    # 持倉狀態
    lines.append("💼 [Strategy 1 持倉狀態]")
    lines.append(f"   📅 回測期間: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    lines.append(f"   🏛️  DCA 倉位: {len(dca_positions)} 倉")
    lines.append(f"   🤖 AI 倉位: {len(ai_positions)} 倉")
    lines.append(f"   📊 總倉數: {len(ai_positions) + len(dca_positions)} 倉")
    if total_2x > 0:
        lines.append(f"   🔥 2x 倉位: {total_2x} 倉 (DCA:{dca_2x_count} + AI:{ai_2x_count})")
    lines.append("-" * 50)
    
    # 資金與倉位價值
    lines.append("💰 [資金與倉位價值]")
    lines.append(f"   📦 AI 持倉成本:  ${ai_total_cost:,.0f} ({ai_total_shares} 股)")
    lines.append(f"   📦 DCA 持倉成本: ${dca_total_cost:,.0f} ({dca_total_shares} 股)")
    lines.append("   " + "─" * 25)
    lines.append(f"   💵 總投入成本:   ${total_cost:,.0f}")
    lines.append(f"   💎 目前市值:     ${total_current_value:,.0f}")
    profit_sign = "+" if unrealized_profit >= 0 else ""
    lines.append(f"   📈 未實現損益:   ${profit_sign}{unrealized_profit:,.0f} ({profit_sign}{unrealized_pct:.2f}%)")
    lines.append("   " + "─" * 25)
    lines.append(f"   💵 剩餘可用現金: ${remaining_cash:,.0f}")
    lines.append(f"   🏦 總資產:       ${total_assets:,.0f}")
    lines.append("-" * 50)
    
    # ===== 當日交易總結 (含交易金額統計) =====
    lines.append(f"📝 [當日交易總結] (回測: 以收盤價 {close_price:,.2f} 執行)")
    
    # 顯示交易金額統計
    total_buy_amount = today_buy_1x_amount + today_buy_2x_amount
    total_sell_amount = today_sell_1x_amount + today_sell_2x_amount
    
    if total_buy_amount > 0 or total_sell_amount > 0:
        lines.append("")
        lines.append("   💰 當日交易金額統計:")
        
        if total_buy_amount > 0:
            lines.append("   ├─ 📈 買入:")
            if today_buy_1x_count > 0:
                lines.append(f"   │  • 無槓桿 (1x): {today_buy_1x_count} 倉 = ${today_buy_1x_amount:,.0f}")
            if today_buy_2x_count > 0:
                lines.append(f"   │  • 有槓桿 (2x): {today_buy_2x_count} 倉 = ${today_buy_2x_amount:,.0f}")
            lines.append(f"   │  • 總買入: ${total_buy_amount:,.0f}")
        
        if total_sell_amount > 0:
            lines.append("   ├─ 📉 賣出:")
            if today_sell_1x_count > 0:
                lines.append(f"   │  • 無槓桿 (1x): {today_sell_1x_count} 倉 = ${today_sell_1x_amount:,.0f}")
            if today_sell_2x_count > 0:
                lines.append(f"   │  • 有槓桿 (2x): {today_sell_2x_count} 倉 = ${today_sell_2x_amount:,.0f}")
            lines.append(f"   │  • 總賣出: ${total_sell_amount:,.0f}")
        
        net_amount = total_buy_amount - total_sell_amount
        net_symbol = "淨買入" if net_amount > 0 else "淨賣出" if net_amount < 0 else "持平"
        lines.append(f"   └─ 💼 {net_symbol}: ${abs(net_amount):,.0f}")
        lines.append("")
    
    # 交易判斷說明
    if buy_signal == "BUY" and kd_pass:
        if regime_mode == "BULL":
            lines.append("   🟢 回測交易: AI+1倉 (V5 無濾網限制, AI判斷BUY)")
        else:
            lines.append("   🟡 回測交易: AI+1倉 (通過 10日高點濾網)")
        lines.append("   ℹ️ 實際跟單: 明日執行時價格可能不同")
    elif buy_signal == "BUY" and not kd_pass:
        lines.append(f"   ⏸️ 無交易: KD濾網未通過 (K={k_value:.1f} >= {kd_threshold})")
    else:
        lines.append("   ⏸️ 無交易: AI 判斷 WAIT")
    lines.append("-" * 50)
    
    # AI 持倉明細 + Sell Agent 判斷
    if ai_positions:
        lines.append("📦 [AI持倉明細 + Sell Agent 判斷]")
        for idx, pos in enumerate(ai_positions, 1):
            buy_price = pos['buy_price']
            buy_date_str = pos['buy_date']
            leverage = pos.get('leverage', 1.0)
            
            # 計算報酬
            base_return = close_price / buy_price
            leveraged_return = 1 + (base_return - 1) * leverage
            return_pct = (leveraged_return - 1) * 100
            
            # Sell Agent 判斷
            sell_obs = np.concatenate([obs[0], [leveraged_return]]).astype(np.float32).reshape(1, -1)
            sell_action, _ = sell_model.predict(sell_obs, deterministic=True)
            sell_probs = sell_model.policy.get_distribution(sell_model.policy.obs_to_tensor(sell_obs)[0]).distribution.probs.detach().cpu().numpy()[0]
            sell_conf = float(sell_probs[1]) if sell_action[0] == 1 else float(sell_probs[0])
            
            is_sell_signal = (sell_action[0] == 1 and sell_conf > sell_threshold)
            is_stop_loss = leveraged_return < 0.92
            
            # 共識檢查
            is_consensus_veto = False
            if is_sell_signal and not is_stop_loss:
                if buy_action_pred[0] == 1 and buy_conf > buy_consensus_threshold:
                    is_consensus_veto = True
            
            # 決定狀態
            if is_stop_loss:
                status = f"🔴 SELL 建議 (停損 {leveraged_return*100:.1f}%)"
            elif is_consensus_veto:
                status = f"🟢 HOLD AI賣訊被否決 (🚫 Consensus Veto (Buy Conf {buy_conf*100:.1f}% > {buy_consensus_threshold}))"
            elif is_sell_signal:
                status = f"🔴 SELL 建議 (AI賣出 {sell_conf*100:.1f}%)"
            else:
                status = f"🟢 HOLD AI決定 ({(1-sell_conf)*100:.1f}%)"
            
            lev_tag = f" [2x]" if leverage > 1 else ""
            lines.append(f"   #{idx} 買入: {buy_date_str} @ {buy_price:,.2f}{lev_tag}")
            lines.append(f"       報酬: {return_pct:+.2f}% | {status}")
        lines.append("-" * 50)
    
    # DCA 持倉明細
    if dca_positions:
        lines.append("📦 [DCA持倉明細]")
        for idx, pos in enumerate(dca_positions, 1):
            buy_price = pos['buy_price']
            buy_date_str = pos['buy_date']
            leverage = pos.get('leverage', 1.0)
            
            base_return = close_price / buy_price
            leveraged_return = 1 + (base_return - 1) * leverage
            return_pct = (leveraged_return - 1) * 100
            
            lev_tag = f" [2x]" if leverage > 1 else ""
            lines.append(f"   #{idx} 買入: {buy_date_str} @ {buy_price:,.2f}{lev_tag}")
            lines.append(f"       報酬: {return_pct:+.2f}% | 槓桿: {leverage:.1f}x")
        lines.append("-" * 50)
    
    lines.append("=" * 50)
    
    # 保存報告
    start_str = start_date.strftime('%Y%m%d')
    end_str = end_date.strftime('%Y%m%d')
    report_path = os.path.join(RESULTS_PATH, f'end_date_summary_{start_str}_{end_str}.txt')
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"\n[Output] 📄 End Date Summary: {report_path}")
    return report_path
