from collections import deque
from enum import Enum
from typing import List, Iterable

import matplotlib.pyplot as plt
from matplotlib import ticker

from src import tool, exante
from src.clazz import Clazz
from src.tool import DateTime


def avg_val(series: List[Clazz]):
    return sum([s.y for s in series]) / len(series)


# plot

class Color(Enum):
    yellow = 'yellow'
    orange = 'orange'
    red = 'red'
    brown = 'brown'
    olive = 'olive'
    green = 'green'
    blue = 'blue'
    black = 'black'


def plot_series(series: List[Clazz]):
    plt.plot([s.x for s in series], [s.y for s in series], '-', label='series', color='grey', linewidth=1)


def plot_dots(series: List[Clazz], color: Color):
    plt.plot([s.x for s in series],
             [s.y for s in series],
             'o', label=f'dot-{color.name}', color=color.name, linewidth=1, markersize=3)


def plot_swings(series: List[Clazz], score: int):
    color = score_to_color(score)
    plt.plot([s.x for s in series],
             [s.y for s in series],
             'o', label=f'score-{score} ({2 ** (score - 1):02})', color=color.name, linewidth=1, markersize=1 + score)


def score_to_color(score: int) -> Color:
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
    return colors[score]


def show_widget(symbol: str, begin: int, end: int):
    def format_date(timestamp, step=0):
        if step is None:
            return DateTime.from_timestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        else:
            return DateTime.from_timestamp(timestamp).strftime('%Y-%m-%d')

    plt.title(f'Swings 2^(n-1) {symbol} [{format_date(begin)} - {format_date(end)}]')
    plt.legend(loc='upper left')
    plt.grid()
    plt.tight_layout()
    plt.gca().set_facecolor('silver')
    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(format_date))
    plt.show()


# data

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


# reduce

def reduce_init(series: List[Clazz]):
    for s in series:
        s.candidate = set()
        s.score = set()


def reduce_series(series: List[Clazz], score: int) -> List[Clazz]:
    assert 1 <= score <= 8
    swing_limit = (2 ** (score - 1)) / 100 * avg_val(series)
    queue = deque(series[:2])

    for s3 in series[2:]:
        s1, s2 = queue[-2], queue[-1]

        delta12 = s2.y - s1.y
        delta23 = s3.y - s2.y

        if delta12 > 0:
            if delta23 > 0:
                s3.candidate |= {score}
                queue[-1] = s3
            elif delta23 < -swing_limit:
                s2.score |= {score}
                s3.candidate |= {-score}
                queue.append(s3)

        if delta12 < 0:
            if delta23 < 0:
                s3.candidate |= {-score}
                queue[-1] = s3
            elif delta23 > swing_limit:
                s2.score |= {-score}
                s3.candidate |= {score}
                queue.append(s3)

    return list(queue)


def mark_swings(series: List[Clazz]):
    reduced = series
    reduce_init(reduced)
    for score in range(1, 8):
        reduced = reduce_series(reduced, score)


def swing_candidates(series: List[Clazz], values: Iterable[int]):
    return [s for s in series if any(v in s.candidate for v in values)]


def swing_scores(series: List[Clazz], values: Iterable[int]):
    return [s for s in series if any(v in s.score for v in values)]


# presentation


def show_candidates(symbol: str, begin: int, end: int):
    series = read_series(symbol, begin, end)
    plot_series(series)

    mark_swings(series)

    score = 3

    candidates = swing_candidates(series, (-score, score))
    plot_dots(candidates, Color.green)

    scores = swing_scores(series, (-score, score))
    plot_dots(scores, Color.red)

    show_widget(symbol, begin, end)


def show_swings(symbol: str, begin: int, end: int):
    series = read_series(symbol, begin, end)
    plot_series(series)

    mark_swings(series)

    for score in range(1, 8):
        scores = swing_scores(series, (-score, score))
        plot_swings(scores, score)

    show_widget(symbol, begin, end)


# main

def execute():
    symbol = 'ABC.NYSE'
    begin = DateTime(2017, 11, 1).to_timestamp()
    end = DateTime.now().to_timestamp()
    show_swings(symbol, begin, end)


if __name__ == '__main__':
    execute()
