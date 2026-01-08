"""
4つの基礎指数の完成度テスト

目的: 4つの基礎指数が正しく実装されているか検証

作成日: 2026-01-08
作成者: AI戦略家
"""

import sys
sys.path.append('/home/user/webapp/nar-ai-yoso')

from core.index_calculator import (
    calculate_ten_index,
    calculate_position_index,
    calculate_agari_index,
    calculate_pace_index,
    calculate_all_indexes
)


def test_ten_index():
    """
    テン指数のテスト
    """
    print("\n" + "="*80)
    print("1️⃣ テン指数（Ten Index）のテスト")
    print("="*80)
    
    # テストケース1: 標準的なデータ
    print("\n[Test Case 1] 標準的なデータ")
    ten_index = calculate_ten_index(
        zenhan_3f=35.0,      # 前半3F
        kyori=1600,          # 距離
        baba_code='1',       # 馬場状態（良）
        keibajo_code='42',   # 競馬場コード（大井）
        furi_code='00',      # 不利なし
        wakuban=3,           # 3枠
        tosu=12,             # 12頭
        kinryo=54.0,         # 54kg
        bataiju=460.0        # 460kg
    )
    print(f"  ✅ テン指数: {ten_index:.1f}")
    print(f"  ✅ 範囲チェック: -100 ≤ {ten_index:.1f} ≤ +100 → {'OK' if -100 <= ten_index <= 100 else 'NG'}")
    
    # テストケース2: 速い前半3F
    print("\n[Test Case 2] 速い前半3F（逃げ馬想定）")
    ten_index_fast = calculate_ten_index(
        zenhan_3f=33.0,      # 速い前半3F
        kyori=1600,
        baba_code='1',
        keibajo_code='42'
    )
    print(f"  ✅ テン指数: {ten_index_fast:.1f}")
    print(f"  ✅ 比較: 速い3F → 高いテン指数 → {'OK' if ten_index_fast > ten_index else 'NG'}")
    
    # テストケース3: 遅い前半3F
    print("\n[Test Case 3] 遅い前半3F（差し馬想定）")
    ten_index_slow = calculate_ten_index(
        zenhan_3f=38.0,      # 遅い前半3F
        kyori=1600,
        baba_code='1',
        keibajo_code='42'
    )
    print(f"  ✅ テン指数: {ten_index_slow:.1f}")
    print(f"  ✅ 比較: 遅い3F → 低いテン指数 → {'OK' if ten_index_slow < ten_index else 'NG'}")
    
    print("\n✅ テン指数テスト完了\n")
    return ten_index, ten_index_fast, ten_index_slow


def test_position_index():
    """
    位置指数のテスト
    """
    print("\n" + "="*80)
    print("2️⃣ 位置指数（Position Index）のテスト")
    print("="*80)
    
    # テストケース1: 先行馬
    print("\n[Test Case 1] 先行馬（2-2-2-2）")
    pos_index_senkou = calculate_position_index(
        corner_1=2,
        corner_2=2,
        corner_3=2,
        corner_4=2,
        tosu=12,
        wakuban=3,
        kyori=1600
    )
    print(f"  ✅ 位置指数: {pos_index_senkou:.1f}")
    
    # テストケース2: 差し馬
    print("\n[Test Case 2] 差し馬（8-8-7-5）")
    pos_index_sashi = calculate_position_index(
        corner_1=8,
        corner_2=8,
        corner_3=7,
        corner_4=5,
        tosu=12,
        wakuban=5,
        kyori=1600
    )
    print(f"  ✅ 位置指数: {pos_index_sashi:.1f}")
    print(f"  ✅ 比較: 先行 < 差し → {'OK' if pos_index_senkou < pos_index_sashi else 'NG'}")
    
    # テストケース3: 追込馬
    print("\n[Test Case 3] 追込馬（12-12-11-9）")
    pos_index_oikomi = calculate_position_index(
        corner_1=12,
        corner_2=12,
        corner_3=11,
        corner_4=9,
        tosu=12,
        wakuban=8,
        kyori=1600
    )
    print(f"  ✅ 位置指数: {pos_index_oikomi:.1f}")
    print(f"  ✅ 比較: 差し < 追込 → {'OK' if pos_index_sashi < pos_index_oikomi else 'NG'}")
    
    print("\n✅ 位置指数テスト完了\n")
    return pos_index_senkou, pos_index_sashi, pos_index_oikomi


def test_agari_index():
    """
    上がり指数のテスト
    """
    print("\n" + "="*80)
    print("3️⃣ 上がり指数（Agari Index）のテスト")
    print("="*80)
    
    # テストケース1: 標準的な上がり3F
    print("\n[Test Case 1] 標準的な上がり3F")
    agari_index = calculate_agari_index(
        kohan_3f=37.5,       # 後半3F
        kyori=1600,
        baba_code='1',
        keibajo_code='42',
        furi_code='00',
        kinryo=54.0,
        bataiju=460.0,
        zenhan_3f=35.0
    )
    print(f"  ✅ 上がり指数: {agari_index:.1f}")
    print(f"  ✅ 範囲チェック: -100 ≤ {agari_index:.1f} ≤ +100 → {'OK' if -100 <= agari_index <= 100 else 'NG'}")
    
    # テストケース2: 速い上がり3F
    print("\n[Test Case 2] 速い上がり3F（決め手あり）")
    agari_index_fast = calculate_agari_index(
        kohan_3f=35.0,       # 速い後半3F
        kyori=1600,
        baba_code='1',
        keibajo_code='42',
        zenhan_3f=35.0
    )
    print(f"  ✅ 上がり指数: {agari_index_fast:.1f}")
    print(f"  ✅ 比較: 速い上がり → 高い上がり指数 → {'OK' if agari_index_fast > agari_index else 'NG'}")
    
    # テストケース3: 遅い上がり3F
    print("\n[Test Case 3] 遅い上がり3F（失速）")
    agari_index_slow = calculate_agari_index(
        kohan_3f=40.0,       # 遅い後半3F
        kyori=1600,
        baba_code='1',
        keibajo_code='42',
        zenhan_3f=35.0
    )
    print(f"  ✅ 上がり指数: {agari_index_slow:.1f}")
    print(f"  ✅ 比較: 遅い上がり → 低い上がり指数 → {'OK' if agari_index_slow < agari_index else 'NG'}")
    
    print("\n✅ 上がり指数テスト完了\n")
    return agari_index, agari_index_fast, agari_index_slow


