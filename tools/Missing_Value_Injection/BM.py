"""BM（块缺失）缺失值注入模块。"""

import argparse
from pathlib import Path
from typing import List, Sequence, Tuple

import numpy as np
import pandas as pd

try:
    from .inject_range_utils import get_injection_range, load_dataset_properties
except ImportError:
    from inject_range_utils import get_injection_range, load_dataset_properties


DEFAULT_BALANCED_CONTEXTS = [512, 2048, 2880, 4096, 8192]


def parse_missing_ratios(ratio_str: str) -> List[float]:
    ratio_str = ratio_str.strip().strip("[]")
    ratios = [float(r.strip()) for r in ratio_str.split(",") if r.strip()]
    if not ratios:
        raise ValueError("missing_ratio list is empty")
    for ratio in ratios:
        if not 0 <= ratio <= 1:
            raise ValueError(f"missing_ratio must be between 0 and 1, got {ratio}")
    return ratios


def parse_int_list(value: str) -> List[int]:
    chunks = [c.strip() for c in value.strip().strip("[]").split(",") if c.strip()]
    if not chunks:
        raise ValueError("balanced_contexts list is empty")
    contexts = [int(c) for c in chunks]
    if any(c <= 0 for c in contexts):
        raise ValueError("balanced_contexts must be positive integers")
    return sorted(set(contexts))


def _allocate_integer(total: int, weights: Sequence[float]) -> List[int]:
    if total <= 0:
        return [0 for _ in weights]
    weight_sum = float(sum(weights))
    if weight_sum <= 0:
        out = [0 for _ in weights]
        out[0] = total
        return out
    raw = [total * (w / weight_sum) for w in weights]
    base = [int(np.floor(v)) for v in raw]
    rem = total - sum(base)
    if rem > 0:
        order = sorted(range(len(raw)), key=lambda i: (raw[i] - base[i]), reverse=True)
        for i in order[:rem]:
            base[i] += 1
    return base


def _can_place(occupied: np.ndarray, start_rel: int, length: int, min_gap: int = 1) -> bool:
    end_rel = start_rel + length
    left = max(0, start_rel - min_gap)
    right = min(len(occupied), end_rel + min_gap)
    return not occupied[left:right].any()


def _place_block_random(
    occupied: np.ndarray,
    global_start_idx: int,
    layer_start: int,
    layer_end: int,
    block_length: int,
    rng: np.random.Generator,
    trials: int,
) -> int | None:
    max_start = layer_end - block_length
    if max_start < layer_start:
        return None

    n_candidates = max_start - layer_start + 1
    attempts = min(max(1, trials), n_candidates)
    for _ in range(attempts):
        start = int(rng.integers(layer_start, max_start + 1))
        start_rel = start - global_start_idx
        if _can_place(occupied, start_rel, block_length):
            occupied[start_rel:start_rel + block_length] = True
            return start

    if n_candidates <= 10000:
        starts = np.arange(layer_start, max_start + 1)
        rng.shuffle(starts)
        for start in starts.tolist():
            start_rel = int(start) - global_start_idx
            if _can_place(occupied, start_rel, block_length):
                occupied[start_rel:start_rel + block_length] = True
                return int(start)

    return None


def _build_stratified_ranges(
    dataset_name: str,
    term: str,
    data_path: str,
    start_idx: int,
    end_idx: int,
    balanced_contexts: Sequence[int],
) -> List[Tuple[int, int]]:
    starts: List[int] = []
    for mc in sorted(set(balanced_contexts)):
        r = get_injection_range(dataset_name=dataset_name, term=term, data_path=data_path, max_context=mc)
        s = max(start_idx, int(r["start_index"]))
        e = min(end_idx, int(r["end_index"]))
        if s < e:
            starts.append(s)

    starts = sorted(set(starts), reverse=True)
    if not starts:
        return [(start_idx, end_idx)]

    ranges: List[Tuple[int, int]] = []
    prev = end_idx
    for s in starts:
        if s < prev:
            ranges.append((s, prev))
            prev = s
    if start_idx < prev:
        ranges.append((start_idx, prev))
    return ranges


def _context_stats(
    df: pd.DataFrame,
    data_cols: Sequence[str],
    dataset_name: str,
    term: str,
    data_path: str,
    start_idx: int,
    end_idx: int,
    balanced_contexts: Sequence[int],
) -> List[dict]:
    stats = []
    for mc in sorted(set(balanced_contexts)):
        r = get_injection_range(dataset_name=dataset_name, term=term, data_path=data_path, max_context=mc)
        s = max(start_idx, int(r["start_index"]))
        e = min(end_idx, int(r["end_index"]))
        if s >= e:
            continue
        part = df.iloc[s:e][list(data_cols)]
        total_cells = len(part) * len(data_cols)
        missing_cells = int(part.isna().sum().sum())
        ratio = (missing_cells / total_cells) if total_cells > 0 else 0.0
        stats.append(
            {
                "max_context": mc,
                "start_index": s,
                "end_index": e,
                "total_cells": total_cells,
                "missing_cells": missing_cells,
                "missing_ratio": ratio,
            }
        )
    return stats



