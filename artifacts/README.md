# 共享研究产物

这里是所有 TFC 工作树共同指向的物理目录。`unified/library.sqlite3` 是日常场景、填补和预测数值的唯一入口；`unified/README.md` 给出查询方式。各研究的 `runs/<run_id>/` 保存冻结配置、状态、结果、失败记录和额外数组。

新的跨研究通用一维填补与点预测通过 TFC 的 `research_pipeline.shared_results.ensure_fill` / `ensure_prediction` 按完整合同先查后算，正式数值写入同一库；通用作业配置、状态和库内记录 ID 放 `unified/runs/<run_id>/`，不再复制这些数组。用 `scripts/tfc_data.py reuse` 加填补与预测合同 JSON 可只读查看是否能精确复用。旧导入来源没有新版方法合同的记录仍可读取，但不能仅凭同名方法自动当成新计算的缓存。专题候选轨迹、诊断及指标继续放所属研究的 run。

干净历史、原生缺失和模型默认处理的对照预测使用同一库的 `baseline_records`；新入口为 `ensure_baseline`，只读查询为 `tfc_data.py reference`。通用 run 支持按相同配置恢复，成功后的任务记录指向库内来源，不复制预测数值。预测反馈的新输入可由 TFC 的 `forecast_feedback.shared_scene.load_shared_scene(scene_id)` 直接从统一库读取；旧 V0.x 的 NPZ 和配置仍用于原协议追溯。

统一库还支持与一维窗口分开的表格场景、整表填补和绑定预测。通过 TFC 的 `Library.put_table_scene` / `get_table_fill` / `get_table_prediction` 查询，或用 `scripts/tfc_data.py table-scenes` 与 `table` 导出普通 CSV；旧 Eval CSV 仍直接留在 `legacy_eval/`。

- `missing_imputation_forecast/`：旧 Stage 1/2 正式产物。
- `work1_vnext/`：Work1 与候选扩充。
- [`forecast_feedback_imputation/`](forecast_feedback_imputation/README.md)：预测反馈实验的 39 个历史 run、缓存与日志；Stage1 输入共享引用，当前开发入口见该目录说明。
- `imputation_optimization_paper/`：论文实验、最新提交稿、独立方法包；当前维护入口见 [论文说明](imputation_optimization_paper/manuscript_iclr_20260920/README.md)。已清理旧修订稿与失效渲染脚本；旧稿指标表在 `derived/legacy_manuscript_review_20260923/`，独有过程素材保留在工作归档供追溯。
- 最新论文稿的两份框架图 ZIP 经逐字节确认相同，现只保留 `框架图_可编辑PPT与矢量文件.zip`；当前打包脚本也只生成这一份。历史打包脚本保留原流程。
- [`legacy_eval/`](legacy_eval/README.md)：旧 Eval 流程的原样 CSV 预测、结果表和图；包含旧路径对应表。
- `document_update_20260731/`：7 月报告的 DOCX 修订稿、构建脚本、参考材料与版式说明；一次性 PDF/逐页 PNG 渲染预览已清理。多个修订稿时间不同，按实际稿件名选择。
- `weekly_report_20260914/`：9 月周报与论文式说明的 DOCX；`_work/` 含 Markdown 源稿、构建脚本和正式配图，临时 PDF 与逐页渲染预览已清理。

当前结论与使用边界从 TFC 的 `docs/RESULTS.md` 进入。历史实现可以维护；已有运行记录保留其来源，新运行创建独立 run，结果按实际输入与预测合同发布到统一库。不为日常迁移重新计算文件哈希。
