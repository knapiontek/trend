from collections import deque
from typing import List, Iterable

import matplotlib.pyplot as plt

from src import tool, yahoo


def read_series(begin: int, end: int) -> List[tool.Clazz]:
    interval = tool.INTERVAL_1D
    with yahoo.SecuritySeries(interval) as security_series:
        abc_series = security_series['ABC.NYSE']
        return [tool.Clazz(x=s.timestamp / 1e6, y1=s.low, y2=s.high)
                for s in abc_series if begin <= s.timestamp <= end]


def avg_series(series: Iterable[tool.Clazz]):
    return [tool.Clazz(x=s.x, y=(s.y1 + s.y2) / 2) for s in series]


def flatten_series(series: Iterable[tool.Clazz]):
    series = [[tool.Clazz(x=s.x, y=s.y1), tool.Clazz(x=s.x, y=s.y2)] for s in series]
    return sum(series, [])


def plot_series(xs: List[float], ys: List[float], label: str, score: int = 0):
    colors = ['grey', 'olive', 'green', 'blue', 'orange', 'red', 'brown', 'black']
    color = colors[score]
    style = 'o' if score else '-'
    plt.plot(xs, ys, style, label=f'{label}-{score}', color=color, linewidth=1, markersize=1 + score)


def reduce_series(series: List[tool.Clazz], score: int) -> List[tool.Clazz]:
    queue = deque(series[:2])

    for s in series[2:]:
        y1, y2, y3 = queue[-2].y, queue[-1].y, s.y

        delta12 = y1 - y2
        delta23 = y2 - y3
        scope = (2 ** score) / 100 * y2

        if delta12 > 0:
            if delta23 > 0:
                queue[-1] = s
            elif delta23 < -scope:
                queue.append(s)

        if delta12 < 0:
            if delta23 < 0:
                queue[-1] = s
            elif delta23 > scope:
                queue.append(s)

    output = list(queue)
    if len(output) > 2:
        for s in output:
            s.score = score
    return output


def show_flatten(begin: int, end: int):
    min_score = 2
    series = read_series(begin, end)
    flatten = flatten_series(series)
    reduced = reduce_series(flatten, min_score)
    plot_series([s.x for s in reduced], [s.y for s in reduced], 'ABC')

    for score in range(min_score + 1, 8):
        reduced = reduce_series(reduced, score)
        if len(reduced) > 2:
            plot_series([s.x for s in reduced], [s.y for s in reduced], 'score', score)

    plt.legend(loc='upper left')
    plt.grid()
    plt.tight_layout()
    plt.show()


def show_avg(begin: int, end: int):
    series = read_series(begin, end)
    avg = avg_series(series)
    plot_series([s.x for s in avg], [s.y for s in avg], 'ABC')

    reduced = avg
    for score in range(1, 8):
        reduced = reduce_series(reduced, score)
        if len(reduced) > 2:
            plot_series([s.x for s in reduced], [s.y for s in reduced], 'score', score)

    plt.legend(loc='upper left')
    plt.grid()
    plt.tight_layout()
    plt.show()


def execute():
    show_avg(1514851200, 1607644800)


if __name__ == '__main__':
    execute()
