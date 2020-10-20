from typing import Dict, List, Optional

import more_itertools


def simplify(series: List[Dict], key: str, order: int) -> List[Dict]:
    if not order:
        return series

    items: List[Optional[Dict]] = series[:]
    for i1, i2, i3 in more_itertools.windowed(range(len(series)), 3):
        if None not in (i1, i2, i3):
            c1 = series[i1][key]
            c2 = series[i2][key]
            c3 = series[i3][key]
            if c1 < c2 < c3:
                items[i2] = None
            elif c1 > c2 > c3:
                items[i2] = None
    return [item for item in items if item]
