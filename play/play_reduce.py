from collections import deque
from typing import List, Iterable

import matplotlib.pyplot as plt

from src import tool, yahoo


def read_data(begin: int, end: int) -> List[tool.Clazz]:
    interval = tool.INTERVAL_1D
    with yahoo.SecuritySeries(interval) as security_series:
        abc_series = security_series['ABC.NYSE']
        print(abc_series[-1].timestamp)
        abc_series = [s for s in abc_series if begin <= s.timestamp <= end]
    for s in abc_series:
        s.grade = 0.0
        s.timestamp /= 1e6
    return abc_series


def plot_series(series: Iterable[tool.Clazz], grade: float, label: str, color: str, style='-'):
    series = [s for s in series if s.grade >= grade]
    timestamps = [s.timestamp for s in series]
    closes = [s.close for s in series]
    plt.plot(timestamps, closes, style, label=label, color=color, linewidth=1, markersize=2)


def reduce(series: List[tool.Clazz], limit: float) -> Iterable[tool.Clazz]:
    if series and limit > 0:
        limit *= series[-1].close / 100
    else:
        return series

    queue = deque()  # reversed to series
    for s in reversed(series):
        if len(queue) >= 2:
            close1, close2, close3 = queue[1].close, queue[0].close, s.close

            delta12 = close1 - close2
            delta23 = close2 - close3

            if delta12 > 0:
                if delta23 > 0:
                    queue[0] = s
                elif delta23 < -limit:
                    queue.appendleft(s)
            if delta12 < 0:
                if delta23 < 0:
                    queue[0] = s
                elif delta23 > limit:
                    queue.appendleft(s)
        else:
            queue.appendleft(s)
    return queue


def show(begin: int, end: int, limit: float):
    abc_series = read_data(begin, end)
    plot_series(abc_series, 0.0, 'ABC', 'grey')

    reduced = reduce(abc_series, limit)
    plot_series(reduced, 0.0, 'reduced', 'blue', 'o')

    plt.legend(loc='upper left')
    plt.grid()
    plt.tight_layout()
    plt.show()


def execute():
    show(1514851200, 1606953600, 4)


if __name__ == '__main__':
    execute()
