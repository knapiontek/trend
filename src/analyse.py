from collections import deque
from typing import List

import more_itertools

from src import tool, schema


def windowed(series: List[tool.Clazz], w_size: int):
    for window in more_itertools.windowed(series, w_size):
        if None not in window:
            yield window


def clean(series: List[tool.Clazz]):
    required = ['_id', '_rev', '_key'] + schema.SECURITY_SCHEMA['rule']['required']
    for i, s in enumerate(series):
        series[i] = tool.Clazz({k: v for k, v in s.items() if k in required})


def reduce(series: List[tool.Clazz], score: int) -> List[tool.Clazz]:
    if score is None:
        return series

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
    sma_name = f'sma-{w_size}'
    for window in windowed(series, w_size):
        last = window[-1]
        if sma_name not in last:
            closes = [s.close for s in window]
            last[sma_name] = sum(closes) / w_size


def vma(series: List[tool.Clazz], w_size: int):
    vma_name = f'vma-{w_size}'
    for window in windowed(series, w_size):
        last = window[-1]
        if vma_name not in last:
            weighted_closes = [s.close * s.volume for s in window]
            volumes = [s.volume for s in window]
            sum_volumes = sum(volumes)
            if sum_volumes:
                last[vma_name] = sum(weighted_closes) / sum_volumes


def action(series: List[tool.Clazz]) -> float:
    w_size = 100
    vma_name = f'vma-{w_size}'

    profit = position = 0.0
    for s1, s2 in windowed(series[w_size - 1:], 2):
        vma_value = s2[vma_name]

        s2.action = s2.profit = None

        # long
        if s1.close < vma_value < s2.close:
            if position < 0:  # close short
                s2.action = s2.close
                s2.profit = s2.close + position
                profit += s2.profit
                position = 0.0
            elif position == 0:
                position = s2.action = s2.close

        # short
        if s2.close < vma_value < s1.close:
            if position > 0:  # close long
                s2.action = s2.close
                s2.profit = s2.close - position
                profit += s2.profit
                position = 0.0
            elif position == 0:
                position = s2.action = -s2.close

    return profit
