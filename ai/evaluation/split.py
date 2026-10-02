"""Train/test splitting by battery identity (never by row) so one battery cannot sit on both sides — avoids leakage."""
from __future__ import annotations

import random
from typing import Sequence


def group_split(groups: Sequence[str], test_fraction: float = 0.3, seed: int = 0):
    """-> (train_idx, test_idx).  Whole groups (batteries) go to one side.  Needs >= 2 groups."""
    ids = sorted(set(groups))
    if len(ids) < 2:
        raise ValueError("need at least 2 distinct batteries to split")
    rng = random.Random(seed)
    rng.shuffle(ids)
    n_test = min(len(ids) - 1, max(1, round(len(ids) * test_fraction)))
    test_ids = set(ids[:n_test])
    tr = [i for i, g in enumerate(groups) if g not in test_ids]
    te = [i for i, g in enumerate(groups) if g in test_ids]
    assert not ({groups[i] for i in tr} & {groups[i] for i in te})
    return tr, te


def regression_metrics(y_true, y_pred) -> dict:
    n = len(y_true)
    err = [p - t for t, p in zip(y_true, y_pred)]
    mae = sum(abs(e) for e in err) / n
    rmse = (sum(e * e for e in err) / n) ** 0.5
    mean = sum(y_true) / n
    ss_tot = sum((t - mean) ** 2 for t in y_true)
    r2 = None if ss_tot == 0 else 1 - sum(e * e for e in err) / ss_tot
    return {"n": n, "mae": mae, "rmse": rmse, "r2": r2}
