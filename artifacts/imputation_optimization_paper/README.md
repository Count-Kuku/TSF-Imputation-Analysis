# 面向预测的填补优化研究产物

当前入口：TFC `experiments/imputation_optimization/README.md`、`experiments/imputation_optimization/METHOD.md`。`CURRENT_*.json` 指向各专题当前运行；`runs/<run_id>/` 存配置、状态、候选、指标与失败。`method_exports/` 是可单独迁出的论文方法素材，`manuscript_iclr_20260920/` 为最新提交稿，`working_archive/` 保留仍需追溯的旧过程材料。

普通场景、基础填补和点预测从统一库读取；模型驱动填补的方法键已按生成模型分开。优化轨迹、相关性、变体与稿件素材属于本研究。恢复旧 run 先读相应 `CURRENT_*.json` 和 run 内状态；新运行创建独立目录，不覆盖已提交论文的证据。
