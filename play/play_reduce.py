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
    results = []
    for s in series:
        value1, value2 = (s.low, s.high) if s.close > s.open else (s.high, s.low)
        results += [Clazz(timestamp=s.timestamp, value=s.open),
                    Clazz(timestamp=s.timestamp, value=value1),
                    Clazz(timestamp=s.timestamp, value=value2),
                    Clazz(timestamp=s.timestamp, value=s.close)]
    plt.plot([s.timestamp for s in results],
             [s.value for s in results],
             '-', label='series', color='grey', linewidth=1)


def plot_swings(series: List[Clazz], score: int):
    results = []
    for s in series:
        if score <= s.valid_low_score:
            results += [Clazz(timestamp=s.timestamp, value=s.low)]
        if score <= s.valid_high_score:
            results += [Clazz(timestamp=s.timestamp, value=s.high)]
    color = Color.from_score(score)
    plt.plot([s.timestamp for s in results],
             [s.value for s in results],
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


# show


def show_swings(symbol: str, interval: timedelta, begin: int, end: int):
    series = read_series(symbol, interval, begin, end)
    plot_series(series)

    swings.calculate(series)

    for score in range(1, 8):
        plot_swings(series, score)

    show_widget(symbol, begin, end)


# main

def execute():
    symbol = 'ABC.NYSE'
    interval = tool.INTERVAL_1D
    begin = DateTime(2017, 11, 1).to_timestamp()
    end = DateTime.now().to_timestamp()
    show_swings(symbol, interval, begin, end)


if __name__ == '__main__':
    execute()
