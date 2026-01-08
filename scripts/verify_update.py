#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
スクリプト更新確認ツール
"""

import os
import sys

script_path = os.path.join(os.path.dirname(__file__), 'collect_index_stats.py')

print("=" * 80)
print("collect_index_stats.py の確認")
print("=" * 80)
print(f"\nファイルパス: {script_path}")
print(f"存在確認: {os.path.exists(script_path)}")

if os.path.exists(script_path):
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 重要なキーワードをチェック
    checks = {
        'import logging': 'import logging' in content,
        'logger = logging.getLogger': 'logger = logging.getLogger' in content,
        'error_msg = f"""': 'error_msg = f"""' in content,
        '❌ データ挿入エラー': '❌ データ挿入エラー' in content,
    }
    
    print("\n更新確認:")
    all_ok = True
    for key, result in checks.items():
        status = "✅" if result else "❌"
        print(f"  {status} {key}: {result}")
        if not result:
            all_ok = False
    
    if all_ok:
        print("\n✅ 最新版に更新されています！")
        sys.exit(0)
    else:
        print("\n❌ 古いバージョンです。以下を実行してください:")
        print("  curl -o scripts\\collect_index_stats.py https://raw.githubusercontent.com/aka209859-max/umaconn-keiba-ai/main/scripts/collect_index_stats.py")
        sys.exit(1)
else:
    print("\n❌ ファイルが見つかりません")
    sys.exit(1)