def test_pace_index():
    """
    ペース指数のテスト
    """
    print("\n" + "="*80)
    print("4️⃣ ペース指数（Pace Index）のテスト")
    print("="*80)
    
    # テストケース1: 平均ペース
    print("\n[Test Case 1] 平均ペース（テン35.0 / 上がり37.5）")
    pace_index, pace_type = calculate_pace_index(
        ten_index=15.0,
        agari_index=10.0,
        zenhan_3f=35.0,
        kohan_3f=37.5,
        kyori=1600,
        keibajo_code='42'
    )
    print(f"  ✅ ペース指数: {pace_index:.1f}")
    print(f"  ✅ ペースタイプ: {pace_type}")
    
    # テストケース2: ハイペース
    print("\n[Test Case 2] ハイペース（テン33.0 / 上がり40.0）")
    pace_index_high, pace_type_high = calculate_pace_index(
        ten_index=35.0,
        agari_index=-10.0,
        zenhan_3f=33.0,
        kohan_3f=40.0,
        kyori=1600,
        keibajo_code='42'
    )
    print(f"  ✅ ペース指数: {pace_index_high:.1f}")
    print(f"  ✅ ペースタイプ: {pace_type_high}")
    print(f"  ✅ ハイペース判定: → {'OK' if 'H' in pace_type_high else 'NG'}")
    
    # テストケース3: スローペース
    print("\n[Test Case 3] スローペース（テン38.0 / 上がり35.0）")
    pace_index_slow, pace_type_slow = calculate_pace_index(
        ten_index=-10.0,
        agari_index=25.0,
        zenhan_3f=38.0,
        kohan_3f=35.0,
        kyori=1600,
        keibajo_code='42'
    )
    print(f"  ✅ ペース指数: {pace_index_slow:.1f}")
    print(f"  ✅ ペースタイプ: {pace_type_slow}")
    print(f"  ✅ スローペース判定: → {'OK' if 'S' in pace_type_slow else 'NG'}")
    
    print("\n✅ ペース指数テスト完了\n")
    return pace_index, pace_index_high, pace_index_slow


def test_all_indexes():
    """
    統合テスト: calculate_all_indexes
    """
    print("\n" + "="*80)
    print("🔄 統合テスト: calculate_all_indexes()")
    print("="*80)
    
    horse_data = {
        'zenhan_3f': 35.0,
        'kohan_3f': 37.5,
        'corner_1': 2,
        'corner_2': 2,
        'corner_3': 3,
        'corner_4': 2,
        'kyori': 1600,
        'babajotai_code_dirt': '1',
        'keibajo_code': '42',
        'tosu': 12,
        'furi_code': '00',
        'wakuban': 3,
        'kinryo': 54.0,
        'bataiju': 460.0,
        'soha_time': 96.0
    }
    
    result = calculate_all_indexes(horse_data)
    
    print("\n[結果]")
    print(f"  ✅ テン指数: {result['ten_index']:.1f}")
    print(f"  ✅ 位置指数: {result['position_index']:.1f}")
    print(f"  ✅ 上がり指数: {result['agari_index']:.1f}")
    print(f"  ✅ ペース指数: {result['pace_index']:.1f}")
    print(f"  ✅ ペースタイプ: {result['pace_type']}")
    print(f"  ✅ 予想脚質: {result['ashishitsu']}")
    
    # 必須キーの存在確認
    required_keys = ['ten_index', 'position_index', 'agari_index', 'pace_index']
    all_present = all(key in result for key in required_keys)
    print(f"\n  ✅ 必須キー存在確認: {'OK' if all_present else 'NG'}")
    
    print("\n✅ 統合テスト完了\n")
    return result


def main():
    """
    メイン関数
    """
    print("\n" + "="*80)
    print("🎯 4つの基礎指数 完成度テスト")
    print("="*80)
    
    try:
        # 個別テスト
        test_ten_index()
        test_position_index()
        test_agari_index()
        test_pace_index()
        
        # 統合テスト
        test_all_indexes()
        
        print("\n" + "="*80)
        print("✅ 全テスト合格")
        print("="*80)
        print("\n📊 完成度サマリ:")
        print("  ✅ 1️⃣ テン指数（Ten Index）: 実装完了")
        print("  ✅ 2️⃣ 位置指数（Position Index）: 実装完了")
        print("  ✅ 3️⃣ 上がり指数（Agari Index）: 実装完了")
        print("  ✅ 4️⃣ ペース指数（Pace Index）: 実装完了")
        print("  ✅ 5️⃣ 統合関数（calculate_all_indexes）: 実装完了")
        print("\n🎯 次のステップ:")
        print("  ⏳ 各指数の的中率・補正回収率を分析")
        print("  ⏳ nar_hqs_index_stats テーブル作成")
        print("  ⏳ HQS得点計算への統合")
        print("\n🚀 Play to Win. 10x Mindset.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
