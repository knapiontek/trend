from typing import List

from src import schema
from src.clazz import Clazz


def clean(series: List[Clazz]):
    required = ['_id', '_rev', '_key'] + schema.SECURITY_SCHEMA['rule']['required']
    for i, s in enumerate(series):
        series[i] = Clazz({k: v for k, v in s.items() if k in required})


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


def action(series: List[Clazz]) -> Clazz:
    """
    profit - total profit or loss
    total - total cash required for all openings
    position - cash required for single position
    open_timestamp - timestamp at the opening
    volume - number of all opened positions
    """
    profit = total = position = 0.0
    open_timestamp = volume = 0

    for s in series:
        if (position == 0.0) and (-3 <= s.low_score):
            open_timestamp = s.timestamp
            position = s.action = s.close
            total += position
            volume += 1

        elif (position > 0.0) and (-1 <= s.low_score):
            s.action = -s.close
            s.open_timestamp = open_timestamp
            s.open_position = position
            s.profit = s.close - position
            profit += s.profit
            position = 0.0

    return Clazz(profit=profit, total=total, volume=volume)
