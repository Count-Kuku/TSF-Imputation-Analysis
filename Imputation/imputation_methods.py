"""时间序列缺失值填补方法库.

提供多种填补算法。所有方法均接收 ``DataFrame`` 和待填补列名列表，
返回填补后的 ``DataFrame``。
"""

from __future__ import annotations

import os
import random
from pathlib import Path
from typing import Callable, Dict, Optional, Sequence

import numpy as np
import pandas as pd


DEFAULT_RANDOM_SEED = 42


def _finite_or_default(value: float, default: float) -> float:
    if np.isfinite(value) and value > 0:
        return float(value)
    return float(default)


def _initial_fill_array(values: Sequence[float]) -> np.ndarray:
    """Return a finite 1-D array used for model initialization."""

    series = pd.Series(values, dtype="float64")
    filled = series.interpolate(method="linear", limit_direction="both")
    if filled.isna().any():
        median = series.median(skipna=True)
        if not np.isfinite(median):
            median = 0.0
        filled = filled.fillna(float(median))
    return filled.to_numpy(dtype="float64")


def _finish_column(values: np.ndarray, original: pd.Series) -> pd.Series:
    """Replace any numerical failure leftovers with simple deterministic fills."""

    out = pd.Series(values, index=original.index, dtype="float64")
    if out.isna().any():
        fallback = original.interpolate(method="linear", limit_direction="both")
        if fallback.isna().any():
            median = original.median(skipna=True)
            fallback = fallback.fillna(0.0 if not np.isfinite(median) else median)
        out = out.fillna(fallback)
    return out


