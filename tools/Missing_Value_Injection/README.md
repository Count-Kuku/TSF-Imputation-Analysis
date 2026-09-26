# Missing Value Injection（BM-only）

当前目录提供 BM（Block Missing）注空能力，支持两种模式：

- `stratified`：分层注空（默认），会参考多个 `max_context` 区间尽量平衡缺失率。
- `random`：全随机注空（保留旧行为）。

## 目录说明

```text
tools/Missing_Value_Injection/
├── BM.py
├── batch_bm_injection.py
├── inject_range_utils.py
└── README.md
```

## 环境准备

从本项目根目录运行，示例使用 `D:/anaconda3/envs/TSFIA/python.exe`。原始 CSV 在 `data/datasets/ori/`；新生成的缺失 CSV 默认放入 `artifacts/legacy_eval/generated_masks/`。研究正式运行可用 `--output_dir` 指定自己的独立 run。

新生成的掩码使用显式整数种子和稳定的场景偏移；旧掩码与当时的种子记录保留原样。不要把新掩码当成旧场景的同一实现结果。

## BM.py（单数据集入口）

查看帮助：

```bash
D:/anaconda3/envs/TSFIA/python.exe tools/Missing_Value_Injection/BM.py --help
```

默认参数：

- `--mode stratified`
- `--balanced_contexts 512,2048,2880,4096,8192`
- `--ratio_tolerance 0.1`
- `--repair_steps 20`

示例（默认 stratified）：

```bash
python tools/Missing_Value_Injection/BM.py --dataset Finland_Traffic_15T --missing_ratio 0.1 --term long --no_auto_term
```

示例（显式 random 模式）：

```bash
python tools/Missing_Value_Injection/BM.py --dataset Finland_Traffic_15T --missing_ratio 0.1 --term long --no_auto_term --mode random
```

示例（自定义平衡参数）：

```bash
python tools/Missing_Value_Injection/BM.py --dataset Finland_Traffic_15T --missing_ratio 0.1 --term long --no_auto_term --mode stratified --balanced_contexts 512,2048,2880,4096,8192 --ratio_tolerance 0.1 --repair_steps 20
```

输出路径：

```text
artifacts/legacy_eval/generated_masks/BM/BM_{ratio}/{dataset}_BM_length{block_length}_{ratio}_{term}.csv
```

## batch_bm_injection.py（批量入口）

查看帮助：

```bash
D:/anaconda3/envs/TSFIA/python.exe tools/Missing_Value_Injection/batch_bm_injection.py --help
```

示例（默认 stratified 批量）：

```bash
python tools/Missing_Value_Injection/batch_bm_injection.py --missing_ratios 0.1,0.2 --block_length 50 --mode stratified
```

## 区间缺失率报告脚本

新增脚本：`tools/context_missing_ratio_report.py`，用于按多个 `max_context` 计算同一文件的区间缺失率。

查看帮助：

```bash
python tools/context_missing_ratio_report.py --help
```

示例：

```bash
python tools/context_missing_ratio_report.py --dataset Finland_Traffic_15T --term long --ratio 010 --block_length 50 --contexts 512,2048,2880,4096,8192
```

输出列：

- `max_context`
- `start_index`
- `end_index`
- `injection_length`
- `missing_cells`
- `total_cells`
- `missing_ratio`

## 说明

- 注空时会跳过 `date/time/timestamp/item_id` 列。
- 所有缺失块均为固定长度 `block_length`，不使用补偿块。
- stratified 模式保留随机放置，避免规则化的机械分布。
