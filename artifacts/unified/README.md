# 统一缺失、填补与预测数据池

场景生成合同可由 TFC 的 `research_pipeline.shared_scenarios.ensure_scenario` 登记和精确复用；`tfc_data.py scenes` 支持 `--pattern-key`、`--seed`、`--target-ratio` 筛选。现有 248,089 条研究场景归属全部已登记：Stage1 8,100 条、Work1 732 条、预测反馈别名 460 条、论文扩展 1,482 条、Stage2 正式面板 237,165 条及额外种子 150 条。已核对实际掩码与可确认的参数；论文扩展未记录的种子留空。相同数值数组由库去重保存。说明见 TFC 的 `docs/SCENARIO_CONTRACTS_20260928.md`。

**日常唯一数值入口：`library.sqlite3`。** 使用 TFC 的 `research_pipeline.unified_library.Library` 或 `scripts/tfc_data.py` 查询。场景由实际窗口和布尔掩码确定；同一场景可有多份来源记录，但当前填补和预测按既定优先级选择。新结果写入同一库，不为补齐方法矩阵自动运行模型。

```powershell
D:/anaconda3/python.exe D:/Projects/PycharmProjects/TFC/scripts/tfc_data.py library
D:/anaconda3/python.exe D:/Projects/PycharmProjects/TFC/scripts/tfc_data.py scenes --collection stage1 --dataset ETTh1 --limit 10
D:/anaconda3/python.exe D:/Projects/PycharmProjects/TFC/scripts/tfc_data.py library --scene <scene_id> --method linear --model chronos2 --horizon 48
```

无参数 `library` 显示实时原始记录数和来源集合；具体当前填补/预测请按场景和方法查询。要据此跳过模型调用，还须匹配实际填补值、模型、预测长度、点预测定义和完整运行合同。新写入在共享 `forecast_lock()` 内提交事务，预测必须绑定填补值 ID。

新研究只读检查精确复用时，用 `tfc_data.py reuse --scene <scene_id> --method <method_key> --fill-contract-file <fill_contract.json>`；预测再补 `--model`、`--horizon`、`--point-kind` 和 `--forecast-contract-file`。计算入口是 TFC 的 `research_pipeline.shared_results.ensure_fill` / `ensure_prediction`，普通点值写回本库。通用作业的 `runs/<run_id>/` 只保存配置、状态、来源及库内记录 ID；研究专用轨迹保存在所属研究 run。旧导入来源若没有新版 `method_contract`，仍可浏览与读取，但不会仅凭方法名自动成为新合同的缓存命中。

一批场景的实时覆盖用 `tfc_data.py coverage --collection <集合> --method <公共方法键> --limit <数量>` 查看；可追加 `--output <新CSV文件>` 保存当时的逐场景来源表。预测合同若因实际窗口和掩码而各不相同，用 `--forecast-contracts-file` 传入 `{场景ID: 完整合同}` JSON 映射，不能以一个场景的合同代表整批。

对照预测按 `clean`、`native_nan`、`model_default` 三种类型单独查询；不计作填补方法。可用 `tfc_data.py reference --scene <scene_id> --kind clean --model <model> --horizon <H> --point-kind P50 --contract-file <forecast_contract.json>` 只读检查，新计算使用 `ensure_baseline`。完整预测合同必须匹配，库里有同模型同长度的旧记录也不一定能跳过模型调用。

已登记的 `series_*_work1_v1` 公共方法查询可省略填补合同文件，必要时用 `--period` 指定原周期；例如 `tfc_data.py reuse --scene <scene_id> --method series_linear_work1_v1`。

预测反馈历史的 `linear`、`forward`、`backward`、`pchip` 也已逐值核实并接入相同公共方法键：新增 960 条填补来源、3,856 条绑定预测来源，数值数组数不变。`mean` 在 12/240 个场景与公共实现不同，未归并。细节见 TFC 的 `docs/FEEDBACK_SHARED_MIGRATION_20260928.md`。

2026-09-28 已将逐值核实的 Work1 P2/P5 基础填补 3,240 条及绑定预测 33,504 条登记到六个 `series_*_work1_v1` 公共方法键。原记录与预测合同保留，`arrays` 数量未增加。哪些方法通过或未通过核对、来源如何追溯，见 TFC 的 `docs/WORK1_SHARED_MIGRATION_20260928.md`。

论文参数实验的旧 `__generic` 方法键混合三种生成模型，已为 9,720 条填补及其绑定预测建立 `__generated_by_<model>` 专属键；原记录保留，数组数量仍未增加。旧键的多值组合由 `tfc_data.py library --scene ... --method ...` 的 `fill_ambiguous` 标出。细节见 TFC 的 `docs/PAPER_MODEL_METHOD_MIGRATION_20260928.md`。

Stage2 的 39 份面板和额外种子场景，以及 12 个版本的 251,775 条填补来源、302,235 条绑定点预测来源、1,351 条 clean 对照来源已逐值迁入。V0.119 的三次运行分别保留来源，共用 V0.118.2 的选中场景。分位数、配置、指标、候选回放与重复预测保留在各研究版本目录。面板归属与公共/私有边界见 TFC 的 `docs/STAGE2_MASK_PANEL_INVENTORY_20260928.md` 和 `docs/STAGE2_SHARED_RESULTS_MIGRATION_20260928.md`。

2026-09-15 的静态场景、方法与预测覆盖快照已清理，避免把过时计数当作实时结果。`completion.json`、`audit.json` 和 `import_corrections.json` 保留当时导入与核验的历史证据；其中的旧计数不是当前覆盖。需要新 CSV 时按需使用 TFC 的 `tfc_data.py export` 或 `coverage --output`。正式 NPZ、manifest、配置、指标和失败记录仍留在各自研究 run；本库用于日常数值检索与精确复用。

完整使用约定见 TFC 的 `UNIFIED_DATA.md`、`DATA_ACCESS.md`、`docs/RESULTS.md` 和 `docs/ADDING_STUDY.md`。
