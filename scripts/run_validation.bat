@echo off
chcp 65001 >nul
cd /d E:\UmaData
echo 4指数予測精度検証を開始します...
echo.
echo データファイル: E:\UmaData\data-1768047611955.csv
echo 期間: 20231013 ~ 20251231
echo サンプリング率: 10%%
echo.
echo | python validate_each_index_accuracy_windows.py
echo.
echo 完了しました！結果ファイルを確認してください。
echo - index_accuracy_comparison.csv
echo - index_accuracy_comparison.json
echo.
pause
