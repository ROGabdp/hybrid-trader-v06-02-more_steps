with open('backtest_v5_dca_hybrid_dynamic_n_kd_filter.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 修正第 1705 行（row index 1704）
if lines[1704].startswith('    lines.append(f\\"'):
    lines[1704] = '    lines.append(f"   🏦 總資產:       ${total_assets:,.0f}")\r\n'

with open('backtest_v5_dca_hybrid_dynamic_n_kd_filter.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("File fixed!")
