# 共享研究产物

这里是所有 TFC 工作树共同指向的物理目录。`unified/library.sqlite3` 是日常场景、填补和预测数值的唯一入口；`unified/README.md` 给出查询方式。各研究的 `runs/<run_id>/` 保存冻结配置、状态、结果、失败记录和额外数组。

- `missing_imputation_forecast/`：旧 Stage 1/2 正式产物。
- `work1_vnext/`：Work1 与候选扩充。
- `forecast_feedback_imputation/`：预测反馈实验。
- `imputation_optimization_paper/`：论文实验、提交稿、独立方法包及工作稿归档。
- [`legacy_eval/`](legacy_eval/README.md)：旧 Eval 流程的原样 CSV 预测、结果表和图；包含旧路径对应表。

当前结论与使用边界从 TFC 的 `docs/RESULTS.md` 进入。历史实现可以维护；已有运行记录保留其来源，新运行创建独立 run，结果按实际输入与预测合同发布到统一库。不为日常迁移重新计算文件哈希。
