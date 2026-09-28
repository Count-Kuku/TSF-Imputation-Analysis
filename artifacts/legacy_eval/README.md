# 旧 Eval 结果与路径迁移索引

2026-09-28 逐目录清点：`intermediate_predictions/` 有 484 个 clean 预测批次、8,104 份逐窗口 CSV；458 个批次可找到汇总指标 CSV，26 个批次只有预测 CSV。已有指标表中的窗口数与相应 CSV 数一致。用 `D:/anaconda3/python.exe Eval/legacy_results.py --model <模型> --dataset <数据集> --term <short|medium|long> --window <序号>` 查询原文件与时间范围；追加 `--include-values` 可直接在 JSON 中读取该窗口的日期与预测值，不需加载预测模型。缺指标的批次保留原预测并明确显示 `metrics_file: null`。旧 Eval 的完整输入窗口及模型运行合同不足以核定跨研究精确复用，所以这些 CSV 仍按研究私有历史产物读取，不强行并入共享预测缓存。

这些文件是旧评估流程生成的原样 CSV 和图像。2026-09-26 只移动目录并更新读取路径，没有重新计算预测、指标或文件哈希。数据仍按模型和原文件名浏览。

| 旧路径（项目根目录下） | 当前位置 | 文件数 |
|---|---|---:|
| `data/Intermediate_Predictions/` | `artifacts/legacy_eval/intermediate_predictions/` | 8104 |
| `results/` | `artifacts/legacy_eval/results/` | 459（含说明文件） |
| `draw/outputs_by_dataset/` | `artifacts/legacy_eval/figures_by_dataset/` | 356 |
| `draw/outputs_by_model/` | `artifacts/legacy_eval/figures_by_model/` | 70 |

原路径下的相对文件名不变。例如旧 `results/chronos2/impute/x.csv` 现在是 `artifacts/legacy_eval/results/chronos2/impute/x.csv`。评估、分析和绘图脚本的默认路径已同步修改；调用时仍可通过命令行显式指定其他目录。旧 results_analysis/ 目录及分量权重文件在整理时不存在，没有可迁移的数据；相关脚本后续输出统一放在 artifacts/legacy_eval/analysis/。

这批旧结果保留为可直接打开的文件；跨研究查找实际场景、填补和预测，仍从 [`artifacts/unified/`](../unified/README.md) 的查询入口进行。旧 Eval 工具今后按需新生成的缺失 CSV、填补 CSV 和分析结果分别放在 `generated_masks/`、`imputed_datasets/` 和 `analysis/`，这些目录在首次运行前不存在。新的研究运行输出请放入对应研究的 `runs/<run_id>/`，避免继续扩展本旧流程目录。
