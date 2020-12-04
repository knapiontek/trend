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


def plot_series(series: Iterable[tool.Clazz], label: str, score: int = 0):
    colors = ['grey', 'olive', 'green', 'blue', 'orange', 'red', 'brown', 'black']
    color = colors[score]
    timestamps = [s.timestamp for s in series]
    closes = [s.close for s in series]
    style = 'o' if score else '-'
    plt.plot(timestamps, closes, style, label=f'{label}-{score}', color=color, linewidth=1, markersize=1 + score)


def reduce(series: List[tool.Clazz], score: int) -> List[tool.Clazz]:
    queue = deque()  # reversed to series

    for s in reversed(series):
        if len(queue) >= 2:
            close1, close2, close3 = queue[1].close, queue[0].close, s.close

            delta12 = close1 - close2
            delta23 = close2 - close3
            scope = (2 ** score) / 100 * close2

            if delta12 > 0:
                if delta23 > 0:
                    queue[0] = s
                elif delta23 < -scope:
                    queue.appendleft(s)
            if delta12 < 0:
                if delta23 < 0:
                    queue[0] = s
                elif delta23 > scope:
                    queue.appendleft(s)
        else:
            queue.appendleft(s)

    result = list(queue)
    if len(result) > 2:
        for s in result:
            s.score = score
    return result


def show(begin: int, end: int):
    abc_series = read_data(begin, end)
    plot_series(abc_series, 'ABC')

    for score in range(1, 8):
        abc_series = reduce(abc_series, score)
        if len(abc_series) > 2:
            plot_series(abc_series, 'score', score)

    plt.legend(loc='upper left')
    plt.grid()
    plt.tight_layout()
    plt.show()


def execute():
    show(1514851200, 1606953600)


if __name__ == '__main__':
    execute()