def _data_columns(df: pd.DataFrame) -> List[str]:
    excluded_cols = {"date", "time", "timestamp", "item_id"}
    data_cols = [col for col in df.columns if col.lower() not in excluded_cols]
    if not data_cols:
        raise ValueError("No data columns available for missing injection")
    return data_cols


def _build_seed(seed: int, dataset_name: str, term: str, missing_ratio: float, pattern: str, variant: str, mode: str) -> int:
    seed_offset = hash(f"{dataset_name}_{term}_{missing_ratio}_{pattern}_{variant}_{mode}") % 10000
    return seed + seed_offset


def _summarize_injection(
    df: pd.DataFrame,
    data_cols: Sequence[str],
    dataset_name: str,
    term: str,
    data_path: str,
    start_idx: int,
    end_idx: int,
    missing_ratio: float,
    pattern: str,
    variant: str,
    mode: str,
    block_length: int | None,
    balanced_contexts: Sequence[int],
    ratio_tolerance: float,
    repair_steps: int,
    positions: List[dict],
) -> dict:
    injection_length = end_idx - start_idx
    injection_area_size = injection_length * len(data_cols)
    injected_count = int(df.iloc[start_idx:end_idx][list(data_cols)].isna().sum().sum())
    actual_missing_ratio = injected_count / injection_area_size if injection_area_size > 0 else 0.0
    context_stats = _context_stats(
        df=df,
        data_cols=data_cols,
        dataset_name=dataset_name,
        term=term,
        data_path=data_path,
        start_idx=start_idx,
        end_idx=end_idx,
        balanced_contexts=balanced_contexts,
    )
    lower = missing_ratio * (1 - ratio_tolerance)
    upper = missing_ratio * (1 + ratio_tolerance)
    within_tolerance = all(lower <= s["missing_ratio"] <= upper for s in context_stats) if context_stats else True
    return {
        "dataset_name": dataset_name,
        "term": term,
        "missing_ratio": missing_ratio,
        "pattern": pattern,
        "variant": variant,
        "block_length": block_length,
        "mode": mode,
        "n_blocks": sum(1 for p in positions if "length" in p),
        "total_cells": injection_area_size,
        "injected_missing": injected_count,
        "actual_missing_ratio": actual_missing_ratio,
        "injection_range": {"start_index": start_idx, "end_index": end_idx, "length": injection_length},
        "balanced_contexts": list(sorted(set(balanced_contexts))),
        "ratio_tolerance": ratio_tolerance,
        "repair_steps": repair_steps,
        "within_tolerance": within_tolerance,
        "context_stats": context_stats,
        "positions": positions,
        "block_positions": positions,
        "data_columns": list(data_cols),
    }


def _inject_mcar_point(
    df: pd.DataFrame,
    data_cols: Sequence[str],
    start_idx: int,
    end_idx: int,
    missing_ratio: float,
    rng: np.random.Generator,
) -> List[dict]:
    n_rows = end_idx - start_idx
    total_cells = n_rows * len(data_cols)
    target_missing = int(round(total_cells * missing_ratio))
    if target_missing <= 0:
        return []

    target_missing = min(target_missing, total_cells)
    flat_indices = rng.choice(total_cells, size=target_missing, replace=False)
    positions: List[dict] = []
    n_cols = len(data_cols)
    for flat_idx in flat_indices.tolist():
        row_offset = int(flat_idx) // n_cols
        col_offset = int(flat_idx) % n_cols
        row_idx = start_idx + row_offset
        col = data_cols[col_offset]
        df.loc[row_idx, col] = np.nan
        positions.append({"column": col, "index": row_idx})
    return positions


def _target_missing_cells(
    n_rows: int,
    n_cols: int,
    missing_ratio: float,
) -> int:
    total_cells = max(0, n_rows) * max(0, n_cols)
    return max(0, min(total_cells, int(round(total_cells * missing_ratio))))


def _available_counts_by_column(
    df: pd.DataFrame,
    data_cols: Sequence[str],
    start_idx: int,
    end_idx: int,
) -> List[int]:
    counts: List[int] = []
    for col in data_cols:
        counts.append(int(df.iloc[start_idx:end_idx][col].notna().sum()))
    return counts


def _allocate_by_capacity(total: int, capacities: Sequence[int]) -> List[int]:
    capped_total = min(max(0, total), int(sum(capacities)))
    quotas = _allocate_integer(capped_total, capacities)
    overflow = 0
    for i, capacity in enumerate(capacities):
        if quotas[i] > capacity:
            overflow += quotas[i] - capacity
            quotas[i] = capacity

    while overflow > 0:
        changed = False
        for i, capacity in enumerate(capacities):
            if quotas[i] >= capacity:
                continue
            quotas[i] += 1
            overflow -= 1
            changed = True
            if overflow <= 0:
                break
        if not changed:
            break
    return quotas


