from collections import deque
from typing import List, Sized, Iterable

from more_itertools import windowed

from src import tool, schema


def i_windowed(sized: Sized, size: int):
    return windowed(range(len(sized)), size)


def clean(series: List[tool.Clazz]):
    required = ['_id', '_rev', '_key'] + schema.SECURITY_SCHEMA['rule']['required']
    for i, s in enumerate(series):
        series[i] = tool.Clazz({k: v for k, v in s.items() if k in required})


def reduce(series: List[tool.Clazz], limit: float) -> Iterable[tool.Clazz]:
    if series and limit > 0:
        limit = series[-1].close / 100 * limit
    else:
        return series

    queue = deque()
    for s in reversed(series):
        if len(queue) >= 2:
            close1, close2, close3 = queue[1].close, queue[0].close, s.close

            delta12 = close1 - close2
            delta23 = close2 - close3

            if delta12 > 0:
                if delta23 > 0:
                    queue[0] = s
                elif delta23 < -limit:
                    queue.appendleft(s)
            if delta12 < 0:
                if delta23 < 0:
                    queue[0] = s
                elif delta23 > limit:
                    queue.appendleft(s)
        else:
            queue.appendleft(s)
    return queue


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
