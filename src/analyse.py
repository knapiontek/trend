from collections import deque
from typing import List

from more_itertools import windowed

from src import tool, schema


def clean(series: List[tool.Clazz]):
    required = ['_id', '_rev', '_key'] + schema.SECURITY_SCHEMA['rule']['required']
    for i, s in enumerate(series):
        series[i] = tool.Clazz({k: v for k, v in s.items() if k in required})


def reduce(series: List[tool.Clazz], score: int) -> List[tool.Clazz]:
    queue = deque(series[:2])

    for s in series[2:]:
        y1, y2, y3 = queue[-2].close, queue[-1].close, s.close

        delta12 = y1 - y2
        delta23 = y2 - y3

        scope = (2 ** score) / 100 * y2

        if delta12 > 0:
            if delta23 > 0:
                queue[-1] = s
            elif delta23 < -scope:
                queue.append(s)

        if delta12 < 0:
            if delta23 < 0:
                queue[-1] = s
            elif delta23 > scope:
                queue.append(s)

    if queue[-1] != series[-1]:
        queue.append(series[-1])  # first and last element are always in
    return list(queue)


def sma(series: List[tool.Clazz], w_size: int):
    if len(series) >= w_size:
        name = f'sma-{w_size}'
        for window in windowed(series, w_size):
            last = window[-1]
            if name not in last:
                closes = [s.close for s in window]
                last[name] = sum(closes) / w_size
    return series


def vma(series: List[tool.Clazz], w_size: int):
    if len(series) >= w_size:
        name = f'vma-{w_size}'
        for window in windowed(series, w_size):
            last = window[-1]
            if name not in last:
                weighted_closes = [s.close * s.volume for s in window]
                volumes = [s.volume for s in window]
                sum_volumes = sum(volumes)
                if sum_volumes:
                    last[name] = sum(weighted_closes) / sum_volumes
    return series
