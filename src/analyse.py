from collections import deque
from typing import List

from src import schema
from src.clazz import Clazz


def windowed(series: List, w_size: int):
    if len(series) >= w_size:
        q = deque(series[:w_size])
        yield tuple(q)
        for s in series[w_size:]:
            q.rotate(-1)
            q[-1] = s
            yield tuple(q)


def clean(series: List[Clazz]):
    required = ['_id', '_rev', '_key'] + schema.SECURITY_SCHEMA['rule']['required']
    for i, s in enumerate(series):
        series[i] = Clazz({k: v for k, v in s.items() if k in required})


def reduce(series: List[Clazz], score: int) -> List[Clazz]:
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


def sma(series: List[Clazz], w_size: int):
    if len(series) >= w_size:
        sma_name = f'sma-{w_size}'
        sum_value = sum([s.close for s in series[:w_size]])
        series[w_size - 1][sma_name] = sum_value / w_size
        for s1, s2 in zip(series[w_size:], series):
            sum_value += s1.close - s2.close
            s1[sma_name] = sum_value / w_size


def vma(series: List[Clazz], w_size: int):
    if len(series) >= w_size:
        vma_name = f'vma-{w_size}'
        sum_value = sum([s.close * s.volume for s in series[:w_size]])
        sum_volume = sum([s.volume for s in series[:w_size]])
        if sum_volume:
            series[w_size - 1][vma_name] = sum_value / sum_volume
        for s1, s2 in zip(series[w_size:], series):
            sum_value += (s1.close * s1.volume) - (s2.close * s2.volume)
            sum_volume += s1.volume - s2.volume
            if sum_volume:
                s1[vma_name] = sum_value / sum_volume


def action_vma(series: List[Clazz]) -> float:
    w_size = 100
    vma_name = f'vma-{w_size}'

    profit = position = 0.0
    open_timestamp = 0

    for s1, s2 in windowed(series, 2):
        vma_value = s2.get(vma_name)
        if vma_value:
            # long
            if s1.close < vma_value < s2.close:
                if position < 0.0:  # close short
                    s2.action = s2.close
                    s2.open_timestamp = open_timestamp
                    s2.open_position = position
                    s2.profit = -position - s2.close
                    profit += s2.profit
                    position = 0.0
                elif position == 0.0:  # open long
                    position = s2.action = s2.close
                    open_timestamp = s2.timestamp
            # short
            if s2.close < vma_value < s1.close:
                if position > 0.0:  # close long
                    s2.action = -s2.close
                    s2.open_timestamp = open_timestamp
                    s2.open_position = position
                    s2.profit = s2.close - position
                    profit += s2.profit
                    position = 0.0
                elif position == 0.0:  # open short
                    position = s2.action = -s2.close
                    open_timestamp = s2.timestamp

    return profit


def action(series: List[Clazz]) -> float:
    profit = position = 0.0
    open_timestamp = 0

    for s in series:

        # open long
        if position == 0.0 and s.candidate == -3:
            position = s.action = s.close
            open_timestamp = s.timestamp

        # close long
        if position > 0.0 and s.candidate == -1:
            s.action = -s.close
            s.open_timestamp = open_timestamp
            s.open_position = position
            s.profit = s.close - position
            profit += s.profit
            position = 0.0

    return profit
