from typing import List

import matplotlib.pyplot as plt

from src import tool, yahoo


def reduce_on_fly(series: List[float]) -> List[float]:
    if series:
        min_value = [0]
        max_value = [0]
        for i, s in enumerate(series, 1):
            if s < min_value[-1]:
                min_value.append(s)
            if s > max_value[-1]:
                max_value.append(s)
    return series


def show():
    interval = tool.INTERVAL_1D
    with yahoo.SecuritySeries(interval) as security_series:
        abc_series = security_series['ABC.NYSE']
    abc = [s.close for s in abc_series]

    plt.plot(abc, label='ABC', color='blue', linewidth=1)

    plt.legend(loc='upper left')
    plt.grid()
    plt.tight_layout()
    # man = plt.get_current_fig_manager()
    # man.window.showMaximized()
    plt.show()


if __name__ == '__main__':
    show()
