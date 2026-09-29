# 统一缺失、填补与预测数据池

**日常数值入口是 `library.sqlite3`。** 由 TFC 的 `research_pipeline.unified_library.Library` 或 `scripts/tfc_data.py` 查询；TFC 工作树指向本目录的同一物理副本。

```powershell
D:/anaconda3/python.exe D:/Projects/PycharmProjects/TFC/scripts/tfc_data.py library
D:/anaconda3/python.exe D:/Projects/PycharmProjects/TFC/scripts/tfc_data.py scenes --collection stage1 --dataset ETTh1 --limit 10
D:/anaconda3/python.exe D:/Projects/PycharmProjects/TFC/scripts/tfc_data.py library --scene <scene_id> --method linear --model chronos2 --horizon 48
```

## 查询与发布

- `library` / `scenes` 浏览已有值和实时覆盖；`reuse` 按方法及完整预测合同判断是否能跳过计算。`coverage --output` 和 `export` 可按需导出普通 CSV。
- 场景按实际窗口和掩码识别，可用 `--pattern-key`、`--seed`、`--target-ratio` 筛选。新模式使用 `shared_scenarios.ensure_scenario`，显式记录模式版本、比例、参数与种子。
- 公共填补和预测使用 `shared_results.ensure_fill` / `ensure_prediction`；对照使用 `ensure_baseline`。接口在共享锁内查询、按需计算并发布，预测绑定实际填补值。
- 精确复用需要匹配实际输入、方法实现与参数、模型/权重和代码版本、H、种子、批量设置和点值定义。只有方法名相同不能作为缓存命中依据；缺项不自动补齐实验矩阵。
- `clean`、`native_nan`、`model_default` 是独立对照，通过 `reference` 查询，不计作外部填补方法。
- 已登记的 `series_*_work1_v1` 方法可由 `reuse` 自动生成方法合同，需要周期时传 `--period`。旧来源合同不完整时仍可浏览，不自动作为新任务的精确缓存。

## 文件归属

`runs/<run_id>/` 保存公共作业配置、状态、失败和库内记录 ID。专题候选、优化轨迹、选择器、指标与独有数组放 `artifacts/<study>/runs/<run_id>/`。读取旧 NPZ/JSON 使用 TFC 的 `research_pipeline.artifact_io`；公共字段从本库还原，原文件保留私有字段。Work1 正式入口发布成功后自动将任务点预测改为库引用。

旧 Eval 的原样预测 CSV 从 [legacy_eval/](../legacy_eval/README.md) 读取，其逐次输入和模型合同仍有缺项，不强行当作本库的精确缓存。

## 详细说明

维护入口集中在 TFC，避免两仓库重复维护长篇规则：

- `UNIFIED_DATA.md`：数据读取、导出、旧产物读取器及恢复命令。
- `DATA_ACCESS.md`：物理路径配置与工作树接入。
- `docs/ADDING_STUDY.md`：新研究、方法和模式的接入示例。
- 根 `README.md`：两个项目共同的架构总览与研究入口。
- `experiments/<study>/README.md`：具体研究的状态、正式结果、数据集合与使用限制。
