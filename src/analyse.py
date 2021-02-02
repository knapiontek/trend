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
    total - total cash required for all open positions
    long - cash required for single long position
    open_timestamp - timestamp at the opening
    volume - number of all opened longs
    """
    profit = total = long = 0.0
    open_timestamp = volume = 0

    for s in series:
        if (long == 0.0) and (4 <= s.low_score):
            open_timestamp = s.timestamp
            long = s.long = s.close

            total += long
            volume += 1

        elif (long > 0.0) and (2 <= s.low_score):
            s.open_timestamp = open_timestamp
            s.open_long = long
            s.short = s.close
            s.profit = s.short - s.open_long
            long = 0.0

            profit += s.profit

    return Clazz(profit=profit, total=total, volume=volume)
