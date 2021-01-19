from collections import deque
from typing import List, Iterable, Tuple

import matplotlib.pyplot as plt

from src import tool, yahoo
from src.clazz import Clazz


def read_series(begin: int, end: int) -> List[Clazz]:
    interval = tool.INTERVAL_1D
    with yahoo.SecuritySeries(interval) as security_series:
        abc_series = security_series['ABC.NYSE']
        return [Clazz(x=s.timestamp / 1e6, y1=s.low, y2=s.high)
                for s in abc_series if begin <= s.timestamp <= end]


def average(series: List[Clazz]):
    return sum([s.y for s in series]) / len(series)


def mid_series(series: Iterable[Clazz]):
    return [Clazz(x=s.x, y=(s.y1 + s.y2) / 2) for s in series]


def flatten_series(series: Iterable[Clazz]):
    series = [[Clazz(x=s.x, y=s.y1), Clazz(x=s.x, y=s.y2)] for s in series]
    return sum(series, [])


def plot_series(xs: List[float], ys: List[float], label: str, score: int = 0):
    colors = ['grey', 'olive', 'green', 'blue', 'orange', 'red', 'brown', 'black']
    color = colors[score]
    style = 'o' if score else '-'
    plt.plot(xs, ys, style, label=f'{label}-{score}', color=color, linewidth=1, markersize=1 + score)


def reduce_series(series: List[Clazz], score: int) -> List[Clazz]:
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


def detect_swing(series: List[Clazz], score: int) -> Iterable[Tuple[Clazz, Clazz, Clazz]]:
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

    avg = average(mids)
    for s11, s12, s13 in detect_swing(mids, score=4):
        y11, y12, y13 = s11.y, s12.y, s13.y
        if abs(y11 - y13) / avg < 0.01 and y12 > y11 and y12 > y13:
            s13.position = 'open'
            i = mids.index(s13)
            for s21, s22, s23 in detect_swing(mids[i:], score=2):
                s23.position = 'close'
                break

    opens = [r for r in mids if r.get('position') == 'open']
    plot_series([o.x for o in opens], [p.y for p in opens], 'open', 4)

    closes = [r for r in mids if r.get('position') == 'close']
    plot_series([c.x for c in closes], [p.y for p in closes], 'close', 1)

    plt.legend(loc='upper left')
    plt.grid()
    plt.tight_layout()
    plt.show()


def sma1(series: List[Clazz], w_size: int):
    sma_name = f'sma-{w_size}'
    sum_val = 0.0
    for i, s in enumerate(series):
        sum_val += s.close
        if i >= w_size - 1:
            if i >= w_size:
                sum_val -= series[i - w_size].close
            s[sma_name] = sum_val / w_size


def execute():
    show_take_position(1514851200, 1607644800)


if __name__ == '__main__':
    execute()
