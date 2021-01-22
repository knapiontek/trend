from collections import deque
from typing import List

import matplotlib.pyplot as plt
from matplotlib import ticker

from src import tool, yahoo
from src.clazz import Clazz
from src.tool import DateTime


def avg_val(series: List[Clazz]):
    return sum([s.y for s in series]) / len(series)


def plot_series(series: List[Clazz]):
    plt.plot([s.x for s in series], [s.y for s in series], '-', label='series', color='grey', linewidth=1)


def plot_swings(series: List[Clazz], score: int):
    assert 1 <= score <= 8
    colors = [None, 'yellow', 'orange', 'red', 'brown', 'olive', 'green', 'blue', 'black']
    color = colors[score]
    plt.plot([s.x for s in series],
             [s.y for s in series],
             'o', label=f'score-{score}', color=color, linewidth=1, markersize=1 + score)


def show_widget():
    def format_date(timestamp, step):
        return DateTime.from_timestamp(timestamp).strftime('%Y-%m-%d')

    plt.title('Swings')
    plt.legend(loc='upper left')
    plt.grid()
    plt.tight_layout()
    plt.gca().set_facecolor('silver')
    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(format_date))
    plt.show()


def read_series(symbol: str, begin: int, end: int) -> List[Clazz]:
    interval = tool.INTERVAL_1D
    series = []
    with yahoo.SecuritySeries(interval) as security_series:
        for s in security_series[symbol]:
            if begin <= s.timestamp <= end:
                x = s.timestamp
                y1, y2 = (s.low, s.high) if s.close > s.open else (s.high, s.low)
                series += [Clazz(x=x, y=s.open), Clazz(x=x, y=y1), Clazz(x=x, y=y2), Clazz(x=x, y=s.close)]
    return series


def reduce_series(series: List[Clazz], score: int) -> List[Clazz]:
    assert 1 <= score <= 8
    scope = (2 ** (score - 1)) / 100 * avg_val(series)
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


def show_swings(symbol: str, begin: int, end: int):
    series = read_series(symbol, begin, end)
    plot_series(series)

    reduced = series
    for score in range(1, 8):
        reduced = reduce_series(reduced, score)
        if len(reduced) > 2:
            plot_swings(reduced, score)

    show_widget()


def show_deals(symbol: str, begin: int, end: int):
    series = read_series(symbol, begin, end)
    plot_series(series)

    reduced = series
    for score in range(1, 8):
        reduced = reduce_series(reduced, score)

    score = 3
    swings = [s for s in series if s.get('score', 0) >= score]
    plot_swings(swings, score)

    show_widget()


def execute():
    symbol = 'ABC.NYSE'
    begin = DateTime(2017, 11, 1).to_timestamp()
    end = DateTime.now().to_timestamp()
    show_swings(symbol, begin, end)


if __name__ == '__main__':
    rule = (-5, -2, -1)
    print(rule)
    execute()
