"""
RGS 1.0 計算エンジン 単体テスト

テスト項目:
1. 基本計算の正確性
2. 境界値（edge cases）の処理
3. エラーハンドリング
4. 小サンプル補正の動作確認

実行方法:
    cd /home/user/webapp/nar-ai-yoso
    python3 -m pytest tests/test_rgs_calculator.py -v
"""

import sys
sys.path.append('/home/user/webapp/nar-ai-yoso')

import pytest
import math
from core.rgs_calculator import (
    calculate_rgs,
    interpret_rgs,
    calculate_rgs_for_factor,
    calculate_rgs_for_horse
)


class TestRGSCalculation:
    """RGS基本計算のテスト"""
    
    def test_high_profitability_factor(self):
        """高収益ファクター（回収率110%）"""
        rgs = calculate_rgs(
            cntWin=300,
            cntPlace=500,
            adjWinRet=110.0,
            adjPlaceRet=105.0
        )
        assert 7.0 <= rgs <= 8.5, f"RGS should be around 7-8.5, got {rgs}"
        
    def test_neutral_factor(self):
        """中立ファクター（回収率80%）"""
        rgs = calculate_rgs(
            cntWin=200,
            cntPlace=400,
            adjWinRet=80.0,
            adjPlaceRet=80.0
        )
        assert -0.5 <= rgs <= 0.5, f"RGS should be around 0, got {rgs}"
    
    def test_low_profitability_factor(self):
        """低収益ファクター（回収率60%）"""
        rgs = calculate_rgs(
            cntWin=150,
            cntPlace=300,
            adjWinRet=60.0,
            adjPlaceRet=65.0
        )
        assert -6.5 <= rgs <= -4.5, f"RGS should be around -5 to -6, got {rgs}"
    
    def test_small_sample_correction(self):
        """小サンプル補正（信頼度低下）"""
        # 大サンプル
        rgs_large = calculate_rgs(
            cntWin=300,
            cntPlace=500,
            adjWinRet=110.0,
            adjPlaceRet=105.0
        )
        
        # 小サンプル
        rgs_small = calculate_rgs(
            cntWin=10,
            cntPlace=20,
            adjWinRet=110.0,
            adjPlaceRet=105.0
        )
        
        assert rgs_small < rgs_large, "Small sample RGS should be lower than large sample"
        assert 1.5 <= rgs_small <= 3.5, f"Small sample RGS should be around 2-3, got {rgs_small}"


class TestRGSEdgeCases:
    """境界値テスト"""
    
    def test_zero_data(self):
        """データ数ゼロの場合"""
        rgs = calculate_rgs(
            cntWin=0,
            cntPlace=0,
            adjWinRet=100.0,
            adjPlaceRet=100.0
        )
        assert rgs == 0.0, "RGS should be 0 when no data"
    
    def test_extreme_high_return(self):
        """極端に高い回収率（200%）"""
        rgs = calculate_rgs(
            cntWin=500,
            cntPlace=800,
            adjWinRet=200.0,
            adjPlaceRet=180.0
        )
        assert 9.0 <= rgs <= 10.0, f"RGS should be close to +10, got {rgs}"
    
    def test_extreme_low_return(self):
        """極端に低い回収率（20%）"""
        rgs = calculate_rgs(
            cntWin=500,
            cntPlace=800,
            adjWinRet=20.0,
            adjPlaceRet=30.0
        )
        assert -10.0 <= rgs <= -9.0, f"RGS should be close to -10, got {rgs}"
    
    def test_only_win_data(self):
        """単勝データのみ"""
        rgs = calculate_rgs(
            cntWin=300,
            cntPlace=0,
            adjWinRet=110.0,
            adjPlaceRet=0.0
        )
        assert rgs != 0.0, "RGS should not be 0 with only win data"
    
    def test_only_place_data(self):
        """複勝データのみ"""
        rgs = calculate_rgs(
            cntWin=0,
            cntPlace=500,
            adjWinRet=0.0,
            adjPlaceRet=105.0
        )
        assert rgs != 0.0, "RGS should not be 0 with only place data"


