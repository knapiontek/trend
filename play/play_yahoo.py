from pprint import pprint

import matplotlib.pyplot as plt
import pandas as pd
from pandas.plotting import register_matplotlib_converters

from src import config
import seaborn as sns
sns.set()

register_matplotlib_converters()

filename = config.STORE_FOLDER.joinpath('XOM.csv')

xom = pd.read_csv(filename, parse_dates=['Date'])

pprint(xom.dtypes)

xom = xom.sort_values(by='Date')

xom = xom.truncate(before='2020-01-01')

plt.plot(xom.Date, xom.Close, label='Price')

plt.legend(loc='upper left')
plt.grid()
plt.tight_layout()
man = plt.get_current_fig_manager()
man.window.showMaximized()
plt.show()