def _apply_selected_by_column(
    df: pd.DataFrame,
    selected_by_col: dict[str, Sequence[int]],
    max_position_entries: int = 10000,
) -> Tuple[List[dict], dict]:
    positions: List[dict] = []
    segment_count = 0
    selected_count = 0
    per_column_counts: dict[str, int] = {}

    for col, indices in selected_by_col.items():
        unique_indices = sorted(set(int(i) for i in indices))
        if not unique_indices:
            per_column_counts[col] = 0
            continue

        df.loc[unique_indices, col] = np.nan
        per_column_counts[col] = len(unique_indices)
        selected_count += len(unique_indices)

        for seg_start, seg_end in _compress_indices(unique_indices):
            segment_count += 1
            if len(positions) >= max_position_entries:
                continue
            positions.append(
                {
                    "column": col,
                    "start": seg_start,
                    "end": seg_end,
                    "length": seg_end - seg_start,
                }
            )

    return positions, {
        "actual_new_missing": selected_count,
        "position_segments": segment_count,
        "positions_truncated": segment_count > len(positions),
        "per_column_missing": per_column_counts,
    }


def _compress_indices(indices: Sequence[int]) -> List[Tuple[int, int]]:
    if not indices:
        return []
    sorted_indices = sorted(set(int(i) for i in indices))
    ranges: List[Tuple[int, int]] = []
    start = sorted_indices[0]
    prev = sorted_indices[0]
    for idx in sorted_indices[1:]:
        if idx == prev + 1:
            prev = idx
            continue
        ranges.append((start, prev + 1))
        start = idx
        prev = idx
    ranges.append((start, prev + 1))
    return ranges


def _build_forecast_starts(injection_range: dict, start_idx: int, end_idx: int) -> List[int]:
    total_length = int(injection_range.get("total_length", end_idx))
    prediction_length = int(injection_range.get("prediction_length", 0))
    windows = int(injection_range.get("windows", 0))
    if prediction_length <= 0 or windows <= 0:
        return [end_idx]

    first_start = total_length - prediction_length * windows
    starts = [first_start + i * prediction_length for i in range(windows)]
    return [s for s in starts if start_idx < s <= end_idx]


