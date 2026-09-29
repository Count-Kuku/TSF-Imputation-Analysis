# Work1 历史产物与权重

当前入口：TFC `experiments/work1_vnext/README.md`、`STATE.json`、`WORK1_ARTIFACT_INDEX.md`。`p0` 至 `p5` 按原研究阶段保留输入、模型调用和面板结果；`weights/` 与 `vendor/` 保存依赖。旧配置与任务 JSON 直接引用这些位置，历史 run 可按原协议继续读取。

普通场景、填补和绑定预测已进入 `artifacts/unified/library.sqlite3`；六种逐值确认的基础填补另有 `series_*_work1_v1` 公共方法键。新研究先查共享库，Work1 特有的候选扩充、选择和诊断保存在自己的 run。共享映射见 TFC `docs/DATA_MIGRATION.md`。
