# 数据目录

`datasets/ori/` 保存 27 份可直接读取的原始 CSV；其 `raw/` 下还有 180 份 Arrow、源 CSV 与元数据文件。这两层均保留，不能把 `raw/` 当成可随意删除的生成缓存。旧 `Intermediate_Predictions/` 的 8104 份 CSV 已原样移至 [`artifacts/legacy_eval/intermediate_predictions/`](../artifacts/legacy_eval/README.md)。维护中的评估、分析和绘图脚本已改用新路径；历史文档里的旧路径按迁移索引查找。当前场景、填补与预测从 `../artifacts/unified/library.sqlite3` 查询，新的研究结果写入各自 run 目录。新生成的缺失和填补 CSV 默认进入 `artifacts/legacy_eval/`，不写回原始数据目录。
