from collections import deque
from typing import List

from src.clazz import Clazz


def windowed(series: List, w_size: int):
    if len(series) >= w_size:
        q = deque(series[:w_size])
        yield tuple(q)
        for s in series[w_size:]:
            q.rotate(-1)
            q[-1] = s
            yield tuple(q)


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
