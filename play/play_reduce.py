from datetime import timedelta
from enum import Enum
from typing import List

import matplotlib.pyplot as plt
from matplotlib import ticker

from src import tool, exante, swings
from src.clazz import Clazz
from src.tool import DateTime


# data

def read_series(symbol: str, interval: timedelta, begin: int, end: int) -> List[Clazz]:
    with exante.SecuritySeries(interval) as security_series:
        return [s for s in security_series[symbol] if begin <= s.timestamp <= end]


# plot

class Color(Enum):
    grey = 'grey'
    yellow = 'yellow'
    orange = 'orange'
    red = 'red'
    brown = 'brown'
    olive = 'olive'
    green = 'green'
    blue = 'blue'
    black = 'black'

    @staticmethod
    def from_score(score: int) -> 'Color':
        assert 1 <= score <= 8
        colors = [Color.yellow,
                  Color.orange,
                  Color.red,
                  Color.brown,
                  Color.olive,
                  Color.green,
                  Color.blue,
                  Color.black]
        return colors[score - 1]


def plot_line(xs: List[float], ys: List[float], label: str, color: Color):
    plt.plot(xs, ys, '-', label=label, color=color.value, linewidth=1)


def plot_dots(xs: List[float], ys: List[float], label: str, color: Color, size: int):
    plt.plot(xs, ys, 'o', label=label, color=color.value, linewidth=1, markersize=size)


def plot_bars(series: List[Clazz]):
    results = []
    for s in series:
        value1, value2 = (s.low, s.high) if s.close > s.open else (s.high, s.low)
        results += [Clazz(timestamp=s.timestamp, value=s.open),
                    Clazz(timestamp=s.timestamp, value=value1),
                    Clazz(timestamp=s.timestamp, value=value2),
                    Clazz(timestamp=s.timestamp, value=s.close)]
    plot_line([s.timestamp for s in results], [s.value for s in results], label='bars', color=Color.grey)


def plot_valid_swings(series: List[Clazz], score: int):
    results = []
    for s in series:
        if score <= s.valid_low_score:
            results += [Clazz(timestamp=s.timestamp, value=s.low)]
        if score <= s.valid_high_score:
            results += [Clazz(timestamp=s.timestamp, value=s.high)]
    color = Color.from_score(score)
    plot_dots([s.timestamp for s in results], [s.value for s in results],
              label=f'score-{score} [{int(100 * swings.limit_ratio(score)):03}%]',
              color=color, size=1 + score)


def plot_candidate_swings(series: List[Clazz], score: int):
    results = []
    for s in series:
        if score <= s.low_score:
            results += [Clazz(timestamp=s.timestamp, value=s.low)]
        if score <= s.high_score:
            results += [Clazz(timestamp=s.timestamp, value=s.high)]
    color = Color.from_score(score)
    plot_dots([s.timestamp for s in results], [s.value for s in results],
              label=f'score-{score} [{int(100 * swings.limit_ratio(score)):03}%]',
              color=color, size=1 + score)


def plot_strategy(series: List[Clazz]):
    plot_dots([s.timestamp for s in series], [s.test.long for s in series], label='Long', color=Color.green, size=2)
    plot_dots([s.timestamp for s in series], [s.test.short for s in series], label='Short', color=Color.red, size=2)


def show_widget(symbol: str, begin: int, end: int):
    def format_date(timestamp, step=0):
        if step is None:
            return DateTime.from_timestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        else:
            return DateTime.from_timestamp(timestamp).strftime('%Y-%m-%d')

    plt.title(f'{symbol} [{format_date(begin)} - {format_date(end)}]')
    plt.legend(loc='upper left')
    plt.grid()
    plt.tight_layout()
    plt.gca().set_facecolor('silver')
    plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(format_date))
    plt.show()


# show


def show_swings(symbol: str, interval: timedelta, begin: int, end: int):
    series = read_series(symbol, interval, begin, end)
    plot_bars(series)

    swings.calculate(series)

    for score in range(1, 9):
        plot_valid_swings(series, score)

    show_widget(symbol, begin, end)


def show_candidates(symbol: str, interval: timedelta, begin: int, end: int):
    series = read_series(symbol, interval, begin, end)
    plot_bars(series)

    reduced = swings.init(series)
    for score in (1, 3):
        reduced = swings.reduce(reduced, score)
        plot_candidate_swings(series, score)

    show_widget(symbol, begin, end)


class State(Enum):
    LOW_SCORE = 1
    LOW_SCORE1 = 2


def show_strategy(symbol: str, interval: timedelta, begin: int, end: int):
    series = read_series(symbol, interval, begin, end)
    plot_bars(series)

    state = State.LOW_SCORE
    reduced = swings.init(series)
    swings.reduce(reduced, 4)
    for s in series:
        s.test = Clazz(long=0.0, short=0.0)
        if 4 <= s.low_score:
            if state == State.LOW_SCORE:
                state = State.LOW_SCORE1
                s.state = state

    plot_strategy(series)

    show_widget(symbol, begin, end)


# main

def execute():
    symbol = 'ABC.NYSE'
    interval = tool.INTERVAL_1D
    begin = DateTime(2018, 11, 18).to_timestamp()
    end = DateTime(2019, 11, 18).to_timestamp()
    show_candidates(symbol, interval, begin, end)


if __name__ == '__main__':
    execute()
