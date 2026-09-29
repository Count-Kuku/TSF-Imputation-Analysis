# 共享产物目录

这里是所有 TFC 工作树共用的物理产物根。总体职责、共享/私有规则和研究入口统一见 TFC 的根 `README.md`。

| 内容 | 入口 |
|---|---|
| 公共场景、填补、预测与对照 | [unified](unified/README.md)；日常唯一数值入口是 `library.sqlite3` |
| Stage1 / Stage2 | `missing_imputation_forecast/stage1/`、`stage2/` |
| Work1 | [work1_vnext](work1_vnext/README.md) |
| 预测反馈 | [forecast_feedback_imputation](forecast_feedback_imputation/README.md) |
| 填补优化及论文实验 | [imputation_optimization_paper](imputation_optimization_paper/README.md) |
| 最新论文、可编辑图与构建源码 | [论文交付说明](imputation_optimization_paper/manuscript_iclr_20260920/README.md) |
| 旧 Eval 逐窗口 CSV、指标及图 | [legacy_eval](legacy_eval/README.md) |
| 7 月报告源稿、修订与构建素材 | `document_update_20260731/` |
| 9 月周报 Word、源稿与配图 | `weekly_report_20260914/` |

公共作业的 `unified/runs/<run_id>/` 保存配置、状态、失败和公共记录 ID。专题轨迹、候选、指标与私有数组放所属研究的 `runs/<run_id>/`；旧研究的阶段/版本目录沿用其原布局。具体状态与结论从 TFC 对应研究 README 进入。
