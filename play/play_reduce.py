from collections import deque
from typing import List, Iterable, Tuple

import matplotlib.pyplot as plt

from src import tool, yahoo


def read_series(begin: int, end: int) -> List[tool.Clazz]:
    interval = tool.INTERVAL_1D
    with yahoo.SecuritySeries(interval) as security_series:
        abc_series = security_series['ABC.NYSE']
        return [tool.Clazz(x=s.timestamp / 1e6, y1=s.low, y2=s.high)
                for s in abc_series if begin <= s.timestamp <= end]


def average(series: List[tool.Clazz]):
    return sum([s.y for s in series]) / len(series)


def mid_series(series: Iterable[tool.Clazz]):
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
    scope = (2 ** score) / 100 * average(series)
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
    avg = mid_series(series)
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


def take_position(series: List[tool.Clazz], score: int) -> Iterable[Tuple[tool.Clazz, tool.Clazz, tool.Clazz]]:
    avg = average(series)
    scope = (2 ** score) / 100 * avg
    queue = deque(series[:2])

    for s in series[2:]:
        y1, y2, y3 = queue[-2].y, queue[-1].y, s.y

        delta12 = y1 - y2
        delta23 = y2 - y3

        if delta12 > 0:
            if delta23 > 0:
                queue[-1] = s
                if len(queue) >= 3:
                    yield queue[-3], queue[-2], queue[-1]
            elif delta23 < -scope:
                queue.append(s)
                yield queue[-3], queue[-2], queue[-1]

        if delta12 < 0:
            if delta23 < 0:
                queue[-1] = s
                if len(queue) >= 3:
                    yield queue[-3], queue[-2], queue[-1]
            elif delta23 > scope:
                queue.append(s)
                yield queue[-3], queue[-2], queue[-1]


def show_take_position(begin: int, end: int):
    series = read_series(begin, end)
    mids = mid_series(series)
    plot_series([s.x for s in mids], [s.y for s in mids], 'ABC')

    score = 4
    reduced = reduce_series(mids, score)
    plot_series([s.x for s in reduced], [s.y for s in reduced], 'score', score)

    avg = average(mids)
    for s1, s2, s3 in take_position(mids, score):
        y1, y2, y3 = s1.y, s2.y, s3.y
        if abs(y1 - y3) / avg < 0.05:
            s3.position = True

    positions = [r for r in reduced if 'position' in r]
    plot_series([p.x for p in positions], [p.y for p in positions], 'position', 7)

    plt.legend(loc='upper left')
    plt.grid()
    plt.tight_layout()
    plt.show()


def execute():
    show_avg(1514851200, 1607644800)
    show_flatten(1514851200, 1607644800)
    show_take_position(1514851200, 1607644800)


if __name__ == '__main__':
    execute()
