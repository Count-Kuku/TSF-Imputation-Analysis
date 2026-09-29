# Analysis：窗口与旧结果分析

从 My-TSF-Research 根目录使用 `D:/anaconda3/envs/TSFIA/python.exe`。原始数据位于 `data/datasets/ori/`，旧预测位于 `artifacts/legacy_eval/intermediate_predictions/<model>/`。新研究的分析输出放自己的 `artifacts/<study>/runs/<run_id>/`。

## 当前入口

| 模块 | 用途 |
|---|---|
| [window_analysis.py](window_analysis.py) | `prediction` 分析预测窗口，`history` 分析干净历史窗口 |
| [run_batch_analysis.py](run_batch_analysis.py) | 按模型、数据集、期限批量分析；支持 `--prediction_only`、`--history_only`、`--clean_only` |
| [imputed_evaluation.py](imputed_evaluation.py) | 填补值与原始数据之间的误差 |
| [plot_component_vs_smape.py](plot_component_vs_smape.py) | 结构分量与预测误差的分析图 |
| [metrics.py](metrics.py) | STL 趋势强度、趋势线性度、季节强度、季节相关性、残差一阶自相关、谱特征 |

核对当前参数：

```powershell
D:/anaconda3/envs/TSFIA/python.exe -m Analysis.window_analysis --help
D:/anaconda3/envs/TSFIA/python.exe -m Analysis.run_batch_analysis --help
```

读取已有预测并生成窗口特征的示例（会写出分析 JSON，不运行预测模型）：

```powershell
D:/anaconda3/envs/TSFIA/python.exe -m Analysis.window_analysis --model chronos2 prediction --prediction_dir artifacts/legacy_eval/intermediate_predictions/chronos2/ETTh1_clean_short_prediction --output artifacts/legacy_eval/analysis/ETTh1_clean_short_prediction.json
```

这组历史输入包含 20 个预测窗口，重构期间已实际读取验证。分析干净历史时使用 `--model chronos2 history --dataset ETTh1 --term short`，模型历史长度取 `Eval/model_properties.json`。显式 `--output` 选择所属研究的输出文件；默认分析位置为 `artifacts/legacy_eval/analysis/`。

输出 JSON 包含元信息、窗口结果与汇总；指标实现以 `metrics.py` 为准。原数据属性由 `data/datasets/dataset_properties.json` 提供，包含周期等信息；STL 分析需要足够的有效历史。

旧 `data/datasets/Imputed/` 与 `results_analysis/` 不存在。需要填补历史时先查询 TFC 统一库，缺项才按明确的新运行合同生成。`Analysis` 是实际包名，批处理入口为 `run_batch_analysis.py`；当前代码没有旧说明中的 `analysis.batch_window_analysis`。旧结果定位见[产物索引](../artifacts/legacy_eval/README.md)，完整旧说明可从 Git 历史查阅。
