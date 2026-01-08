"""
AAS得点計算テスト - CEO提供データ

CEO式の完全実装:
1. 15% = 15 として扱う（0.15ではない）
2. 母集団標準偏差を使用（STDEV.P, ddof=0）
3. baseCalc = 0.55 × ZH + 0.45 × ZR
4. AAS = 12 × tanh(baseCalc) × Shr
"""

import numpy as np

# CEOから提供されたデータ（16頭）
horses_data = [
    # 馬番, 単勝件数, 単勝的中率, 単勝補正回収率, 複勝件数, 複勝的中率, 複勝補正回収率
    [1, 250, 11.2, 55.5, 250, 35.6, 86.6],
    [2, 254, 12.6, 93.8, 254, 29.1, 80.9],
    [3, 241, 10.8, 87.0, 241, 24.1, 64.9],
    [4, 240, 12.9, 115.8, 240, 27.9, 84.5],
    [5, 251, 4.8, 53.7, 251, 19.9, 72.9],
    [6, 260, 6.9, 80.2, 260, 23.8, 85.5],
    [7, 243, 6.6, 69.8, 243, 18.5, 77.4],
    [8, 241, 7.5, 96.4, 241, 18.7, 76.3],
    [9, 222, 4.5, 68.3, 222, 24.3, 117.7],
    [10, 194, 5.7, 76.5, 194, 21.6, 88.5],
    [11, 192, 8.9, 130.5, 192, 22.9, 112.8],
    [12, 187, 4.3, 69.9, 187, 17.6, 86.6],
    [13, 160, 5.0, 63.4, 160, 12.5, 51.9],
    [14, 163, 3.7, 56.2, 163, 8.6, 40.5],
    [15, 141, 2.8, 53.1, 141, 9.9, 56.3],
    [16, 124, 1.6, 43.6, 124, 11.3, 78.8]
]

print("="*80)
print("📊 AAS得点計算テスト - CEO提供データ（16頭）")
print("="*80)
print()

# Step 1: 基礎値計算（Hit_raw, Ret_raw, N_min）
print("【Step 1】基礎値計算（Hit_raw, Ret_raw, N_min）")
print("-"*80)
print(f"{'馬番':<4} {'単勝的中率':<10} {'複勝的中率':<10} {'単勝補正回収率':<14} {'複勝補正回収率':<14} {'Hit_raw':<10} {'Ret_raw':<10} {'N_min':<8}")
print("-"*80)

results = []

for data in horses_data:
    umaban = int(data[0])
    cnt_win = int(data[1])
    rate_win_hit = data[2]      # %値のまま（11.2% = 11.2）
    adj_win_ret = data[3]       # %値のまま（55.5% = 55.5）
    cnt_place = int(data[4])
    rate_place_hit = data[5]    # %値のまま（35.6% = 35.6）
    adj_place_ret = data[6]     # %値のまま（86.6% = 86.6）
    
    # CEO式: Hit_raw, Ret_raw 計算（%値のまま使用）
    Hit_raw = 0.65 * rate_win_hit + 0.35 * rate_place_hit
    Ret_raw = 0.35 * adj_win_ret + 0.65 * adj_place_ret
    N_min = min(cnt_win, cnt_place)
    
    results.append({
        'umaban': umaban,
        'Hit_raw': Hit_raw,
        'Ret_raw': Ret_raw,
        'N_min': N_min,
        'rate_win_hit': rate_win_hit,
        'rate_place_hit': rate_place_hit,
        'adj_win_ret': adj_win_ret,
        'adj_place_ret': adj_place_ret
    })
    
    print(f"{umaban:<4} {rate_win_hit:<10.1f} {rate_place_hit:<10.1f} {adj_win_ret:<14.1f} {adj_place_ret:<14.1f} {Hit_raw:<10.2f} {Ret_raw:<10.2f} {N_min:<8}")

print()

# Step 2: グループ統計（母集団標準偏差 STDEV.P）
print("【Step 2】グループ統計（母集団標準偏差 STDEV.P）")
print("-"*80)

hit_raws = [r['Hit_raw'] for r in results]
ret_raws = [r['Ret_raw'] for r in results]

μH = np.mean(hit_raws)
σH = np.std(hit_raws, ddof=0)  # ddof=0 → 母集団標準偏差（STDEV.P）
μR = np.mean(ret_raws)
σR = np.std(ret_raws, ddof=0)

