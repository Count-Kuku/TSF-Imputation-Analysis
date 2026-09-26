# Eval：基础模型评估

维护中的入口是 `Eval/run_eval.py`（单项、批量、干净序列）和 `Eval/run_batch_eval.py`（批量调度）；模型适配在 `model_adapters.py`，注册在 `model_registry.py`。

预测长度与 short/medium/long 规则单独位于 `forecast_protocol.py`，只依赖 Pandas；TFC 的实验计划可直接读取，不会为计算长度导入 GluonTS 或加载模型。旧 `eval_pipeline` 仍导出相同接口。

从项目根目录使用 `D:/anaconda3/envs/TSFIA/python.exe` 运行，先执行 `--help` 检查参数。基础 Python 环境缺少 `gluonts`，不能作为本项目评估环境。实际运行前先在 TFC 统一库查询已有场景、填补和预测；旧批处理的“输出文件已存在”判断不等于完整预测合同匹配。

当前 `data/datasets/ori/` 存在；旧文档中的 `data/datasets/BM/`、`data/datasets/Imputed/` 不存在。缺失评估需要明确提供有效输入，不能直接照抄旧命令。旧预测 CSV 与结果位于 `artifacts/legacy_eval/`；新研究的正式结果放对应研究的独立 run。

BM 工具新生成的缺失 CSV 默认位于 `artifacts/legacy_eval/generated_masks/`，单项 Eval 使用 `--eval_data_path` 指向实际文件；批量 Eval 的 `--missing_data_dir` 指向该目录，原始干净 CSV 仍由 `--base_data_dir data/datasets` 读取。填补 CSV 默认进入 `artifacts/legacy_eval/imputed_datasets/`。这些目录在首次生成前可以不存在。

当时的完整参数示例保留在 [历史说明](../docs/history/Eval_README_before_restructure_20260926.md)；旧输出路径见 [迁移索引](../artifacts/legacy_eval/README.md)。
