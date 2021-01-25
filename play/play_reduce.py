from collections import deque
from enum import Enum
from typing import List

import matplotlib.pyplot as plt
from matplotlib import ticker

from src import tool, exante
from src.clazz import Clazz
from src.tool import DateTime


def avg_val(series: List[Clazz]):
    return sum([s.y for s in series]) / len(series)


def plot_series(series: List[Clazz]):
    plt.plot([s.x for s in series], [s.y for s in series], '-', label='series', color='grey', linewidth=1)


class Color(Enum):
    yellow = 'yellow'
    orange = 'orange'
    red = 'red'
    brown = 'brown'
    olive = 'olive'
    green = 'green'
    blue = 'blue'
    black = 'black'


def plot_dots(series: List[Clazz], color: Color):
    plt.plot([s.x for s in series],
             [s.y for s in series],
             'o', label=f'dot-{color.name}', color=color.name, linewidth=1, markersize=3)


def plot_swings(series: List[Clazz], score: int):
    assert 1 <= score <= 8
    colors = [None,
              Color.yellow,
              Color.orange,
              Color.red,
              Color.brown,
              Color.olive,
              Color.green,
              Color.blue,
              Color.black]
    color = colors[score]
    plt.plot([s.x for s in series],
             [s.y for s in series],
             'o', label=f'score-{score} ({2 ** (score - 1):02})', color=color.name, linewidth=1, markersize=1 + score)


def show_widget(symbol: str, begin: int, end: int):
    def format_date(timestamp, step=None):
        return DateTime.from_timestamp(timestamp).strftime('%Y-%m-%d')

    plt.title(f'Swings 2^(n-1) {symbol} [{format_date(begin)} - {format_date(end)}]')
    plt.legend(loc='upper left')
    plt.grid()
    plt.tight_layout()
    plt.gca().set_facecolor('silver')
    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(format_date))
    plt.show()


def read_series(symbol: str, begin: int, end: int) -> List[Clazz]:
    interval = tool.INTERVAL_1D
    series = []
    with exante.SecuritySeries(interval) as security_series:
        for s in security_series[symbol]:
            if begin <= s.timestamp <= end:
                x = s.timestamp
                y1, y2 = (s.low, s.high) if s.close > s.open else (s.high, s.low)
                series += [Clazz(x=x, y=s.open), Clazz(x=x, y=y1), Clazz(x=x, y=y2), Clazz(x=x, y=s.close)]
    return series


def reduce_init(series: List[Clazz]):
    for s in series:
        s.propose = set()
        s.confirm = set()


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
                s.propose |= {-score}
                queue[-1] = s
            elif delta23 < -scope:
                queue[-1].confirm |= {-score}
                s.propose |= {-score}
                queue.append(s)

        if delta12 < 0:
            if delta23 < 0:
                s.propose |= {score}
                queue[-1] = s
            elif delta23 > scope:
                queue[-1].confirm |= {score}
                s.propose |= {score}
                queue.append(s)

    return list(queue)


def show_swings(symbol: str, begin: int, end: int):
    series = read_series(symbol, begin, end)
    plot_series(series)

    reduced = series
    reduce_init(reduced)
    for score in range(1, 8):
        reduced = reduce_series(reduced, score)
        if len(reduced) > 2:
            plot_swings(reduced, score)

    show_widget(symbol, begin, end)


def show_deals(symbol: str, begin: int, end: int):
    series = read_series(symbol, begin, end)
    plot_series(series)

    reduced = series
    reduce_init(reduced)
    for score in range(1, 8):
        reduced = reduce_series(reduced, score)

    score = 3

    swings = [s for s in series if any(v in s.propose for v in (-score, score))]
    plot_dots(swings, Color.green)

    swings = [s for s in series if any(v in s.confirm for v in (-score, score))]
    plot_dots(swings, Color.red)

    show_widget(symbol, begin, end)


def execute():
    symbol = 'ABC.NYSE'
    begin = DateTime(2017, 11, 1).to_timestamp()
    end = DateTime.now().to_timestamp()
    show_deals(symbol, begin, end)
    show_swings(symbol, begin, end)


if __name__ == '__main__':
    rule = (-5, -2, -1)
    print(rule)
    execute()
