from typing import List, Sized

from more_itertools import windowed

from src import tool, schema


def i_windowed(sized: Sized, size: int):
    return windowed(range(len(sized)), size)


def clean(series: List[tool.Clazz]):
    required = ['_id', '_rev', '_key'] + schema.SECURITY_SCHEMA['rule']['required']
    for i, s in enumerate(series):
        series[i] = tool.Clazz({k: v for k, v in s.items() if k in required})


def reduce(series: List[tool.Clazz], max_grade: int) -> List[tool.Clazz]:
    min_spikes: List[int] = []
    max_spikes: List[int] = []
    w_size = 3
    if len(series) >= w_size:
        closes = [s.close for s in series]
        min_val = min(closes)
        max_val = max(closes)
        grade = (max_val - min_val) / max_grade
        for i1, i2, i3 in i_windowed(series, w_size):
            c1 = series[i1].close
            c2 = series[i2].close
            c3 = series[i3].close
            if c2 == min(c1, c2, c3):
                min_spikes = [i for i in min_spikes if series[i] > c2]
                min_spikes.append(i2)
            if c2 == max(c1, c2, c3):
                max_spikes = [i for i in max_spikes if series[i] < c2]
                max_spikes.append(i2)
        return series
    return series


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
