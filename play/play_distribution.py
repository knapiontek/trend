from pprint import pprint

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pandas.plotting import register_matplotlib_converters

from src import config

sns.set(color_codes=True)

register_matplotlib_converters()

filename = config.STORE_FOLDER.joinpath('XOM.csv')

xom = pd.read_csv(filename, parse_dates=['Date'])

pprint(xom.dtypes)

xom = xom.sort_values(by='Date')

plt.subplot(2, 2, 1)
plt.plot(xom.Date, xom.Close, label='Price')
plt.legend(loc='upper left')

plt.subplot(2, 2, 3)
plt.plot(xom.Date, xom.Volume, label='Volume')
plt.legend(loc='upper left')


def distribution(df: pd.DataFrame):
    _min = int(df.Close.min())
    _max = int(df.Close.max())
    x = range(_min, _max)
    y = [0] * (_max - _min)
    for i in df.index:
        close = int(df.Close.iloc[i])
        volume = df.Volume.iloc[i]
        y[close - _min - 1] += volume
    return x, y


plt.subplot(2, 2, 2)
x, y = distribution(xom)
plt.bar(x, y, label='Distribution')
plt.legend(loc='upper left')

plt.grid(True)
plt.tight_layout()
man = plt.get_current_fig_manager()
man.window.showMaximized()
plt.show()
