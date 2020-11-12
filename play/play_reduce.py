from typing import List


def reduce_on_fly(series: List[float]) -> List[float]:
    if series:
        min_value = [0]
        max_value = [0]
        for i, s in enumerate(series, 1):
            if s < min_value[-1]:
                min_value.append(s)
            if s > max_value[-1]:
                max_value.append(s)
    return series
