from typing import List, Optional, Sized

from more_itertools import windowed

from src import tool


def i_windowed(sized: Sized, size: int):
    return windowed(range(len(sized)), size)


def reduce_3_points(series: List[tool.Clazz]) -> List[tool.Clazz]:
    w_size = 3
    if len(series) < w_size:
        return series
    reduced: List[Optional[tool.Clazz]] = series[:]
    for i1, i2, i3 in i_windowed(series, w_size):
        c1 = series[i1].close
        c2 = series[i2].close
        c3 = series[i3].close
        if c1 <= c2 <= c3:
            reduced[i2] = None
            if c1 == c3:
                reduced[i1] = None
        elif c1 >= c2 >= c3:
            reduced[i2] = None
            if c1 == c3:
                reduced[i1] = None
    return [r for r in reduced if r]


def reduce_4_points(series: List[tool.Clazz]) -> List[tool.Clazz]:
    w_size = 4
    if len(series) < w_size:
        return series
    reduced: List[Optional[tool.Clazz]] = series[:]
    for i1, i2, i3, i4 in i_windowed(series, w_size):
        c1 = series[i1].close
        c2 = series[i2].close
        c3 = series[i3].close
        c4 = series[i4].close
        if c1 <= c3 <= c2 <= c4:
            reduced[i2] = None
            reduced[i3] = None
        elif c1 >= c3 >= c2 >= c4:
            reduced[i2] = None
            reduced[i3] = None
    return [r for r in reduced if r]


def set_order(reduced: List[tool.Clazz], order: int):
    for r in reduced:
        r.order = order


def reduce(series: List[tool.Clazz], max_order: int) -> List[tool.Clazz]:
    reduced = reduce_3_points(series)
    set_order(reduced, 1)
    for o in range(2, max_order + 1):
        reduced = reduce_4_points(reduced)
        reduced = reduce_3_points(reduced)
        set_order(reduced, o)
    return reduced


def sma(series: List[tool.Clazz], w_size: int):
    if len(series) < w_size:
        return series
    for window in windowed(series, w_size):
        closes = [s.close for s in window]
        window[-1].sma = sum(closes) / w_size


def vma(series: List[tool.Clazz], w_size: int):
    if len(series) < w_size:
        return series
    for window in windowed(series, w_size):
        weighted_closes = [s.close * s.volume for s in window]
        volumes = [s.volume for s in window]
        window[-1].vma = sum(weighted_closes) / sum(volumes)
