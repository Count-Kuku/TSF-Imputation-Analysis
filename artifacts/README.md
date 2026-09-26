# 共享研究产物

这里是所有 TFC 工作树共同指向的物理目录。`unified/library.sqlite3` 是日常场景、填补和预测数值的唯一入口；`unified/README.md` 给出查询方式。各研究的 `runs/<run_id>/` 保存冻结配置、状态、结果、失败记录和额外数组。

统一库还支持与一维窗口分开的表格场景、整表填补和绑定预测。通过 TFC 的 `Library.put_table_scene` / `get_table_fill` / `get_table_prediction` 查询，或用 `scripts/tfc_data.py table-scenes` 与 `table` 导出普通 CSV；旧 Eval CSV 仍直接留在 `legacy_eval/`。

- `missing_imputation_forecast/`：旧 Stage 1/2 正式产物。
- `work1_vnext/`：Work1 与候选扩充。
- `forecast_feedback_imputation/`：预测反馈实验。
- `imputation_optimization_paper/`：论文实验、最新提交稿、独立方法包；当前维护入口见 [论文说明](imputation_optimization_paper/manuscript_iclr_20260920/README.md)。已清理旧修订稿与失效渲染脚本；旧稿指标表在 `derived/legacy_manuscript_review_20260923/`，独有过程素材保留在工作归档供追溯。
- [`legacy_eval/`](legacy_eval/README.md)：旧 Eval 流程的原样 CSV 预测、结果表和图；包含旧路径对应表。
- `document_update_20260731/`：7 月报告的 DOCX 修订稿、构建脚本、参考材料与版式说明；一次性 PDF/逐页 PNG 渲染预览已清理。多个修订稿时间不同，按实际稿件名选择。
- `weekly_report_20260914/`：9 月周报与论文式说明的 DOCX；`_work/` 含 Markdown 源稿、构建脚本和正式配图，临时 PDF 与逐页渲染预览已清理。

当前结论与使用边界从 TFC 的 `docs/RESULTS.md` 进入。历史实现可以维护；已有运行记录保留其来源，新运行创建独立 run，结果按实际输入与预测合同发布到统一库。不为日常迁移重新计算文件哈希。
