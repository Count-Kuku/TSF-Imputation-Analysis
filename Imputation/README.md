# Imputation Methods

本目录提供时间序列缺失值填补方法。主流程实际调用
`Eval/impute_dataset.py`，底层算法统一注册在 `Imputation/imputation_methods.py`。
旧的 `Imputation/impute.py` 只读取仓库中已不存在的 `window_###.csv + meta.json` 目录且没有外部调用，已移除。需要处理单个旧 Eval CSV 时使用 `Eval/impute_dataset.py`；按窗口严格区分历史与未来的研究应使用 TFC 对应研究入口。

TFC 旧 BM 脚本和 Work1 还有各自的填补实现。同名 knn、mice 或插值方法可能使用不同时间特征、列选择、参数和边界处理；向共享结果库登记时应按实际实现区分方法身份，不能仅凭名称复用。
TFC 的 `research_pipeline.shared_imputation.run_table` 为本目录十四种实际填补方法提供版本化方法键和参数合同。新表格研究可在同一统一库中按完整表格输入、方法合同复用填补和绑定预测；旧 Eval CSV 不会自动成为这种新场景。

## 接口约定

每个填补函数遵循同一接口：

```python
method(df: pd.DataFrame, data_cols: list, ...) -> pd.DataFrame
```

- `df`：包含缺失值的完整数据表，时间列通常已被设为 index。
- `data_cols`：需要填补的数值列。
- 返回值：填补后的 `DataFrame`，保留原 index 和列名。
- 随机方法支持 `random_seed` 参数，默认 `42`。

`Eval/impute_dataset.py` 会自动读取 CSV、识别时间列、调用算法；单独运行时默认保存到：

```text
artifacts/legacy_eval/imputed_datasets/{missing_method}/{missing_method}_{ratio}/{input_stem}_{imputation}.csv
```

## 当前方法

### 基础方法

- `none`：不填补，保留 NaN。
- `mean`：用列均值填补。
- `forward`：前向填补。
- `backward`：后向填补。
- `linear`：线性插值。
- `knn`：基于 KNNImputer 的跨列近邻填补。
- `mice`：基于 IterativeImputer 的 MICE 风格迭代填补。
- `pchip`：分段三次 Hermite 插值。
- `poly2`：二阶多项式插值。
- `poly3`：三阶多项式插值。
- `spline3`：三阶样条插值。

### 新增强单序列方法

- `kalman_struct`

  使用局部线性趋势状态空间模型和 Kalman smoother。状态包含 level 和
  slope，适合趋势明显、块状缺失较长的单变量序列。该实现只依赖
  NumPy/Pandas。

- `kalman_arima`

  先从初始插值序列估计稳定 AR(p) 系数，再用 AR 状态空间 Kalman
  smoother 填补缺失值。默认 `max_lag=3`，用于近似 ARIMA 动态。该实现只
  依赖 NumPy/Pandas。

- `gp_rbf`

  使用一维时间索引上的 RBF Gaussian Process 填补缺失点。长序列会抽取不
  超过 `max_train_points=512` 个观测点以控制矩阵求解开销；抽样由
  `random_seed` 控制，默认 `42`。该实现只依赖 NumPy/Pandas。

- `saits`

  使用 PyPOTS 中的 SAITS 自注意力填补模型。为了保持单序列设定，当前实现
  逐列训练和填补，不使用跨列信息。需要额外安装：

  ```bash
  python -m pip install pypots
  ```

  默认参数偏轻量：`n_steps=96`、`epochs=10`、`batch_size=32`、`device="cpu"`。
  CPU 默认值用于保证固定 `random_seed` 时尽量可复现。大规模正式实验前建议
  根据数据集长度和 GPU 情况调大 `epochs`，如显式使用 CUDA，则还需要注意
  PyTorch/CuBLAS 的确定性设置。

## 使用示例

以下示例以先运行 `tools/Missing_Value_Injection/BM.py` 生成对应缺失 CSV 为前提；目前该生成目录尚不存在，不会为了补齐实验矩阵自动生成。

单文件填补：

```bash
python Eval/impute_dataset.py \
  --eval_data_path artifacts/legacy_eval/generated_masks/BM/BM_010/ETTh1_BM_length50_010_short.csv \
  --imputation_method kalman_struct \
  --base_output_dir artifacts/legacy_eval/imputed_datasets
```

带随机种子：

```bash
python Eval/impute_dataset.py \
  --eval_data_path artifacts/legacy_eval/generated_masks/BM/BM_010/ETTh1_BM_length50_010_short.csv \
  --imputation_method gp_rbf \
  --random_seed 42
```

批量评估时直接传入新方法：

```bash
python Eval/run_batch_eval.py \
  --model chronos2 \
  --dataset ETTh1 \
  --method BM \
  --terms short \
  --missing_ratios 0.10 \
  --imputation_methods mean,forward,backward,linear,knn,mice,pchip,poly2,poly3,spline3,kalman_struct,kalman_arima,gp_rbf,saits \
  --random_seed 42
```

`input_stem` 保留输入文件的完整主文件名（包括 `length50` 等窗口标记），避免不同窗口文件覆盖同一输出。

## 依赖说明

- 必需：`numpy`、`pandas`。
- `knn` / `mice`：需要 `scikit-learn`。
- `pchip` / `poly2` / `poly3` / `spline3`：插值失败时明确报错，不再把线性结果标为原方法；旧产物仍按当时实现解释。
- SAITS：需要 `pypots`，通常也会依赖 `torch`。

当前实现对缺失依赖采用显式处理：`knn` / `mice` 在缺少 scikit-learn 时会抛出安装提示；
`saits` 在缺少 PyPOTS 时会抛出安装提示。若当前系统用户目录不可写，`saits`
会把 PyPOTS 的生态配置目录临时指向当前工作目录下的 `.pypots_home`。
