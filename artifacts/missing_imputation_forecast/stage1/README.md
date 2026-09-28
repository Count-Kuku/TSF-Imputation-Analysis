# Stage1 历史产物

当前研究导航见 TFC `experiments/stage1/README.md`。共有场景、填补和常规预测从 `artifacts/unified/library.sqlite3` 查询；8,100 个正式场景已登记生成合同。用 `tfc_data.py library --collection stage1 --scenario-key <masks.csv中的mask_id>` 可以按可读键查找。

`stage1_missing_v0_9/` 保存掩码清单与时间轴；`stage1_impute_forecast_v0_1/`、`stage1_model_self_impute_v0_1/` 和 `stage1_clean_forecast_v0_1/` 保留原填补/预测、状态与失败；`stage1_analysis_v0_*/` 是独立分析。旧运行器与 Stage2 仍读取这些路径，新工作从统一库先查后算。
