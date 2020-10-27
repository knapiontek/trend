from typing import Dict, List, Optional, Sized

from more_itertools import windowed


def i_windowed(sized: Sized, size: int):
    return windowed(range(len(sized)), size)


def simplify_3_points(series: List[Dict], key: str) -> List[Dict]:
    reduced: List[Optional[Dict]] = series[:]
    for i1, i2, i3 in i_windowed(series, 3):
        c1 = series[i1][key]
        c2 = series[i2][key]
        c3 = series[i3][key]
        if c1 <= c2 <= c3:
            reduced[i2] = None
            if c1 == c3:
                reduced[i1] = None
        elif c1 >= c2 >= c3:
            reduced[i2] = None
            if c1 == c3:
                reduced[i1] = None
    return [s for s in reduced if s]


def simplify_4_points(series: List[Dict], key: str) -> List[Dict]:
    reduced: List[Optional[Dict]] = series[:]
    for i1, i2, i3, i4 in i_windowed(series, 4):
        c1 = series[i1][key]
        c2 = series[i2][key]
        c3 = series[i3][key]
        c4 = series[i4][key]
        if c1 <= c3 <= c2 <= c4:
            reduced[i2] = None
            reduced[i3] = None
        elif c1 >= c3 >= c2 >= c4:
            reduced[i2] = None
            reduced[i3] = None
    return [s for s in reduced if s]


def simplify(series: List[Dict], key: str, order: int) -> List[Dict]:
    if not order:
        return series
    reduced = simplify_3_points(series, key)
    for o in range(order - 1):
        reduced = simplify_4_points(reduced, key)
        reduced = simplify_3_points(reduced, key)
    return reduced


def sma(series: List[Dict], w_size: int) -> List[Dict]:
    result = []
    for window in windowed(series, w_size):
        closes = [s['close'] for s in window]
        timestamp = window[-1]['timestamp']
        dt = dict(sma=sum(closes) / w_size, timestamp=timestamp)
        result.append(dt)
    return result


def vma(series: List[Dict], w_size: int) -> List[Dict]:
    result = []
    for window in windowed(series, w_size):
        weight_closes = [s['close'] * s['volume'] for s in window]
        volumes = [s['volume'] for s in window]
        timestamp = window[-1]['timestamp']
        dt = dict(vma=sum(weight_closes) / sum(volumes), timestamp=timestamp)
        result.append(dt)
    return result