def _inject_front_matched_budget(
    df: pd.DataFrame,
    data_cols: Sequence[str],
    start_idx: int,
    end_idx: int,
    missing_ratio: float,
    block_length: int,
    injection_range: dict,
) -> Tuple[List[dict], dict]:
    injection_length = end_idx - start_idx
    total_cells = injection_length * len(data_cols)
    if injection_length <= 0 or total_cells <= 0:
        return [], {"front_allocation": "matched_budget", "target_missing": 0}

    raw_target_missing = int(round(total_cells * missing_ratio))
    if block_length > 0:
        target_missing = (raw_target_missing // block_length) * block_length
    else:
        target_missing = raw_target_missing
    target_missing = max(0, min(total_cells, target_missing))
    if target_missing <= 0:
        return [], {
            "front_allocation": "matched_budget",
            "raw_target_missing": raw_target_missing,
            "target_missing": 0,
        }

    forecast_starts = _build_forecast_starts(injection_range, start_idx, end_idx)
    if not forecast_starts:
        forecast_starts = [end_idx]

    pairs: List[Tuple[int, str, int, int]] = []
    for col_idx, col in enumerate(data_cols):
        for window_idx, forecast_start in enumerate(forecast_starts):
            pairs.append((col_idx, col, window_idx, forecast_start))

    quotas = _allocate_integer(target_missing, [1.0] * len(pairs))
    occupied = np.zeros((len(data_cols), injection_length), dtype=bool)
    for col_idx, col in enumerate(data_cols):
        occupied[col_idx] = df.iloc[start_idx:end_idx][col].isna().to_numpy()

    selected: dict[Tuple[int, int], List[int]] = {
        (col_idx, window_idx): [] for col_idx, _, window_idx, _ in pairs
    }
    remaining = quotas[:]
    max_distance = max(s - start_idx for s in forecast_starts)

    for distance in range(1, max_distance + 1):
        if sum(remaining) <= 0:
            break
        for pair_idx, (col_idx, _col, window_idx, forecast_start) in enumerate(pairs):
            if remaining[pair_idx] <= 0:
                continue
            row_idx = forecast_start - distance
            if row_idx < start_idx:
                continue
            rel_idx = row_idx - start_idx
            if occupied[col_idx, rel_idx]:
                continue
            occupied[col_idx, rel_idx] = True
            selected[(col_idx, window_idx)].append(row_idx)
            remaining[pair_idx] -= 1

    redistributed = 0
    remaining_total = sum(remaining)
    if remaining_total > 0:
        fallback_candidates: List[Tuple[int, int, int]] = []
        for col_idx in range(len(data_cols)):
            for rel_idx in range(injection_length):
                if occupied[col_idx, rel_idx]:
                    continue
                row_idx = start_idx + rel_idx
                distances = [s - row_idx for s in forecast_starts if row_idx < s]
                if not distances:
                    continue
                fallback_candidates.append((min(distances), col_idx, row_idx))
        fallback_candidates.sort()
        for _, col_idx, row_idx in fallback_candidates[:remaining_total]:
            rel_idx = row_idx - start_idx
            if occupied[col_idx, rel_idx]:
                continue
            occupied[col_idx, rel_idx] = True
            nearest_window = min(
                range(len(forecast_starts)),
                key=lambda i: forecast_starts[i] - row_idx if row_idx < forecast_starts[i] else injection_length + 1,
            )
            selected[(col_idx, nearest_window)].append(row_idx)
            redistributed += 1

    positions: List[dict] = []
    per_window_missing = [0 for _ in forecast_starts]
    for col_idx, col in enumerate(data_cols):
        col_indices: List[int] = []
        for window_idx, forecast_start in enumerate(forecast_starts):
            indices = selected.get((col_idx, window_idx), [])
            if not indices:
                continue
            col_indices.extend(indices)
            per_window_missing[window_idx] += len(indices)
            for seg_start, seg_end in _compress_indices(indices):
                positions.append(
                    {
                        "column": col,
                        "window_index": window_idx,
                        "forecast_start": forecast_start,
                        "start": seg_start,
                        "end": seg_end,
                        "length": seg_end - seg_start,
                    }
                )
        if col_indices:
            df.loc[sorted(set(col_indices)), col] = np.nan

    actual_new_missing = sum(len(set(indices)) for indices in selected.values())
    front_info = {
        "front_allocation": "matched_budget",
        "front_budget_reference": "injection_range_cells",
        "raw_target_missing": raw_target_missing,
        "target_missing": target_missing,
        "actual_new_missing": actual_new_missing,
        "budget_quantum": block_length,
        "prediction_length": int(injection_range.get("prediction_length", 0)),
        "windows": len(forecast_starts),
        "forecast_starts": forecast_starts,
        "missing_quota_per_window": per_window_missing,
        "redistributed_missing": redistributed,
    }
    return positions, front_info


def _infer_period_length(injection_range: dict, n_rows: int) -> int:
    prediction_length = int(injection_range.get("prediction_length", 0))
    if prediction_length > 1:
        return max(2, min(prediction_length, n_rows))
    return max(2, min(24, n_rows))


def _inject_periodic_fixedphase(
    df: pd.DataFrame,
    data_cols: Sequence[str],
    start_idx: int,
    end_idx: int,
    missing_ratio: float,
    rng: np.random.Generator,
    injection_range: dict,
) -> Tuple[List[dict], dict]:
    n_rows = end_idx - start_idx
    target_missing = _target_missing_cells(n_rows, len(data_cols), missing_ratio)
    if n_rows <= 0 or target_missing <= 0:
        return [], {"periodic_allocation": "fixedphase", "target_missing": 0}

    capacities = _available_counts_by_column(df, data_cols, start_idx, end_idx)
    quotas = _allocate_by_capacity(target_missing, capacities)
    period_length = _infer_period_length(injection_range, n_rows)

    phase_order = np.arange(period_length)
    rng.shuffle(phase_order)
    phase_rank = np.empty(period_length, dtype=int)
    phase_rank[phase_order] = np.arange(period_length)

    rel_rows = np.arange(n_rows)
    row_phase_rank = phase_rank[rel_rows % period_length]
    row_order = np.lexsort((rel_rows, row_phase_rank))

    selected_by_col: dict[str, List[int]] = {}
    for col, quota in zip(data_cols, quotas):
        if quota <= 0:
            selected_by_col[col] = []
            continue
        available = df.iloc[start_idx:end_idx][col].notna().to_numpy()
        candidate_rel = row_order[available[row_order]]
        selected_by_col[col] = (start_idx + candidate_rel[:quota]).astype(int).tolist()

    positions, apply_info = _apply_selected_by_column(df, selected_by_col)
    selected_phases = sorted(
        {
            int((row_idx - start_idx) % period_length)
            for indices in selected_by_col.values()
            for row_idx in indices
        }
    )
    info = {
        "periodic_allocation": "fixedphase",
        "period_reference": "prediction_length",
        "period_length": period_length,
        "phase_order": phase_order.astype(int).tolist(),
        "selected_phases": selected_phases,
        "target_missing": target_missing,
    }
    info.update(apply_info)
    return positions, info


def _inject_peak_highvalue(
    df: pd.DataFrame,
    data_cols: Sequence[str],
    start_idx: int,
    end_idx: int,
    missing_ratio: float,
) -> Tuple[List[dict], dict]:
    n_rows = end_idx - start_idx
    target_missing = _target_missing_cells(n_rows, len(data_cols), missing_ratio)
    if n_rows <= 0 or target_missing <= 0:
        return [], {"peak_allocation": "highvalue", "target_missing": 0}

    capacities = _available_counts_by_column(df, data_cols, start_idx, end_idx)
    quotas = _allocate_by_capacity(target_missing, capacities)
    selected_by_col: dict[str, List[int]] = {}

    for col, quota in zip(data_cols, quotas):
        if quota <= 0:
            selected_by_col[col] = []
            continue

        series = pd.to_numeric(df.iloc[start_idx:end_idx][col], errors="coerce")
        values = series.to_numpy(dtype="float64")
        valid_rel = np.flatnonzero(np.isfinite(values))
        if len(valid_rel) == 0:
            selected_by_col[col] = []
            continue
        order = valid_rel[np.argsort(values[valid_rel], kind="mergesort")[::-1]]
        selected_by_col[col] = (start_idx + order[:quota]).astype(int).tolist()

    positions, apply_info = _apply_selected_by_column(df, selected_by_col)
    info = {
        "peak_allocation": "highvalue",
        "score_reference": "within_column_raw_value_descending",
        "target_missing": target_missing,
    }
    info.update(apply_info)
    return positions, info


def _inject_change_highslope(
    df: pd.DataFrame,
    data_cols: Sequence[str],
    start_idx: int,
    end_idx: int,
    missing_ratio: float,
) -> Tuple[List[dict], dict]:
    n_rows = end_idx - start_idx
    target_missing = _target_missing_cells(n_rows, len(data_cols), missing_ratio)
    if n_rows <= 0 or target_missing <= 0:
        return [], {"change_allocation": "highslope", "target_missing": 0}

    capacities = _available_counts_by_column(df, data_cols, start_idx, end_idx)
    quotas = _allocate_by_capacity(target_missing, capacities)
    selected_by_col: dict[str, List[int]] = {}

    for col, quota in zip(data_cols, quotas):
        if quota <= 0:
            selected_by_col[col] = []
            continue

        full_series = pd.to_numeric(df[col], errors="coerce")
        prev_diff = (full_series - full_series.shift(1)).abs()
        next_diff = (full_series.shift(-1) - full_series).abs()
        score = pd.concat([prev_diff, next_diff], axis=1).max(axis=1)
        score_values = score.iloc[start_idx:end_idx].fillna(0.0).to_numpy(dtype="float64")
        value_values = full_series.iloc[start_idx:end_idx].to_numpy(dtype="float64")
        valid_rel = np.flatnonzero(np.isfinite(value_values))
        if len(valid_rel) == 0:
            selected_by_col[col] = []
            continue
        order = valid_rel[np.argsort(score_values[valid_rel], kind="mergesort")[::-1]]
        selected_by_col[col] = (start_idx + order[:quota]).astype(int).tolist()

    positions, apply_info = _apply_selected_by_column(df, selected_by_col)
    info = {
        "change_allocation": "highslope",
        "score_reference": "max_abs_previous_or_next_difference",
        "target_missing": target_missing,
    }
    info.update(apply_info)
    return positions, info


def inject_missing(
    dataset_name: str,
    injection_range: dict,
    missing_ratio: float,
    term: str,
    pattern: str = "BM",
    variant: str | None = None,
    block_length: int = 50,
    seed: int = 42,
    mode: str = "stratified",
    balanced_contexts: Sequence[int] = DEFAULT_BALANCED_CONTEXTS,
    ratio_tolerance: float = 0.1,
    repair_steps: int = 20,
) -> Tuple[pd.DataFrame, dict]:
    pattern_key = pattern.upper()
    if variant is None:
        if pattern_key == "BM":
            variant_key = "fixed"
        elif pattern_key == "TM":
            variant_key = "front_matched"
        elif pattern_key == "PERIODIC":
            variant_key = "fixedphase"
        elif pattern_key == "PEAK":
            variant_key = "highvalue"
        elif pattern_key == "CHANGE":
            variant_key = "highslope"
        else:
            variant_key = "point"
    else:
        variant_key = variant.lower()

    if pattern_key == "BM" and variant_key in {"fixed", "fixed_block", "block"}:
        df, info = inject_bm(
            dataset_name=dataset_name,
            injection_range=injection_range,
            missing_ratio=missing_ratio,
            term=term,
            block_length=block_length,
            seed=seed,
            mode=mode,
            balanced_contexts=balanced_contexts,
            ratio_tolerance=ratio_tolerance,
            repair_steps=repair_steps,
        )
        info["pattern"] = "BM"
        info["variant"] = "fixed"
        return df, info

    data_path = injection_range.get("data_path", "data/datasets")
    csv_path = Path(data_path) / "ori" / f"{dataset_name}.csv"
    df = pd.read_csv(csv_path)
    start_idx = int(injection_range["start_index"])
    end_idx = int(injection_range["end_index"])
    data_cols = _data_columns(df)
    rng = np.random.default_rng(_build_seed(seed, dataset_name, term, missing_ratio, pattern_key, variant_key, mode))

    extra_info: dict = {}
    if pattern_key == "MCAR" and variant_key in {"point", "random_point", "mcar"}:
        positions = _inject_mcar_point(
            df=df,
            data_cols=data_cols,
            start_idx=start_idx,
            end_idx=end_idx,
            missing_ratio=missing_ratio,
            rng=rng,
        )
    elif pattern_key == "TM" and variant_key in {"front", "front_matched", "matched_front", "forecast_front", "pre_forecast"}:
        positions, extra_info = _inject_front_matched_budget(
            df=df,
            data_cols=data_cols,
            start_idx=start_idx,
            end_idx=end_idx,
            missing_ratio=missing_ratio,
            block_length=block_length,
            injection_range=injection_range,
        )
    elif pattern_key == "PERIODIC" and variant_key in {"fixedphase", "fixed_phase", "seasonal", "periodic"}:
        positions, extra_info = _inject_periodic_fixedphase(
            df=df,
            data_cols=data_cols,
            start_idx=start_idx,
            end_idx=end_idx,
            missing_ratio=missing_ratio,
            rng=rng,
            injection_range=injection_range,
        )
    elif pattern_key == "PEAK" and variant_key in {"highvalue", "high_value", "peak"}:
        positions, extra_info = _inject_peak_highvalue(
            df=df,
            data_cols=data_cols,
            start_idx=start_idx,
            end_idx=end_idx,
            missing_ratio=missing_ratio,
        )
    elif pattern_key == "CHANGE" and variant_key in {"highslope", "high_slope", "change", "change_point"}:
        positions, extra_info = _inject_change_highslope(
            df=df,
            data_cols=data_cols,
            start_idx=start_idx,
            end_idx=end_idx,
            missing_ratio=missing_ratio,
        )
    else:
        raise ValueError(f"Unsupported missing pattern/variant: {pattern_key}/{variant_key}")

    info = _summarize_injection(
        df=df,
        data_cols=data_cols,
        dataset_name=dataset_name,
        term=term,
        data_path=data_path,
        start_idx=start_idx,
        end_idx=end_idx,
        missing_ratio=missing_ratio,
        pattern=pattern_key,
        variant=variant_key,
        mode=mode,
        block_length=block_length if pattern_key in {"BM", "TM"} else None,
        balanced_contexts=balanced_contexts,
        ratio_tolerance=ratio_tolerance,
        repair_steps=repair_steps,
        positions=positions,
    )
    info.update(extra_info)
    return df, info


def build_missing_filename(
    dataset_name: str,
    pattern: str,
    missing_ratio: float,
    term: str,
    variant: str | None = None,
    block_length: int | None = None,
) -> str:
    ratio_str = f"{int(missing_ratio * 100):03d}"
    pattern_key = pattern.upper()
    variant_key = variant.lower() if variant else None
    if pattern_key == "BM" and variant_key in {None, "fixed", "fixed_block", "block"}:
        length = block_length if block_length is not None else 50
        return f"{dataset_name}_BM_length{length}_{ratio_str}_{term}.csv"
    parts = [dataset_name, pattern_key]
    if variant_key:
        parts.append(variant_key)
    if block_length is not None and pattern_key in {"BM", "TM"}:
        parts.append(f"length{block_length}")
    parts.extend([ratio_str, term])
    return "_".join(parts) + ".csv"

def _inject_for_column(
    df: pd.DataFrame,
    col: str,
    start_idx: int,
    end_idx: int,
    ranges: Sequence[Tuple[int, int]],
    block_length: int,
    n_blocks_target: int,
    rng: np.random.Generator,
    repair_steps: int,
) -> List[dict]:
    occupied = np.zeros(end_idx - start_idx, dtype=bool)
    positions: List[dict] = []
    range_lengths = [max(0, e - s) for s, e in ranges]
    blocks_per_range = _allocate_integer(n_blocks_target, range_lengths)

    for (r_start, r_end), target_blocks in zip(ranges, blocks_per_range):
        placed_blocks = 0
        while placed_blocks < target_blocks:
            start = _place_block_random(
                occupied=occupied,
                global_start_idx=start_idx,
                layer_start=r_start,
                layer_end=r_end,
                block_length=block_length,
                rng=rng,
                trials=max(32, repair_steps * 8),
            )
            if start is None:
                break
            end = start + block_length
            df.loc[start:end - 1, col] = np.nan
            positions.append({"column": col, "start": start, "end": end, "length": block_length})
            placed_blocks += 1
    return positions


def inject_bm(
    dataset_name: str,
    injection_range: dict,
    missing_ratio: float,
    term: str,
    block_length: int = 50,
    seed: int = 42,
    mode: str = "stratified",
    balanced_contexts: Sequence[int] = DEFAULT_BALANCED_CONTEXTS,
    ratio_tolerance: float = 0.1,
    repair_steps: int = 20,
) -> Tuple[pd.DataFrame, dict]:
    data_path = injection_range.get("data_path", "data/datasets")
    csv_path = Path(data_path) / "ori" / f"{dataset_name}.csv"
    df = pd.read_csv(csv_path)

    start_idx = int(injection_range["start_index"])
    end_idx = int(injection_range["end_index"])
    injection_length = end_idx - start_idx

    data_cols = _data_columns(df)

    total_target_missing = int(round(injection_length * len(data_cols) * missing_ratio))
    total_target_blocks = max(0, total_target_missing // block_length)
    blocks_per_col = _allocate_integer(total_target_blocks, [1.0] * len(data_cols))

    seed_offset = hash(f"{dataset_name}_{term}_{missing_ratio}_BM_{mode}") % 10000
    rng = np.random.default_rng(seed + seed_offset)

    if mode == "stratified":
        ranges = _build_stratified_ranges(
            dataset_name=dataset_name,
            term=term,
            data_path=data_path,
            start_idx=start_idx,
            end_idx=end_idx,
            balanced_contexts=balanced_contexts,
        )
    else:
        ranges = [(start_idx, end_idx)]

    block_positions: List[dict] = []
    for col, n_blocks in zip(data_cols, blocks_per_col):
        if n_blocks <= 0:
            continue
        positions = _inject_for_column(
            df=df,
            col=col,
            start_idx=start_idx,
            end_idx=end_idx,
            ranges=ranges,
            block_length=block_length,
            n_blocks_target=n_blocks,
            rng=rng,
            repair_steps=repair_steps,
        )
        block_positions.extend(positions)

    injection_area_size = injection_length * len(data_cols)
    injected_count = int(df.iloc[start_idx:end_idx][data_cols].isna().sum().sum())
    actual_missing_ratio = injected_count / injection_area_size if injection_area_size > 0 else 0.0

    context_stats = _context_stats(
        df=df,
        data_cols=data_cols,
        dataset_name=dataset_name,
        term=term,
        data_path=data_path,
        start_idx=start_idx,
        end_idx=end_idx,
        balanced_contexts=balanced_contexts,
    )
    lower = missing_ratio * (1 - ratio_tolerance)
    upper = missing_ratio * (1 + ratio_tolerance)
    within_tolerance = all(lower <= s["missing_ratio"] <= upper for s in context_stats) if context_stats else True

    info = {
        "dataset_name": dataset_name,
        "term": term,
        "missing_ratio": missing_ratio,
        "block_length": block_length,
        "mode": mode,
        "n_blocks": len(block_positions),
        "total_cells": injection_area_size,
        "injected_missing": injected_count,
        "actual_missing_ratio": actual_missing_ratio,
        "injection_range": {"start_index": start_idx, "end_index": end_idx, "length": injection_length},
        "balanced_contexts": list(sorted(set(balanced_contexts))),
        "ratio_tolerance": ratio_tolerance,
        "repair_steps": repair_steps,
        "within_tolerance": within_tolerance,
        "context_stats": context_stats,
        "block_positions": block_positions,
        "data_columns": data_cols,
    }
    return df, info


def save_dataset(
    df: pd.DataFrame,
    dataset_name: str,
    missing_ratio: float,
    term: str,
    output_base_dir: str = "data/datasets",
    block_length: int = 50,
    pattern: str = "BM",
    variant: str | None = None,
) -> str:
    ratio_str = f"{int(missing_ratio * 100):03d}"
    pattern_key = pattern.upper()
    output_dir = Path(output_base_dir) / pattern_key / f"{pattern_key}_{ratio_str}"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_filename = build_missing_filename(
        dataset_name=dataset_name,
        pattern=pattern_key,
        missing_ratio=missing_ratio,
        term=term,
        variant=variant,
        block_length=block_length,
    )
    output_path = output_dir / output_filename
    df.to_csv(output_path, index=False)
    return str(output_path)


def get_available_terms(dataset_name: str, data_path: str = "data/datasets") -> List[str]:
    props = load_dataset_properties(data_path)
    if dataset_name not in props:
        raise ValueError(f"Dataset '{dataset_name}' not found in properties")
    ds_term = props[dataset_name].get("term", "med_long")
    return ["short"] if ds_term == "short" else ["short", "medium", "long"]


def run_bm_injection(
    dataset_name: str,
    missing_ratios: List[float],
    terms: List[str],
    data_path: str = "data/datasets",
    output_base_dir: str = "data/datasets",
    block_length: int = 50,
    max_context: int = 8192,
    seed: int = 42,
    mode: str = "stratified",
    pattern: str = "BM",
    variant: str | None = None,
    balanced_contexts: Sequence[int] = DEFAULT_BALANCED_CONTEXTS,
    ratio_tolerance: float = 0.1,
    repair_steps: int = 20,
) -> List[dict]:
    data_path = str(Path(data_path))
    effective_max_context = max(max_context, max(balanced_contexts) if balanced_contexts else max_context)
    results = []
    for term in terms:
        print(f"\n获取数据集 '{dataset_name}' ({term}) 的注错区间...")
        injection_range = get_injection_range(dataset_name=dataset_name, term=term, data_path=data_path, max_context=effective_max_context)
        injection_range["data_path"] = data_path
        print(f"  注错区间：[{injection_range['start_index']}, {injection_range['end_index']})")
        print(f"  注错区间长度：{injection_range['end_index'] - injection_range['start_index']}")

        for missing_ratio in missing_ratios:
            print(f"\n{'=' * 80}")
            print(f"注入：pattern={pattern.upper()}, variant={variant or 'auto'}, term={term}, missing_ratio={missing_ratio:.2%}, mode={mode}")
            if pattern.upper() in {"BM", "TM"}:
                print(f"  块长度：{block_length}")
            print(f"{'=' * 80}")

            df_injected, info = inject_missing(
                dataset_name=dataset_name,
                injection_range=injection_range,
                missing_ratio=missing_ratio,
                term=term,
                pattern=pattern,
                variant=variant,
                block_length=block_length,
                seed=seed,
                mode=mode,
                balanced_contexts=balanced_contexts,
                ratio_tolerance=ratio_tolerance,
                repair_steps=repair_steps,
            )

            effective_variant = info.get("variant", variant)
            output_path = save_dataset(
                df=df_injected,
                dataset_name=dataset_name,
                missing_ratio=missing_ratio,
                term=term,
                output_base_dir=output_base_dir,
                block_length=block_length,
                pattern=pattern,
                variant=effective_variant,
            )
            info["output_path"] = output_path
            info["original_path"] = str(Path(data_path) / "ori" / f"{dataset_name}.csv")
            info["pattern"] = pattern.upper()
            info["variant"] = effective_variant

            print("\n注入结果:")
            print(f"  总单元格数：{info['total_cells']}")
            print(f"  块数量：{info['n_blocks']}")
            print(f"  注入缺失值数：{info['injected_missing']}")
            print(f"  实际缺失比例：{info['actual_missing_ratio']:.2%}")
            print(f"  五区间约束达标：{info['within_tolerance']}")
            print("\n文件保存:")
            print(f"  {output_path}")
            print("=" * 80)
            results.append(info)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BM（块缺失）缺失值注入")
    parser.add_argument("--dataset", type=str, required=True, help="数据集名称（如 ETTh1）")
    parser.add_argument("--missing_ratio", type=str, required=True, help="缺失比例，支持单个值或逗号分隔列表")
    parser.add_argument("--term", type=str, default=None, choices=["short", "medium", "long"], help="预测 horizon 类型")
    parser.add_argument("--data_path", type=str, default="data/datasets", help="数据集目录")
    parser.add_argument("--output_dir", type=str, default="data/datasets", help="输出目录")
    parser.add_argument("--block_length", type=int, default=50, help="块长度")
    parser.add_argument("--max_context", type=int, default=8192, help="最大回顾窗口长度")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    parser.add_argument("--mode", type=str, default="stratified", choices=["stratified", "random"], help="注空模式")
    parser.add_argument("--pattern", type=str, default="BM", choices=["BM", "MCAR", "TM", "TVMR", "PERIODIC", "PEAK", "CHANGE"], help="missing pattern")
    parser.add_argument("--variant", type=str, default=None, help="missing variant, e.g. point/front/fixed")
    parser.add_argument("--balanced_contexts", type=str, default="512,2048,2880,4096,8192", help="stratified 模式的 context 列表")
    parser.add_argument("--ratio_tolerance", type=float, default=0.1, help="允许相对偏差（默认 0.1）")
    parser.add_argument("--repair_steps", type=int, default=20, help="随机搜索尝试系数（默认 20）")
    parser.add_argument("--no_auto_term", action="store_true", help="禁用自动 term 检测，使用 --term 指定值")
    args = parser.parse_args()

    if args.data_path == "datasets":
        args.data_path = str(Path(__file__).resolve().parents[2] / "data" / "datasets")
    if args.output_dir == "datasets":
        args.output_dir = str(Path(__file__).resolve().parents[2] / "data" / "datasets")

    missing_ratios = parse_missing_ratios(args.missing_ratio)
    balanced_contexts = parse_int_list(args.balanced_contexts)
    if args.no_auto_term:
        terms = [args.term] if args.term else ["short"]
        print(f"使用指定的 term: {terms}")
    else:
        terms = get_available_terms(args.dataset, args.data_path)
        print(f"自动检测到数据集 '{args.dataset}' 的 term 配置：{terms}")

    results = run_bm_injection(
        dataset_name=args.dataset,
        missing_ratios=missing_ratios,
        terms=terms,
        data_path=args.data_path,
        output_base_dir=args.output_dir,
        block_length=args.block_length,
        max_context=args.max_context,
        seed=args.seed,
        mode=args.mode,
        pattern=args.pattern,
        variant=args.variant,
        balanced_contexts=balanced_contexts,
        ratio_tolerance=args.ratio_tolerance,
        repair_steps=args.repair_steps,
    )

    print(f"\n{'=' * 80}")
    print(f"批量注入完成！共生成 {len(results)} 个文件:")
    print(f"{'=' * 80}")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['output_path']}")
    print(f"{'=' * 80}\n")
