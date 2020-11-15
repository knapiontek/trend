from typing import List, Sized, Tuple, Optional

import matplotlib.pyplot as plt
from more_itertools import windowed

from src import tool, yahoo


def i_windowed(sized: Sized, size: int):
    return windowed(range(len(sized)), size)


def read_data(timestamp) -> List[tool.Clazz]:
    interval = tool.INTERVAL_1D
    with yahoo.SecuritySeries(interval) as security_series:
        abc_series = [s for s in security_series['ABC.NYSE'] if s.timestamp < timestamp]
    for s in abc_series:
        s.grade = 0.0
        s.timestamp /= 1e6
    return abc_series


def plot_series(series: List[tool.Clazz], grade: float, label: str, color: str, style='-'):
    series = [s for s in series if s.grade >= grade]
    timestamps = [s.timestamp for s in series]
    closes = [s.close for s in series]
    plt.plot(timestamps, closes, style, label=label, color=color, linewidth=1, markersize=2)


def reduce1(series: List[tool.Clazz], max_grade: int) -> Tuple[List[tool.Clazz], List[tool.Clazz]]:
    min_spikes: List[tool.Clazz] = []
    max_spikes: List[tool.Clazz] = []
    w_size = 3
    if len(series) >= w_size:
        closes = [s.close for s in series]
        min_val = min(closes)
        max_val = max(closes)
        grade = round((max_val - min_val) / max_grade)
        for i1, i2, i3 in i_windowed(series, w_size):
            c1, c2, c3 = [series[i].close for i in [i1, i2, i3]]
            if c2 == min(c1, c2, c3):
                min_spikes = [s for s in min_spikes if s.close < c2]
                min_spikes.append(series[i2])
                for s in max_spikes:
                    s.grade = max(s.grade, abs(s.close - c2))
            if c2 == max(c1, c2, c3):
                max_spikes = [s for s in max_spikes if s.close > c2]
                max_spikes.append(series[i2])
                for s in min_spikes:
                    s.grade = max(s.grade, abs(s.close - c2))
        return min_spikes, max_spikes
    return [], []


def show1(timestamp):
    abc_series = read_data(timestamp)
    plot_series(abc_series, 0.0, 'ABC', 'grey')

    min_spikes, max_spikes = reduce1(abc_series, 10)
    plot_series(min_spikes, 0.0, 'min', 'green', 'o')
    plot_series(max_spikes, 0.0, 'max', 'red', 'o')
    plot_series(min_spikes, 20.0, 'min20', 'orange', 'o')
    plot_series(max_spikes, 20.0, 'max20', 'blue', 'o')

    plt.legend(loc='upper left')
    plt.grid()
    plt.tight_layout()
    plt.show()


def test1():
    for ts in [1524750000, 1546000000, 1700000000]:
        show1(ts)


def clean(series: List[tool.Clazz]) -> List[tool.Clazz]:
    reduced: List[Optional[tool.Clazz]] = series[:]
    for i1, i2, i3 in i_windowed(series, 3):
        close1, close2, close3 = [series[i].close for i in [i1, i2, i3]]
        if close1 <= close2 <= close3:
            reduced[i2] = None
            if close1 == close3:
                reduced[i1] = None
        elif close1 >= close2 >= close3:
            reduced[i2] = None
            if close1 == close3:
                reduced[i1] = None
    return list(filter(None, reduced))


def reduce2(series: List[tool.Clazz], grade: int) -> List[tool.Clazz]:
    queue: List[tool.Clazz] = []
    for s in series:
        if s.timestamp > 1516.9:
            print(s.timestamp)
        if len(queue) >= 2:
            close1, close2 = [queue[i].close for i in [-2, -1]]
            close3 = s.close
            delta = close1 - close3
            delta1 = close1 - close2
            delta2 = close2 - close3
            if delta1 > 0:
                if delta2 > 0:
                    if delta > delta1:
                        queue[-1] = s
                elif delta2 < -grade:
                    queue.append(s)
            if delta1 < 0:
                if delta2 < 0:
                    if delta < delta1:
                        queue[-1] = s
                elif delta2 > grade:
                    queue.append(s)
        else:
            queue.append(s)
    return queue


def show2(timestamp):
    abc_series = clean(read_data(timestamp))
    plot_series(abc_series, 0.0, 'ABC', 'grey')

    reduced = reduce2(abc_series, 2)
    plot_series(reduced, 0.0, 'reduced', 'blue', 'o')

    plt.legend(loc='upper left')
    plt.grid()
    plt.tight_layout()
    plt.show()


def test2():
    show2(1524750000)


if __name__ == '__main__':
    test2()
