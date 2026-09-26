"""计算各方法排名，支持指定模型"""
import pandas as pd
from pathlib import Path
import sys

model_name = sys.argv[1] if len(sys.argv) > 1 else "chronos2"

datasets = sorted(p.stem for p in (Path('data/datasets/ori').glob('*.csv')))
methods = ['linear','mean','forward','backward','gp_rbf','kalman_arima','kalman_struct','saits',f'{model_name}_forecast']
ratios = ['010','020','030']

def get_smape(fp):
    if not fp.exists(): return None
    try:
        d = pd.read_csv(fp)
        row = d[d['metric']=='sMAPE[0.5]']
        return float(row['value'].iloc[0]) if len(row) else None
    except: return None

rank_counts = {m: {} for m in methods}
n_pairs = 0

for ds in datasets:
    for r in ratios:
        scores = {}
        for m in methods:
            fp = Path(f'artifacts/legacy_eval/results/{model_name}/impute/{m}_{ds}_BM_length50_{r}_short_results.csv')
            v = get_smape(fp)
            if v is not None:
                scores[m] = v
        if len(scores) < 2:
            continue
        n_pairs += 1
        sorted_m = sorted(scores, key=scores.get)
        for rank, m in enumerate(sorted_m, 1):
            rc = rank_counts[m]
            rc['total'] = rc.get('total', 0) + 1
            rc[rank] = rc.get(rank, 0) + 1

def safe(k, d, default=0):
    return d.get(k, default)

print(f'Model: {model_name}  |  Total pairs: {n_pairs}')
print()
print(f'{"Method":25s} | {"AvgRank":>7s} | {"Top3%":>6s} | {"1st":>5s} | {"2nd":>5s} | {"3rd":>5s}')
print('-' * 65)

for m in sorted(methods, key=lambda x: (sum(k*safe(k,rank_counts[x]) for k in range(1,10))/max(safe('total',rank_counts[x]),1))):
    rc = rank_counts[m]
    total = safe('total', rc)
    if total == 0: continue
    avg_rank = sum(k * safe(k, rc) for k in range(1, 10)) / total
    top3 = safe(1, rc) + safe(2, rc) + safe(3, rc)
    top3_rate = top3 / total * 100
    print(f'{m:25s} | {avg_rank:6.2f} | {top3_rate:5.1f}% | {safe(1,rc):3d} | {safe(2,rc):3d} | {safe(3,rc):3d}')
