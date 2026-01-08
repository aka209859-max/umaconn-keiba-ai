@echo off
REM BASE_TIMES自動更新バッチスクリプト
REM CEOのローカル環境で実行してください

echo ================================================================================
echo config/base_times.py 自動更新スクリプト
echo ================================================================================
echo.

REM プロジェクトルートを設定
set PROJECT_ROOT=E:\UmaData\nar-analytics-python-v2
cd /d %PROJECT_ROOT%

REM 最新のresultファイルを探す
echo 📂 最新の結果ファイルを検索中...
for /f "delims=" %%i in ('dir /b /o-d output\base_times_result_*.txt 2^>nul') do (
    set LATEST_FILE=%%i
    goto :found
)

echo ❌ エラー: base_times_result_*.txt が見つかりません
pause
exit /b 1

:found
echo ✅ 最新の結果ファイル: %LATEST_FILE%
echo.

REM バックアップを作成
echo 💾 バックアップを作成中...
if exist config\base_times.py (
    for /f "tokens=2-4 delims=/ " %%a in ('date /t') do set DATE=%%c%%a%%b
    for /f "tokens=1-2 delims=: " %%a in ('time /t') do set TIME=%%a%%b
    set BACKUP_FILE=config\base_times_backup_%DATE%_%TIME%.py
    copy config\base_times.py "%BACKUP_FILE%" >nul
    echo ✅ バックアップ作成: %BACKUP_FILE%
) else (
    echo ⚠️ 既存のbase_times.pyが見つかりません（新規作成します）
)
echo.

REM Pythonスクリプトで更新
echo 🔧 BASE_TIMESを更新中...
python -c "import re; f=open('output\\%LATEST_FILE%', 'r', encoding='utf-8'); content=f.read(); f.close(); match=re.search(r'BASE_TIMES = \{.*?\n\}', content, re.DOTALL); base_times=match.group(0) if match else None; print('✅ BASE_TIMESを抽出しました' if base_times else '❌ エラー: BASE_TIMESが見つかりません'); header='''\"\"\"地方競馬全14競馬場の基準タイム設定（実データ版 - v13）\\n\\n✅ 競馬場コード修正完了（公式発表の正しいコード）\\n✅ 実データから算出（%LATEST_FILE%）\\n✅ 特殊期間フィルタ適用済み\\n✅ soha_time（実測走破タイム）追加\\n\\nデータ構造:\\n- 1200m未満: zenhan_3f = soha_time - kohan_3f（前半部分の実測値）\\n- 1200m: zenhan_3f = soha_time - kohan_3f（前半3F確定値）\\n- 1200m超: zenhan_3f = Ten3FEstimator（前半3Fペース推定）\\n\\n作成日: 2026-01-09\\nデータソース: nvd_ra, nvd_se (PostgreSQL)\\n\"\"\"\\n\\nfrom typing import Dict, Tuple, Optional\\nimport logging\\n\\nlogger = logging.getLogger(__name__)\\n\\n'''; footer='''\\n\\n# 競馬場名マッピング\\nKEIBAJO_NAMES = {\\n    '30': '門別',\\n    '35': '盛岡',\\n    '36': '水沢',\\n    '42': '浦和',\\n    '43': '船橋',\\n    '44': '大井',\\n    '45': '川崎',\\n    '46': '金沢',\\n    '47': '笠松',\\n    '48': '名古屋',\\n    '50': '園田',\\n    '51': '姫路',\\n    '54': '高知',\\n    '55': '佐賀'\\n}\\n\\ndef get_base_time(keibajo_code: str, kyori: int, time_type: str = 'soha_time') -> Optional[float]:\\n    \"\"\"指定された競馬場・距離の基準タイムを取得\"\"\"\\n    if keibajo_code not in BASE_TIMES:\\n        logger.warning(f\"競馬場コード {keibajo_code} が見つかりません\")\\n        return None\\n    if kyori not in BASE_TIMES[keibajo_code]:\\n        available_kyori = sorted(BASE_TIMES[keibajo_code].keys())\\n        closest_kyori = min(available_kyori, key=lambda x: abs(x - kyori))\\n        logger.warning(f\"距離 {kyori}m が見つかりません。最も近い距離 {closest_kyori}m を使用します\")\\n        kyori = closest_kyori\\n    data = BASE_TIMES[keibajo_code][kyori]\\n    if time_type not in data:\\n        logger.warning(f\"タイムタイプ {time_type} が見つかりません\")\\n        return None\\n    return data[time_type]\\n'''; out=open('config\\base_times.py', 'w', encoding='utf-8'); out.write(header + base_times + footer); out.close(); print('✅ config/base_times.py を更新しました')" 2>nul

if %ERRORLEVEL% NEQ 0 (
    echo ❌ エラー: 更新に失敗しました
    pause
    exit /b 1
)

echo.
echo 動作確認中...
python -c "from config.base_times import BASE_TIMES; print(f'✅ BASE_TIMES読込成功'); print(f'   競馬場数: {len(BASE_TIMES)}'); print(f'   大井1200m: {BASE_TIMES[\"44\"][1200]}')" 2>nul

if %ERRORLEVEL% NEQ 0 (
    echo ❌ エラー: 動作確認に失敗しました
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo ✅ 更新完了！
echo ================================================================================
echo.
echo 次のステップ:
echo   python scripts\collect_index_stats.py
echo.
pause
