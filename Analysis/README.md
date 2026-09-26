# Analysis：旧结果分析

现有代码入口包括 `run_batch_analysis.py`、`window_analysis.py`、`imputed_evaluation.py` 和 `plot_component_vs_smape.py`。从项目根目录使用 `D:/anaconda3/envs/TSFIA/python.exe -m Analysis.<模块名> --help` 核对当前脚本参数；基础 Python 环境缺少 `gluonts`。

历史预测 CSV 位于 `artifacts/legacy_eval/intermediate_predictions/`，默认分析输出位置为 `artifacts/legacy_eval/analysis/`。

已用 `chronos2/ETTh1_clean_short_prediction/` 的 20 份旧 CSV 做过实际读取检查。可从项目根目录运行：

```powershell
D:/anaconda3/envs/TSFIA/python.exe -m Analysis.window_analysis --model chronos2 prediction --prediction_dir artifacts/legacy_eval/intermediate_predictions/chronos2/ETTh1_clean_short_prediction --output artifacts/legacy_eval/analysis/ETTh1_clean_short_prediction.json
```

当前 `data/datasets/ori/` 可用于干净历史分析；旧 `data/datasets/Imputed/` 和旧 `results_analysis/` 均不存在，依赖它们的分析不能直接重跑。若研究需要这些数值，先查询 TFC 统一库；缺项才按明确的新运行合同生成。

旧说明中 `python -m analysis.*`、`batch_window_analysis.py` 等示例并不对应当前目录和文件，仅供追溯。完整旧说明保留在 [历史文档](../docs/history/Analysis_README_before_restructure_20260926.md)。
