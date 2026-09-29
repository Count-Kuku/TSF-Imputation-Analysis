# Work1 产物与权重

研究接手入口为 TFC 的 `experiments/work1_vnext/README.md`，当前状态、正式报告、方法身份和产物索引均从该页进入。

`p0` 至 `p5` 保存各阶段的输入、manifest、任务、私有字段与失败记录；`weights/` 和 `vendor/` 保存模型依赖。旧 NPZ/JSON 使用 TFC 的 `research_pipeline.artifact_io` 读取，公共场景、填补和点预测从 `artifacts/unified/library.sqlite3` 获取。

新 run 按完整合同先查询已有结果；Work1 特有的候选扩充、选择与诊断仍放本研究。旧脚本可维护，修改后记录实际方法/模型版本。
