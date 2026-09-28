"""Browse historical Eval forecasts and metrics without loading forecast models."""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "artifacts/legacy_eval"
COHORT = re.compile(r"^(?P<dataset>.+)_clean_(?P<term>short|medium|long)_prediction$")


def read_metrics(path: Path) -> dict[str, str]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return {row["metric"]: row["value"] for row in csv.DictReader(handle)}


def cohorts(root: Path = LEGACY) -> list[dict]:
    records = []
    for model_dir in sorted((root / "intermediate_predictions").iterdir()):
        if not model_dir.is_dir():
            continue
        for folder in sorted(model_dir.iterdir()):
            match = COHORT.fullmatch(folder.name) if folder.is_dir() else None
            if match is None:
                raise ValueError(f"Unsupported legacy prediction directory: {folder}")
            dataset, term = match.group("dataset", "term")
            summary = root / "results" / model_dir.name / "clean" / f"{dataset}_clean_{term}_results.csv"
            metrics = read_metrics(summary) if summary.is_file() else None
            names = [p.name for p in folder.glob("*.csv")]
            prefix = f"{folder.name}_"
            indices = sorted(int(name[len(prefix):-4]) for name in names
                             if name.startswith(prefix) and name[len(prefix):-4].isdigit())
            if len(indices) != len(names) or indices != list(range(len(indices))):
                raise ValueError(f"Legacy forecast numbering changed: {folder}")
            if not indices:
                raise ValueError(f"Empty legacy prediction directory: {folder}")
            if metrics is not None and int(metrics["windows"]) != len(indices):
                raise ValueError(f"Legacy forecast count differs from metrics: {folder}")
            if metrics is None:
                first = folder / f"{folder.name}_0.csv"
                with first.open(encoding="utf-8-sig", newline="") as handle:
                    horizon = sum(1 for _ in csv.DictReader(handle))
            else:
                horizon = int(metrics["prediction_length"])
            records.append({
                "model": model_dir.name, "dataset": dataset, "term": term,
                "horizon": horizon,
                "windows": None if metrics is None else int(metrics["windows"]),
                "prediction_count": len(indices),
                "prediction_dir": str(folder),
                "metrics_file": str(summary) if metrics is not None else None,
            })
    return records


def read_prediction(path: Path, horizon: int) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["date", "prediction"]:
            raise ValueError(f"Invalid legacy prediction columns: {path}")
        values = list(reader)
    if not values or len(values) != horizon:
        raise ValueError(f"Legacy prediction length differs from cohort: {path}")
    if any(not row["date"] or not math.isfinite(float(row["prediction"])) for row in values):
        raise ValueError(f"Invalid legacy prediction values: {path}")
    return values


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model")
    parser.add_argument("--dataset")
    parser.add_argument("--term", choices=("short", "medium", "long"))
    parser.add_argument("--window", type=int)
    parser.add_argument("--include-values", action="store_true",
                        help="Include the stored date/prediction rows for the selected window")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    if args.include_values and args.window is None:
        parser.error("--include-values requires --window")
    found = [row for row in cohorts() if
             (args.model is None or row["model"] == args.model) and
             (args.dataset is None or row["dataset"] == args.dataset) and
             (args.term is None or row["term"] == args.term)]
    if args.window is not None:
        if len(found) != 1 or not 0 <= args.window < found[0]["prediction_count"]:
            parser.error("--window requires one matching cohort and an available index")
        item = found[0]
        path = Path(item["prediction_dir"]) / f"{Path(item['prediction_dir']).name}_{args.window}.csv"
        values = read_prediction(path, item["horizon"])
        item = dict(item, prediction_file=str(path), point_count=len(values),
                    first_date=values[0]["date"], last_date=values[-1]["date"])
        if args.include_values:
            item["values"] = values
        print(json.dumps(item, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"matching_cohorts": len(found), "rows": found[:args.limit]},
                         ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
