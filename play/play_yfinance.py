from pprint import pprint

import matplotlib.pyplot as plt
import yfinance as yf

msft = yf.Ticker("MSFT")

# get stock info
print(msft.info)

# get historical market data
hist = msft.history(period="1000d")
pprint(hist)

hist['Close'].plot(figsize=(16, 9))
plt.show()
