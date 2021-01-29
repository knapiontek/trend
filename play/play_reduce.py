from enum import Enum
from typing import List

import matplotlib.pyplot as plt
from matplotlib import ticker

from src import tool, exante, swings
from src.clazz import Clazz
from src.tool import DateTime


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


def plot_series(series: List[Clazz]):
    plt.plot([s.timestamp for s in series],
             [s.value for s in series],
             '-', label='series', color='grey', linewidth=1)


def plot_dots(series: List[Clazz], color: Color):
    plt.plot([s.timestamp for s in series],
             [s.value for s in series],
             'o', label=f'dot-{color.name}', color=color.name, linewidth=1, markersize=3)


def plot_swings(series: List[Clazz], score: int):
    color = score_to_color(score)
    plt.plot([s.timestamp for s in series],
             [s.value for s in series],
             'o', label=f'score-{score} [{2 ** (score - 1):02}%]', color=color.name, linewidth=1, markersize=1 + score)


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
                value1, value2 = (s.low, s.high) if s.close > s.open else (s.high, s.low)
                series += [Clazz(timestamp=s.timestamp, value=s.open),
                           Clazz(timestamp=s.timestamp, value=value1),
                           Clazz(timestamp=s.timestamp, value=value2),
                           Clazz(timestamp=s.timestamp, value=s.close)]
    return series


# presentation


def show_scores(symbol: str, begin: int, end: int):
    series = read_series(symbol, begin, end)
    plot_series(series)

    swings.calculate(series)

    score = 3

    scores = swings.scores(series, (-score, score))
    plot_dots(scores, Color.green)

    fixes = swings.fixes(series, (-score, score))
    plot_dots(fixes, Color.red)

    show_widget(symbol, begin, end)


def show_swings(symbol: str, begin: int, end: int):
    series = read_series(symbol, begin, end)
    plot_series(series)

    swings.calculate(series)

    for score in range(1, 8):
        fixes = swings.fixes(series, (-score, score))
        plot_swings(fixes, score)

    show_widget(symbol, begin, end)


# main

def execute():
    symbol = 'ABC.NYSE'
    begin = DateTime(2017, 11, 1).to_timestamp()
    end = DateTime.now().to_timestamp()
    show_scores(symbol, begin, end)


if __name__ == '__main__':
    execute()
