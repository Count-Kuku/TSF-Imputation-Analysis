# Stage2 策略推荐产物

研究接手入口为 TFC 的 `experiments/stage2/README.md`。每个 `stage2_strategy_recommender_v0_*` 子目录是一份版本运行证据，可从 `protocol/`、`status/`、`tables/`、`reports/`、`audits/` 查找；`workspace_logs_20260926/` 保存旧工作日志。

普通场景、填补、绑定点预测与 clean 对照从 `artifacts/unified/library.sqlite3` 查询。集合、角色与原面板映射见 TFC 的 `config/stage2_mask_panels.json`。旧 NPZ 通过统一读取器恢复公共值，私有字段留在原文件。

候选回放、重复预测、选择器、预算与风险过程属于本研究的私有证据，保留各次运行。新实验使用独立 run，记录公共场景/结果 ID。
