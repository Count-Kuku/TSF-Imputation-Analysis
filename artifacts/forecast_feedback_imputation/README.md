# 预测反馈填补研究产物

TFC 研究入口：`D:/Projects/PycharmProjects/TFC/experiments/forecast_feedback/README.md`；目录和数据来源见同目录 `DATA_LAYOUT.md`。本目录是共享 `artifacts` 下的单一物理副本，各 TFC 工作树的 `artifacts` 均指向它。

- `runs/<run_id>/`：39 个历史运行目录，含正式结果、smoke/pilot、恢复运行和汇总；按各自 `status.json`、`audit.json`、配置和来源判断用途，不按目录名直接合并。
- `cache/`：历史运行的冻结快照、场景/基线清单与预检记录。
- `logs/`：历史作业状态和日志。
- `../missing_imputation_forecast/stage1/`：多研究共用的场景 NPZ、manifest、split lock 与基础填补缓存；本研究只引用，不复制。
- `../unified/library.sqlite3`：日常查询实际场景、填补、预测的统一数值入口。

已完成的最近比较：`runs/quantile_full_comparison_v083_20260914_01/` 是 12 数据集 240 场景的汇总；`runs/other_imputers_comparison_v084_20260914_01/` 是 11 数据集 220 场景、21 标签的比较。新研究运行创建新的独立 run，并通过 TFC 的 `Library` 发布可复用数值；历史配置和路径保留原样供追溯。
