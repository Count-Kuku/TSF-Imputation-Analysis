# Eval：基础模型评估

本目录维护基础模型适配和旧 CSV 评估协议。新研究从 TFC 的独立研究目录调用基础实现，先查询统一库，普通结果发布到共享库，专题过程放自己的 run。

## 读取已有结果

从 My-TSF-Research 根目录运行，无需加载预测模型：

```powershell
D:/anaconda3/python.exe Eval/legacy_results.py --model chronos2 --dataset ETTh1 --term short --window 0 --include-values
```

不传 `--window` 时列出匹配批次。窗口读取返回 CSV 路径、日期和预测点，可定位汇总指标；缺失指标显示 `metrics_file: null`。检查包括窗口编号、指标表窗口数、列名、预测长度及有限数值。正式旧结果和旧路径对应见[产物索引](../artifacts/legacy_eval/README.md)。

## 文件与运行入口

| 文件 | 用途 |
|---|---|
| [run_eval.py](run_eval.py) | `clean` 干净序列、`single` 单个缺失文件、`batch` 批量评估 |
| [run_batch_eval.py](run_batch_eval.py) | 批量调度，支持 `--clean_only`、`--include_clean` 和已有输出检查 |
| [model_adapters.py](model_adapters.py) / [model_registry.py](model_registry.py) | 基础模型实现与注册 |
| [eval_pipeline.py](eval_pipeline.py) | 数据读取、窗口切分、指标评估 |
| [forecast_protocol.py](forecast_protocol.py) | 预测长度规则，只依赖 Pandas |
| [impute_dataset.py](impute_dataset.py) | 调用公共表格填补实现 |

旧协议运行环境为 `D:/anaconda3/envs/TSFIA/python.exe`。从项目根目录核对参数：

```powershell
D:/anaconda3/envs/TSFIA/python.exe Eval/run_eval.py clean --help
D:/anaconda3/envs/TSFIA/python.exe Eval/run_eval.py single --help
D:/anaconda3/envs/TSFIA/python.exe Eval/run_batch_eval.py --help
```

`single` 需要实际存在的 `--eval_data_path` 和非 `none` 的 `--imputation_method`。批量缺失输入用 `--missing_data_dir` 指定，原始数据根用 `--base_data_dir` 指定。新运行显式指定所属研究的 `--output_dir`、`--intermediate_dir`，需要填补文件时指定 `--imputed_data_dir`；避免覆盖历史结果。模型相关参数包括 `--model_name`、`--batch_size`、`--device`、`--num_samples`；Chronos2 另有 `--predict_batches_jointly`、`--torch_dtype`。实际选项以 CLI 为准。

当前原始数据在 `data/datasets/ori/`。旧 `data/datasets/BM/` 和 `data/datasets/Imputed/` 不存在；旧工具默认新增缺失和填补文件分别写入 `artifacts/legacy_eval/generated_masks/`、`imputed_datasets/`，首次生成前目录可以不存在。先从 TFC 统一库核对是否已有所需场景和结果，再决定是否生成。

旧批处理按“输出文件已存在”跳过任务，不能代替统一库的完整输入与预测合同匹配。更换配置时使用新 run，不用历史文件名判断结果等价。

## 历史窗口与预测长度

[model_properties.json](model_properties.json) 指定各适配器的历史长度上限：Chronos2 8192、TimesFM 2.5 4096、VisionTS++ 4000、Sundial 2880、TimesFM 2.0 与 Kairos 23M/50M 2048。适配器截取预测起点之前的末段历史；可用历史不足时按实际长度输入。同数据集、同预测长度的目标区间可以相同，各模型输入历史长度可以不同。

`forecast_protocol.py` 根据频率及 short/medium/long 计算 H，也可用 `--prediction_length` 显式指定。常见小时序列对应 48/480/720 步。原 CSV 只保存 `date,prediction`，当前配置不能单独证明每次历史运行都使用这一配置；精确复用还需要当次输入、权重/代码、随机种子及点值协议。

## 扩展模型

1. 在 `model_adapters.py` 实现 `predict(test_data_input)`，返回 GluonTS 预测对象。
2. 在 `model_registry.py` 注册；在 `run_eval.py`、`run_batch_eval.py` 等实际使用入口的模型选项中加入新名称。
3. 在 `model_properties.json` 登记历史长度，记录实际权重、参数、点值语义和运行版本；TFC 研究通过完整合同查询和发布。

模型依赖与本地缓存见[本机资产](../docs/LOCAL_ASSETS.md)和 [TSFIA.yml](../TSFIA.yml)。完整参数由当前 CLI 提供，重构前的重复说明可从 Git 历史查阅。
