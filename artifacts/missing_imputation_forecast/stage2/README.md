# Stage2 策略推荐历史产物

当前入口：TFC `experiments/stage2/STAGE2_HANDOFF.md`、`STAGE2_CURRENT_SYNTHESIS.md`、`STAGE2_EXPERIMENT_REGISTRY.md`。每个 `stage2_strategy_recommender_v0_*` 子目录代表一个历史版本的独立运行证据，可从 `protocol/`、`status/`、`tables/`、`reports/`、`audits/` 查找；`workspace_logs_20260926/` 是旧工作日志。

版本目录包含选择器、风险、预算与审计等研究私有结果。旧运行器和报告引用具体版本路径，因此保留原位置。可跨研究使用的基础场景、填补和常规预测从 `artifacts/unified/library.sqlite3` 查询；以后新运行使用独立 run 目录并引用库内场景与结果。

V0.107/V0.113 的 1,290 个基础及额外种子场景、V0.108/V0.114 的 19,350 条填补与绑定预测及 76 条 clean 对照已核实并迁入统一库。旧 NPZ 仍提供分位数、时间轴及恢复证据；其他面板与重复运行仍按版本保留，等待逐项区分公共结果和研究专用结果。映射及查询示例见 TFC `docs/STAGE2_SHARED_RESULTS_MIGRATION_20260928.md`。
