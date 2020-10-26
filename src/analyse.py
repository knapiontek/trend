from typing import Dict, List, Optional, Sized

import more_itertools


def window(sized: Sized, size: int):
    return more_itertools.windowed(range(len(sized)), size)


def simplify_3_points(series: List[Dict], key: str) -> List[Dict]:
    reduced: List[Optional[Dict]] = series[:]
    for i1, i2, i3 in window(series, 3):
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
    for i1, i2, i3, i4 in window(series, 4):
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
