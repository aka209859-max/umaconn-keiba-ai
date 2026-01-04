@echo off
REM NAR AI予想システム - 実行バッチファイル
REM 
REM 使い方:
REM   1. このファイルをダブルクリック → 明日の予想を生成
REM   2. コマンドプロンプトで実行 → run_prediction.bat 20250105
REM
REM 出力先:
REM   E:\UmaData\nar-analytics-python\output\[日付]\

echo ========================================
echo NAR AI予想システム
echo ========================================
echo.

cd /d E:\UmaData\nar-analytics-python

if "%1"=="" (
    echo 明日の予想を生成します...
    python main.py
) else (
    echo %1 の予想を生成します...
    python main.py --date %1
)

echo.
echo ========================================
echo 処理完了
echo ========================================
pause