class TestRGSInterpretation:
    """RGS解釈テスト"""
    
    def test_strong_recommendation(self):
        """強く推奨（RGS ≥ +7.0）"""
        result = interpret_rgs(7.5)
        assert result['category'] == 'strong'
        assert result['label'] == '強く推奨'
        assert result['estimated_return'] == 110.0
    
    def test_recommended(self):
        """推奨（RGS ≥ +2.0）"""
        result = interpret_rgs(3.0)
        assert result['category'] == 'recommended'
        assert result['label'] == '推奨'
        assert result['estimated_return'] == 90.0
    
    def test_neutral(self):
        """中立（-2.0 < RGS < +2.0）"""
        result = interpret_rgs(0.5)
        assert result['category'] == 'neutral'
        assert result['label'] == '中立'
        assert result['estimated_return'] == 80.0
    
    def test_not_recommended(self):
        """非推奨（RGS ≤ -2.0）"""
        result = interpret_rgs(-3.0)
        assert result['category'] == 'not_recommended'
        assert result['label'] == '非推奨'
        assert result['estimated_return'] == 70.0


class TestRGSForFactor:
    """ファクター統計データからのRGS計算テスト"""
    
    def test_calculate_rgs_for_factor(self):
        """ファクター統計データからRGS計算"""
        factor_stats = {
            'cntWin': 300,
            'cntPlace': 500,
            'adjWinRet': 110.0,
            'adjPlaceRet': 105.0
        }
        
        result = calculate_rgs_for_factor(factor_stats)
        
        assert 'rgs_score' in result
        assert 'interpretation' in result
        assert 'confidence' in result
        assert 'data_count' in result
        
        assert 7.0 <= result['rgs_score'] <= 8.5
        assert result['confidence'] > 0.5
        assert result['data_count'] == 800
    
    def test_low_confidence_factor(self):
        """低信頼度ファクター"""
        factor_stats = {
            'cntWin': 5,
            'cntPlace': 10,
            'adjWinRet': 120.0,
            'adjPlaceRet': 110.0
        }
        
        result = calculate_rgs_for_factor(factor_stats)
        
        assert result['confidence'] < 0.3, "Confidence should be low for small samples"
        assert result['data_count'] == 15


class TestRGSForHorse:
    """馬全体のRGS計算テスト"""
    
    def test_calculate_rgs_for_horse(self):
        """馬の全ファクターからRGS総合スコア計算"""
        horse_factors_stats = [
            {
                'factor_id': 'F17',
                'factor_name': '馬齢',
                'cntWin': 300,
                'cntPlace': 500,
                'adjWinRet': 110.0,
                'adjPlaceRet': 105.0
            },
            {
                'factor_id': 'F22',
                'factor_name': '前走タイム差',
                'cntWin': 200,
                'cntPlace': 400,
                'adjWinRet': 95.0,
                'adjPlaceRet': 90.0
            }
        ]
        
        result = calculate_rgs_for_horse(horse_factors_stats)
        
        assert 'total_rgs' in result
        assert 'average_rgs' in result
        assert 'factor_scores' in result
        assert 'recommendation' in result
        
        assert len(result['factor_scores']) == 2
        assert result['total_rgs'] > 0


class TestRGSMathematicalProperties:
    """RGS数学的性質のテスト"""
    
    def test_rgs_range(self):
        """RGSは常に-10〜+10の範囲内"""
        test_cases = [
            (1000, 2000, 200.0, 180.0),  # 極端な高回収率
            (1000, 2000, 10.0, 15.0),    # 極端な低回収率
            (10, 20, 150.0, 140.0),      # 小サンプル高回収率
        ]
        
        for cntWin, cntPlace, adjWinRet, adjPlaceRet in test_cases:
            rgs = calculate_rgs(cntWin, cntPlace, adjWinRet, adjPlaceRet)
            assert -10.0 <= rgs <= 10.0, f"RGS {rgs} is out of range [-10, +10]"
    
    def test_rgs_monotonicity(self):
        """回収率が高いほどRGSも高い（単調性）"""
        rgs_60 = calculate_rgs(300, 500, 60.0, 65.0)
        rgs_80 = calculate_rgs(300, 500, 80.0, 80.0)
        rgs_100 = calculate_rgs(300, 500, 100.0, 95.0)
        rgs_120 = calculate_rgs(300, 500, 120.0, 115.0)
        
        assert rgs_60 < rgs_80 < rgs_100 < rgs_120, "RGS should increase with return rate"


# pytest実行用
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
