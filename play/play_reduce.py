from typing import List, Sized, Tuple

import matplotlib.pyplot as plt
from more_itertools import windowed

from src import tool, yahoo


def i_windowed(sized: Sized, size: int):
    return windowed(range(len(sized)), size)


def reduce(series: List[tool.Clazz], max_grade: int) -> Tuple[List[tool.Clazz], List[tool.Clazz]]:
    min_spikes: List[tool.Clazz] = []
    max_spikes: List[tool.Clazz] = []
    w_size = 3
    if len(series) >= w_size:
        closes = [s.close for s in series]
        min_val = min(closes)
        max_val = max(closes)
        grade = round((max_val - min_val) / max_grade, 0)
        for i1, i2, i3 in i_windowed(series, w_size):
            c1 = series[i1].close
            c2 = series[i2].close
            c3 = series[i3].close
            if c2 == min(c1, c2, c3):
                min_spikes = [s for s in min_spikes if s.close > c2]
                min_spikes.append(series[i2])
            if c2 == max(c1, c2, c3):
                max_spikes = [s for s in max_spikes if s.close < c2]
                max_spikes.append(series[i2])
        return min_spikes, max_spikes
    return [], []


def plot_series(series: List[tool.Clazz], label: str, color: str):
    timestamps = [s.timestamp for s in series]
    closes = [s.close for s in series]
    plt.plot(timestamps, closes, label=label, color=color, linewidth=1)


def show():
    interval = tool.INTERVAL_1D
    with yahoo.SecuritySeries(interval) as security_series:
        abc_series = security_series['ABC.NYSE']

    plot_series(abc_series, 'ABC', 'blue')

    min_spikes, max_spikes = reduce(abc_series, 8)
    plot_series(min_spikes, 'min', 'green')
    plot_series(max_spikes, 'max', 'red')

    plt.legend(loc='upper left')
    plt.grid()
    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    show()
