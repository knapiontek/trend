from collections import deque
from typing import List, Iterable

import matplotlib.pyplot as plt

from src import tool, yahoo
from src.clazz import Clazz


def show_widget():
    plt.title('Swings')
    plt.legend(loc='upper left')
    plt.grid()
    plt.tight_layout()
    plt.show()


def plot_series(series: List[Clazz]):
    plt.plot([s.x for s in series], [s.y for s in series], '-', label='series', color='grey', linewidth=1)


def plot_swings(series: List[Clazz], score: int = 0):
    colors = ['grey', 'olive', 'green', 'blue', 'orange', 'red', 'brown', 'black']
    color = colors[score]
    plt.plot([s.x for s in series],
             [s.y for s in series],
             'o', label=f'score-{score}', color=color, linewidth=1, markersize=1 + score)


def read_series(begin: int, end: int) -> List[Clazz]:
    interval = tool.INTERVAL_1D
    with yahoo.SecuritySeries(interval) as security_series:
        abc_series = security_series['ABC.NYSE']
        return [Clazz(x=s.timestamp / 1e6, y1=s.low, y2=s.high)
                for s in abc_series if begin <= s.timestamp <= end]


def avg_val(series: List[Clazz]):
    return sum([s.y for s in series]) / len(series)


def avg_series(series: Iterable[Clazz]):
    return [Clazz(x=s.x, y=(s.y1 + s.y2) / 2) for s in series]


def reduce_series(series: List[Clazz], score: int) -> List[Clazz]:
    scope = (2 ** score) / 100 * avg_val(series)
    queue = deque(series[:2])

    for s in series[2:]:
        y1, y2, y3 = queue[-2].y, queue[-1].y, s.y

        delta12 = y1 - y2
        delta23 = y2 - y3

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
    for s in output[1:]:
        s.score = score
    return output


def show_swings(begin: int, end: int):
    series = read_series(begin, end)
    avg = avg_series(series)
    plot_series(avg)

    reduced = avg
    for score in range(0, 8):
        reduced = reduce_series(reduced, score)
        if len(reduced) > 2:
            plot_swings(reduced, score)

    show_widget()


def show_deals(begin: int, end: int):
    series = read_series(begin, end)
    avg = avg_series(series)
    plot_series(avg)

    reduced = avg
    for score in range(0, 8):
        reduced = reduce_series(reduced, score)

    score = 3
    swings = [s for s in avg if s.get('score', 0) >= score]
    plot_swings(swings, score)

    show_widget()


def execute():
    show_deals(1514851200, 1607644800)


if __name__ == '__main__':
    execute()
