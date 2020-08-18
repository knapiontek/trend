import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src import config

sns.set(color_codes=True)

filename = config.STORE_PATH.joinpath('XOM.csv')

xom = pd.read_csv(filename, parse_dates=['Date'])
xom = xom.sort_values(by='Date')
sns.distplot(xom.Close)

plt.show()
