# My-TSF-Research

本项目保存时序预测基础模型适配、基础填补实现、原始数据和共享研究产物。研究协议、当前结论及统一数据读取入口在 TFC 项目；TFC 各工作树的 `artifacts` 都指向这里的同一物理目录。

## 从哪里开始

| 需求 | 位置 |
|---|---|
| 查询已有场景、填补与预测 | `artifacts/unified/library.sqlite3`；使用 TFC 的 `research_pipeline.unified_library.Library` 或 `scripts/tfc_data.py` |
| 查论文与正式运行结果 | [artifacts/README.md](artifacts/README.md)；先看各自状态和 run 报告 |
| 修改预测模型适配 | [Eval/README.md](Eval/README.md)、`Eval/model_adapters.py` |
| 修改基础填补实现 | [Imputation/README.md](Imputation/README.md)、`Imputation/imputation_methods.py` |
| 查看原始与旧中间数据 | [data/README.md](data/README.md)、[旧输出迁移索引](artifacts/legacy_eval/README.md) |
| 辨认本机模型和环境目录 | [本机资产索引](docs/LOCAL_ASSETS.md) |
| 追溯旧结果、分析及出图流程 | [旧输出迁移索引](artifacts/legacy_eval/README.md)、[Analysis/README.md](Analysis/README.md)、[Visualize/README.md](Visualize/README.md)、[窗口差异散点图](Visualize/gap_scatter/README.md) |

## 目录职责

- `Eval/`、`Imputation/`：基础模型与基础填补实现的维护源。历史实现可以继续修改；新运行记录实际使用的版本和方法身份。
- `data/datasets/ori/`：原始数据。旧流程的 CSV 预测、结果表和图片已移入 [`artifacts/legacy_eval/`](artifacts/legacy_eval/README.md)，文件格式不变。
- `artifacts/unified/`：日常数值的唯一入口。已有场景和结果按实际窗口、掩码、填补值、预测合同查询，不为补齐矩阵自动运行模型。
- `artifacts/<study>/runs/<run_id>/`：研究的配置、状态、指标、失败记录及额外数组。后续运行的图表也随对应 run 存放。

新研究的代码、测试和结论文档按研究主题放在 TFC；只在确实需要新增基础模型适配或基础填补实现时修改本项目。论文固定方法已可从 `artifacts/imputation_optimization_paper/method_exports/` 独立导出，不依赖本项目的预测器或旧输出目录。

BM 注入、模型评估和窗口分析分别从 [缺失生成工具](tools/Missing_Value_Injection/README.md)、[Eval](Eval/README.md) 和 [Analysis](Analysis/README.md) 进入。重构前的重复 README 已移出工作目录，原文仍可从 Git 历史查询。旧 `data/datasets/BM`、`data/datasets/Imputed`、`results_analysis` 当前不存在；已有公共结果先查统一库，历史 CSV 按产物索引定位。

## GitHub 仓库

日常开发和推送使用个人 fork 的 [`Count-Kuku/TSF-Imputation-Analysis`](https://github.com/Count-Kuku/TSF-Imputation-Analysis) 的 `main`。本地 `origin` 指向该 fork；`upstream` 指向[原仓库](https://github.com/Decadentvc/TSF-Imputation-Analysis)，仅用于查看和按需同步，不直接向其推送。当前 fork 的 `main` 采用原 `zyh_pic` 的研究状态，与原仓库 `main` 已分叉；以后引入上游改动时应先检查差异并测试。

GitHub 只保存 Git 跟踪的文件。`artifacts/unified/library.sqlite3` 等被忽略的共享研究数据仍保存在本机目录，不随 fork 的 `main` 推送。