def _set_random_seed(random_seed: int = DEFAULT_RANDOM_SEED) -> np.random.Generator:
    random.seed(random_seed)
    np.random.seed(random_seed)
    try:
        import torch

        torch.manual_seed(random_seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(random_seed)
        try:
            torch.use_deterministic_algorithms(True, warn_only=True)
        except TypeError:
            torch.use_deterministic_algorithms(True)
        except Exception:
            pass
        try:
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
        except Exception:
            pass
    except Exception:
        pass
    return np.random.default_rng(random_seed)


def _prepare_pypots_home() -> None:
    """Point PyPOTS ecosystem config to a writable path when the user home is locked."""

    try:
        default_home = Path.home() / ".pypots"
        default_home.mkdir(parents=True, exist_ok=True)
        return
    except Exception:
        pass

    fallback_home = Path.cwd() / ".pypots_home"
    fallback_home.mkdir(parents=True, exist_ok=True)
    os.environ["USERPROFILE"] = str(fallback_home)
    os.environ.setdefault("HOME", str(fallback_home))


def mean_imputation(df: pd.DataFrame, data_cols: list) -> pd.DataFrame:
    """均值填补"""
    df_imputed = df.copy()
    df_imputed[data_cols] = df_imputed[data_cols].fillna(df_imputed[data_cols].mean())
    return df_imputed


def forward_fill(df: pd.DataFrame, data_cols: list) -> pd.DataFrame:
    """前向填补"""
    df_imputed = df.copy()
    df_imputed[data_cols] = df_imputed[data_cols].ffill()
    return df_imputed


def backward_fill(df: pd.DataFrame, data_cols: list) -> pd.DataFrame:
    """后向填补"""
    df_imputed = df.copy()
    df_imputed[data_cols] = df_imputed[data_cols].bfill()
    return df_imputed


def linear_interpolation(df: pd.DataFrame, data_cols: list) -> pd.DataFrame:
    """线性插值填补"""
    df_imputed = df.copy()
    df_imputed[data_cols] = df_imputed[data_cols].interpolate(method='linear')
    return df_imputed


def _positional_interpolation(
    df: pd.DataFrame,
    data_cols: list,
    method: str,
    order: Optional[int] = None,
) -> pd.DataFrame:
    """Interpolate each column on positions to avoid duplicate timestamp failures."""

    df_imputed = df.copy()
    for col in data_cols:
        series = pd.to_numeric(df_imputed[col], errors="coerce")
        if not series.isna().any():
            continue

        values = series.to_numpy(dtype="float64")
        positional = pd.Series(values, index=pd.RangeIndex(len(values)), dtype="float64")
        kwargs = {"method": method, "limit_direction": "both"}
        if order is not None:
            kwargs["order"] = order

        filled = positional.interpolate(**kwargs)
        if filled.isna().any():
            raise ValueError(f"{method} interpolation left missing values in column {col!r}")
        df_imputed[col] = pd.Series(filled.to_numpy(dtype="float64"), index=series.index)

    return df_imputed


def pchip_interpolation(df: pd.DataFrame, data_cols: list) -> pd.DataFrame:
    """Piecewise cubic Hermite interpolation."""

    return _positional_interpolation(df, data_cols, method="pchip")


def poly2_interpolation(df: pd.DataFrame, data_cols: list) -> pd.DataFrame:
    """Second-order polynomial interpolation."""

    return _positional_interpolation(df, data_cols, method="polynomial", order=2)


def poly3_interpolation(df: pd.DataFrame, data_cols: list) -> pd.DataFrame:
    """Third-order polynomial interpolation."""

    return _positional_interpolation(df, data_cols, method="polynomial", order=3)


def spline3_interpolation(df: pd.DataFrame, data_cols: list) -> pd.DataFrame:
    """Third-order spline interpolation."""

    return _positional_interpolation(df, data_cols, method="spline", order=3)


def knn_imputation(df: pd.DataFrame, data_cols: list, n_neighbors: int = 5) -> pd.DataFrame:
    """KNN imputation across data columns."""

    try:
        from sklearn.impute import KNNImputer
    except ImportError as exc:
        raise ImportError(
            "KNN imputation requires scikit-learn. Install scikit-learn before using method `knn`."
        ) from exc

    df_imputed = df.copy()
    numeric = df_imputed[data_cols].apply(pd.to_numeric, errors="coerce")
    usable_cols = [col for col in data_cols if numeric[col].notna().any()]

    if usable_cols:
        imputer = KNNImputer(n_neighbors=max(1, min(n_neighbors, len(numeric))))
        transformed = imputer.fit_transform(numeric[usable_cols])
        df_imputed[usable_cols] = pd.DataFrame(transformed, index=df.index, columns=usable_cols)

    for col in data_cols:
        series = pd.to_numeric(df_imputed[col], errors="coerce")
        df_imputed[col] = _finish_column(series.to_numpy(dtype="float64"), series)

    return df_imputed


def mice_imputation(
    df: pd.DataFrame,
    data_cols: list,
    random_seed: int = DEFAULT_RANDOM_SEED,
    max_iter: int = 10,
) -> pd.DataFrame:
    """MICE-style iterative imputation across data columns."""

    try:
        from sklearn.experimental import enable_iterative_imputer  # noqa: F401
        from sklearn.impute import IterativeImputer
    except ImportError as exc:
        raise ImportError(
            "MICE imputation requires scikit-learn. Install scikit-learn before using method `mice`."
        ) from exc

    df_imputed = df.copy()
    numeric = df_imputed[data_cols].apply(pd.to_numeric, errors="coerce")
    usable_cols = [col for col in data_cols if numeric[col].notna().any()]

    if usable_cols:
        imputer = IterativeImputer(
            max_iter=max_iter,
            random_state=random_seed,
            initial_strategy="median",
            sample_posterior=False,
        )
        transformed = imputer.fit_transform(numeric[usable_cols])
        df_imputed[usable_cols] = pd.DataFrame(transformed, index=df.index, columns=usable_cols)

    for col in data_cols:
        series = pd.to_numeric(df_imputed[col], errors="coerce")
        df_imputed[col] = _finish_column(series.to_numpy(dtype="float64"), series)

    return df_imputed


def none_imputation(df: pd.DataFrame, data_cols: list) -> pd.DataFrame:
    """不进行任何填补，直接返回原始数据（保留缺失值）
    
    Args:
        df: 包含缺失值的数据框
        data_cols: 需要填补的列名列表
    
    Returns:
        原始数据框（保留缺失值）
    """
    return df.copy()


def _kalman_local_linear_smooth(values: Sequence[float]) -> np.ndarray:
    """Local linear trend Kalman smoother for a single sequence."""

    y = np.asarray(values, dtype="float64")
    n = len(y)
    if n == 0:
        return y.copy()

    observed = np.isfinite(y)
    filled = _initial_fill_array(y)
    if observed.sum() == 0:
        return filled

    diff = np.diff(filled)
    data_var = _finite_or_default(np.nanvar(filled), 1.0)
    diff_var = _finite_or_default(np.nanvar(diff), data_var * 0.01)
    r = _finite_or_default(diff_var * 0.1, data_var * 0.01)
    q_level = _finite_or_default(diff_var * 0.05, data_var * 0.001)
    q_slope = _finite_or_default(diff_var * 0.005, data_var * 0.0001)

    f = np.array([[1.0, 1.0], [0.0, 1.0]])
    q = np.diag([q_level, q_slope])
    h = np.array([[1.0, 0.0]])
    eye = np.eye(2)

    initial_slope = np.nanmedian(diff) if diff.size else 0.0
    if not np.isfinite(initial_slope):
        initial_slope = 0.0

    x = np.array([filled[0], initial_slope], dtype="float64")
    p = np.diag([data_var, diff_var + 1e-6])

    x_pred = np.zeros((n, 2), dtype="float64")
    p_pred = np.zeros((n, 2, 2), dtype="float64")
    x_filt = np.zeros((n, 2), dtype="float64")
    p_filt = np.zeros((n, 2, 2), dtype="float64")

    for t in range(n):
        if t == 0:
            xp = x
            pp = p
        else:
            xp = f @ x_filt[t - 1]
            pp = f @ p_filt[t - 1] @ f.T + q

        x_pred[t] = xp
        p_pred[t] = pp

        if observed[t]:
            innovation = y[t] - float(h @ xp)
            s = float(h @ pp @ h.T + r)
            if not np.isfinite(s) or s <= 1e-12:
                s = 1e-12
            k = (pp @ h.T / s).reshape(2)
            xf = xp + k * innovation
            pf = (eye - k[:, None] @ h) @ pp
        else:
            xf = xp
            pf = pp

        x_filt[t] = xf
        p_filt[t] = (pf + pf.T) / 2.0

    x_smooth = x_filt.copy()
    p_smooth = p_filt.copy()
    for t in range(n - 2, -1, -1):
        try:
            c = p_filt[t] @ f.T @ np.linalg.pinv(p_pred[t + 1])
        except np.linalg.LinAlgError:
            c = np.zeros((2, 2), dtype="float64")
        x_smooth[t] = x_filt[t] + c @ (x_smooth[t + 1] - x_pred[t + 1])
        p_smooth[t] = p_filt[t] + c @ (p_smooth[t + 1] - p_pred[t + 1]) @ c.T

    smoothed = x_smooth[:, 0]
    out = filled.copy()
    out[~observed] = smoothed[~observed]
    return out


def kalman_struct_imputation(df: pd.DataFrame, data_cols: list) -> pd.DataFrame:
    """结构时间序列 Kalman smoother 填补.

    使用局部线性趋势状态空间模型，适合单变量趋势型序列和块状缺失。
    """

    df_imputed = df.copy()
    for col in data_cols:
        series = pd.to_numeric(df_imputed[col], errors="coerce")
        if not series.isna().any():
            continue
        smoothed = _kalman_local_linear_smooth(series.to_numpy())
        df_imputed[col] = _finish_column(smoothed, series)
    return df_imputed


def _fit_ar_coefficients(filled: np.ndarray, max_lag: int = 3) -> tuple[np.ndarray, float, float]:
    observed = np.asarray(filled, dtype="float64")
    n = len(observed)
    if n < 4:
        return np.array([0.8]), float(np.nanmean(observed)), 1.0

    mean = float(np.nanmean(observed))
    std = float(np.nanstd(observed))
    if not np.isfinite(std) or std < 1e-8:
        std = 1.0

    z = (observed - mean) / std
    p = min(max_lag, max(1, n // 10))
    rows = []
    targets = []
    for t in range(p, n):
        rows.append(z[t - p:t][::-1])
        targets.append(z[t])

    x = np.asarray(rows, dtype="float64")
    y = np.asarray(targets, dtype="float64")
    try:
        coefs, *_ = np.linalg.lstsq(x, y, rcond=None)
    except np.linalg.LinAlgError:
        coefs = np.array([0.8] + [0.0] * (p - 1), dtype="float64")

    if not np.all(np.isfinite(coefs)):
        coefs = np.array([0.8] + [0.0] * (p - 1), dtype="float64")

    # Keep the companion matrix stable enough for smoothing.
    abs_sum = np.sum(np.abs(coefs))
    if abs_sum >= 0.98:
        coefs = coefs * (0.98 / abs_sum)

    residual = y - x @ coefs if len(y) else np.array([0.0])
    residual_var = _finite_or_default(np.var(residual), 0.01)
    return coefs.astype("float64"), mean, std * np.sqrt(residual_var)


def _kalman_ar_smooth(values: Sequence[float], max_lag: int = 3) -> np.ndarray:
    """AR(p) state-space Kalman smoother used by kalman_arima."""

    y_raw = np.asarray(values, dtype="float64")
    n = len(y_raw)
    if n == 0:
        return y_raw.copy()

    observed = np.isfinite(y_raw)
    filled = _initial_fill_array(y_raw)
    coefs, mean, residual_scale = _fit_ar_coefficients(filled, max_lag=max_lag)
    std = float(np.nanstd(filled))
    if not np.isfinite(std) or std < 1e-8:
        std = 1.0

    y = (y_raw - mean) / std
    filled_z = (filled - mean) / std
    p_order = len(coefs)

    f = np.zeros((p_order, p_order), dtype="float64")
    f[0, :] = coefs
    if p_order > 1:
        f[1:, :-1] = np.eye(p_order - 1)

    q = np.zeros((p_order, p_order), dtype="float64")
    q[0, 0] = _finite_or_default((residual_scale / std) ** 2, 0.01)
    h = np.zeros((1, p_order), dtype="float64")
    h[0, 0] = 1.0
    r = max(q[0, 0] * 0.1, 1e-5)
    eye = np.eye(p_order)

    state = np.zeros(p_order, dtype="float64")
    first_vals = filled_z[:p_order]
    state[: len(first_vals)] = first_vals[::-1]
    p_mat = np.eye(p_order) * max(float(np.nanvar(filled_z)), 1.0)

    x_pred = np.zeros((n, p_order), dtype="float64")
    p_pred = np.zeros((n, p_order, p_order), dtype="float64")
    x_filt = np.zeros((n, p_order), dtype="float64")
    p_filt = np.zeros((n, p_order, p_order), dtype="float64")

    for t in range(n):
        if t == 0:
            xp = state
            pp = p_mat
        else:
            xp = f @ x_filt[t - 1]
            pp = f @ p_filt[t - 1] @ f.T + q

        x_pred[t] = xp
        p_pred[t] = pp

        if observed[t]:
            innovation = y[t] - float(h @ xp)
            s = float(h @ pp @ h.T + r)
            if not np.isfinite(s) or s <= 1e-12:
                s = 1e-12
            k = (pp @ h.T / s).reshape(p_order)
            xf = xp + k * innovation
            pf = (eye - k[:, None] @ h) @ pp
        else:
            xf = xp
            pf = pp

        x_filt[t] = xf
        p_filt[t] = (pf + pf.T) / 2.0

    x_smooth = x_filt.copy()
    p_smooth = p_filt.copy()
    for t in range(n - 2, -1, -1):
        try:
            c = p_filt[t] @ f.T @ np.linalg.pinv(p_pred[t + 1])
        except np.linalg.LinAlgError:
            c = np.zeros((p_order, p_order), dtype="float64")
        x_smooth[t] = x_filt[t] + c @ (x_smooth[t + 1] - x_pred[t + 1])
        p_smooth[t] = p_filt[t] + c @ (p_smooth[t + 1] - p_pred[t + 1]) @ c.T

    out = filled.copy()
    out[~observed] = mean + std * x_smooth[~observed, 0]
    return out


def kalman_arima_imputation(
    df: pd.DataFrame,
    data_cols: list,
    max_lag: int = 3,
) -> pd.DataFrame:
    """AR 状态空间 Kalman smoother 填补.

    该实现以稳定 AR(p) 近似 ARIMA 动态，并用 Kalman smoother 恢复缺失点。
    """

    df_imputed = df.copy()
    for col in data_cols:
        series = pd.to_numeric(df_imputed[col], errors="coerce")
        if not series.isna().any():
            continue
        smoothed = _kalman_ar_smooth(series.to_numpy(), max_lag=max_lag)
        df_imputed[col] = _finish_column(smoothed, series)
    return df_imputed


def _rbf_kernel(x1: np.ndarray, x2: np.ndarray, length_scale: float, variance: float) -> np.ndarray:
    sqdist = (x1[:, None] - x2[None, :]) ** 2
    return variance * np.exp(-0.5 * sqdist / max(length_scale, 1e-8) ** 2)


def _select_gp_train_indices(
    obs_idx: np.ndarray,
    miss_idx: np.ndarray,
    max_train_points: int,
    rng: np.random.Generator,
) -> np.ndarray:
    if len(obs_idx) <= max_train_points:
        return obs_idx

    if len(miss_idx):
        distance = np.min(np.abs(obs_idx[:, None] - miss_idx[None, :]), axis=1)
        local_count = max_train_points // 2
        local = obs_idx[np.argsort(distance)[:local_count]]
        remaining = np.setdiff1d(obs_idx, local, assume_unique=False)
        random_count = max_train_points - len(local)
        if random_count > 0 and len(remaining) > 0:
            sampled = rng.choice(remaining, size=min(random_count, len(remaining)), replace=False)
            selected = np.concatenate([local, sampled])
        else:
            selected = local
        return np.sort(selected)

    return np.sort(rng.choice(obs_idx, size=max_train_points, replace=False))


def gp_rbf_imputation(
    df: pd.DataFrame,
    data_cols: list,
    random_seed: int = DEFAULT_RANDOM_SEED,
    max_train_points: int = 512,
    noise: float = 1e-4,
) -> pd.DataFrame:
    """RBF Gaussian Process 填补.

    使用时间索引作为一维输入。长序列会抽取观测训练点以控制复杂度；
    抽样由 ``random_seed`` 控制。
    """

    rng = _set_random_seed(random_seed)
    df_imputed = df.copy()

    for col in data_cols:
        series = pd.to_numeric(df_imputed[col], errors="coerce")
        values = series.to_numpy(dtype="float64")
        missing_mask = ~np.isfinite(values)
        if not missing_mask.any():
            continue

        obs_idx = np.where(~missing_mask)[0]
        miss_idx = np.where(missing_mask)[0]
        if len(obs_idx) < 2:
            df_imputed[col] = _finish_column(_initial_fill_array(values), series)
            continue

        selected = _select_gp_train_indices(obs_idx, miss_idx, max_train_points, rng)
        n = len(values)
        x_train = selected.astype("float64") / max(n - 1, 1)
        x_miss = miss_idx.astype("float64") / max(n - 1, 1)

        y_train_raw = values[selected]
        y_mean = float(np.mean(y_train_raw))
        y_std = float(np.std(y_train_raw))
        if not np.isfinite(y_std) or y_std < 1e-8:
            y_std = 1.0
        y_train = (y_train_raw - y_mean) / y_std

        if len(selected) > 2:
            spacing = np.median(np.diff(np.sort(x_train)))
            length_scale = max(float(spacing) * 10.0, 0.03)
        else:
            length_scale = 0.1
        variance = _finite_or_default(np.var(y_train), 1.0)

        k = _rbf_kernel(x_train, x_train, length_scale, variance)
        k[np.diag_indices_from(k)] += noise + 1e-8

        try:
            chol = np.linalg.cholesky(k)
            alpha = np.linalg.solve(chol.T, np.linalg.solve(chol, y_train))
            k_star = _rbf_kernel(x_miss, x_train, length_scale, variance)
            pred = y_mean + y_std * (k_star @ alpha)
        except np.linalg.LinAlgError:
            pred = _initial_fill_array(values)[miss_idx]

        out = values.copy()
        out[miss_idx] = pred
        df_imputed[col] = _finish_column(out, series)

    return df_imputed


def _build_saits_windows(values: np.ndarray, n_steps: int) -> tuple[np.ndarray, list[tuple[int, int]]]:
    n = len(values)
    if n == 0:
        return np.empty((0, 0, 1), dtype="float32"), []
    n_steps = max(2, min(n_steps, n))
    stride = max(1, n_steps // 2)
    starts = list(range(0, max(1, n - n_steps + 1), stride))
    if not starts or starts[-1] != n - n_steps:
        starts.append(max(0, n - n_steps))
    starts = sorted(set(starts))
    windows = []
    spans = []
    for start in starts:
        end = start + n_steps
        windows.append(values[start:end].reshape(n_steps, 1))
        spans.append((start, end))
    return np.asarray(windows, dtype="float32"), spans


def _instantiate_saits(SAITS, params: Dict):
    attempts = [
        params,
        {k: v for k, v in params.items() if k not in {"patience", "device"}},
        {
            k: v
            for k, v in params.items()
            if k
            in {
                "n_steps",
                "n_features",
                "n_layers",
                "d_model",
                "d_ffn",
                "n_heads",
                "d_k",
                "d_v",
                "dropout",
                "epochs",
                "batch_size",
            }
        },
    ]
    last_error = None
    for kwargs in attempts:
        try:
            return SAITS(**kwargs)
        except TypeError as exc:
            last_error = exc
    raise last_error


def saits_imputation(
    df: pd.DataFrame,
    data_cols: list,
    random_seed: int = DEFAULT_RANDOM_SEED,
    n_steps: int = 96,
    epochs: int = 10,
    batch_size: int = 32,
    device: Optional[str] = "cpu",
) -> pd.DataFrame:
    """SAITS 深度学习填补.

    依赖 PyPOTS。为了保持单序列设定，本函数逐列训练/填补，不利用跨列信息。
    """

    _set_random_seed(random_seed)
    _prepare_pypots_home()
    try:
        from pypots.imputation import SAITS
    except ImportError as exc:
        raise ImportError(
            "SAITS imputation requires PyPOTS. Install it with `pip install pypots` "
            "in the project environment before using method `saits`."
        ) from exc

    df_imputed = df.copy()
    for col in data_cols:
        series = pd.to_numeric(df_imputed[col], errors="coerce")
        values = series.to_numpy(dtype="float64")
        missing_mask = ~np.isfinite(values)
        if not missing_mask.any():
            continue
        if np.isfinite(values).sum() < 2:
            df_imputed[col] = _finish_column(_initial_fill_array(values), series)
            continue

        mean = float(np.nanmean(values))
        std = float(np.nanstd(values))
        if not np.isfinite(std) or std < 1e-8:
            std = 1.0
        standardized = (values - mean) / std

        x_windows, spans = _build_saits_windows(standardized, n_steps=n_steps)
        if len(spans) == 0:
            df_imputed[col] = _finish_column(_initial_fill_array(values), series)
            continue

        actual_steps = x_windows.shape[1]
        model_params = {
            "n_steps": actual_steps,
            "n_features": 1,
            "n_layers": 2,
            "d_model": 64,
            "d_ffn": 128,
            "n_heads": 4,
            "d_k": 16,
            "d_v": 16,
            "dropout": 0.0,
            "epochs": epochs,
            "batch_size": min(batch_size, max(1, len(x_windows))),
            "patience": None if epochs <= 3 else min(3, epochs - 1),
        }
        if device is not None:
            model_params["device"] = device

        model = _instantiate_saits(SAITS, model_params)
        train_set = {"X": x_windows}
        model.fit(train_set)
        imputed_windows = model.impute(train_set)

        sums = np.zeros(len(values), dtype="float64")
        counts = np.zeros(len(values), dtype="float64")
        for window, (start, end) in zip(imputed_windows, spans):
            pred = np.asarray(window).reshape(actual_steps)
            sums[start:end] += pred[: end - start]
            counts[start:end] += 1.0

        out = values.copy()
        covered = missing_mask & (counts > 0)
        out[covered] = mean + std * (sums[covered] / counts[covered])
        df_imputed[col] = _finish_column(out, series)

    return df_imputed


IMPUTATION_METHODS: Dict[str, Callable] = {
    'mean': mean_imputation,
    'forward': forward_fill,
    'backward': backward_fill,
    'linear': linear_interpolation,
    'knn': knn_imputation,
    'mice': mice_imputation,
    'pchip': pchip_interpolation,
    'poly2': poly2_interpolation,
    'poly3': poly3_interpolation,
    'spline3': spline3_interpolation,
    'kalman_struct': kalman_struct_imputation,
    'kalman_arima': kalman_arima_imputation,
    'gp_rbf': gp_rbf_imputation,
    'saits': saits_imputation,
    'none': none_imputation,
}


def get_imputation_method(method_name: str):
    """获取填补方法函数."""

    normalized = method_name.lower()
    if normalized not in IMPUTATION_METHODS:
        raise ValueError(
            f"Unknown imputation method: {method_name}. "
            f"Available methods: {list(IMPUTATION_METHODS.keys())}"
        )

    return IMPUTATION_METHODS[normalized]
