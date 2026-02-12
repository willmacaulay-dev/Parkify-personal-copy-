from __future__ import annotations
from typing import Deque, Iterable, Optional, Tuple

Sample = Tuple[str, int, int, int]  # (gid, t_epoch, available, occupied)


def predict_available( history: Deque[Tuple[str, int, int, int]], capacity: int, horizon_min: int = 30 ):

    data = list(history)

    # no history
    if not data:
        return None

    _, t1, a1, _ = data[-1]
    curr = int(a1)

    # insufficient history
    if len(data) < 2:
        return clamp(curr, capacity)

    _, t0, a0, _ = data[0]
    t0, a0 = int(t0), int(a0)
    t1 = int(t1)

    dt = t1 - t0
    if dt <= 0:
        return clamp(curr, capacity)

    rate = (curr - a0) / dt
    pred = curr + rate * (horizon_min * 60)

    return clamp(int(round(pred)), capacity)

# clamp to 0, capacity
def clamp(x: int, capacity: int):
    if x < 0:
        x = 0
    if capacity is not None and x > capacity:
        x = int(capacity)
    return x