print(f"Hit_raw平均（μH）:         {μH:.3f}")
print(f"Hit_raw標準偏差（σH）:     {σH:.3f}")
print(f"Ret_raw平均（μR）:         {μR:.3f}")
print(f"Ret_raw標準偏差（σR）:     {σR:.3f}")
print()

# Step 3: Zスコア化
print("【Step 3】Zスコア化")
print("-"*80)
print(f"{'馬番':<4} {'Hit_raw':<10} {'Ret_raw':<10} {'ZH':<10} {'ZR':<10}")
print("-"*80)

for r in results:
    ZH = (r['Hit_raw'] - μH) / σH if σH > 0 else 0
    ZR = (r['Ret_raw'] - μR) / σR if σR > 0 else 0
    
    r['ZH'] = ZH
    r['ZR'] = ZR
    
    print(f"{r['umaban']:<4} {r['Hit_raw']:<10.2f} {r['Ret_raw']:<10.2f} {ZH:<10.3f} {ZR:<10.3f}")

print()

# Step 4: 信頼度収縮（Shrinkage）
print("【Step 4】信頼度収縮（Shrinkage）")
print("-"*80)
print(f"{'馬番':<4} {'N_min':<8} {'Shr':<10}")
print("-"*80)

for r in results:
    N_min = r['N_min']
    Shr = np.sqrt(N_min / (N_min + 400))
    r['Shr'] = Shr
    
    print(f"{r['umaban']:<4} {N_min:<8} {Shr:<10.4f}")

print()

# Step 5: AAS得点計算
print("【Step 5】AAS得点計算")
print("-"*80)
print(f"{'馬番':<4} {'ZH':<10} {'ZR':<10} {'Shr':<10} {'baseCalc':<10} {'AAS':<10}")
print("-"*80)

for r in results:
    ZH = r['ZH']
    ZR = r['ZR']
    Shr = r['Shr']
    
    # CEO式: baseCalc = 0.55 × ZH + 0.45 × ZR
    baseCalc = 0.55 * ZH + 0.45 * ZR
    
    # CEO式: AAS = 12 × tanh(baseCalc) × Shr
    AAS = 12 * np.tanh(baseCalc) * Shr
    
    # CEO仕様: 小数点第2位を四捨五入
    AAS = round(AAS, 1)
    
    r['baseCalc'] = baseCalc
    r['AAS'] = AAS
    
    print(f"{r['umaban']:<4} {ZH:<10.3f} {ZR:<10.3f} {Shr:<10.4f} {baseCalc:<10.3f} {AAS:<10.1f}")

print()

# Step 6: 最終ランキング
print("【Step 6】最終ランキング")
print("="*80)

# AAS得点でソート
results_sorted = sorted(results, key=lambda x: x['AAS'], reverse=True)

print(f"{'順位':<4} {'馬番':<4} {'AAS得点':<10} {'Hit_raw':<10} {'Ret_raw':<10} {'N_min':<8}")
print("-"*80)

for i, r in enumerate(results_sorted, 1):
    print(f"{i:<4} {r['umaban']:<4} {r['AAS']:<+10.1f} {r['Hit_raw']:<10.2f} {r['Ret_raw']:<10.2f} {r['N_min']:<8}")

print()
print("="*80)
print("✅ AAS得点計算完了！")
print("="*80)
print()

# 詳細出力（上位3頭）
print("【詳細】上位3頭のAAS得点内訳")
print("-"*80)

for i in range(min(3, len(results_sorted))):
    r = results_sorted[i]
    print(f"\n第{i+1}位: 馬番{r['umaban']} - AAS得点: {r['AAS']:+.1f}点")
    print(f"  単勝的中率:       {r['rate_win_hit']:.1f}%")
    print(f"  複勝的中率:       {r['rate_place_hit']:.1f}%")
    print(f"  補正単勝回収率:   {r['adj_win_ret']:.1f}%")
    print(f"  補正複勝回収率:   {r['adj_place_ret']:.1f}%")
    print(f"  Hit_raw:          {r['Hit_raw']:.2f}")
    print(f"  Ret_raw:          {r['Ret_raw']:.2f}")
    print(f"  ZH:               {r['ZH']:.3f}")
    print(f"  ZR:               {r['ZR']:.3f}")
    print(f"  Shrinkage:        {r['Shr']:.4f}")
    print(f"  baseCalc:         {r['baseCalc']:.3f}")
    print(f"  AAS得点:          {r['AAS']:+.1f}点")
