import yfinance as yf
import matplotlib.pyplot as plt
import seaborn

msft = yf.Ticker("MSFT")

# get stock info
print(msft.info)

# get historical market data
hist = msft.history(period="100d")

hist['Close'].plot(figsize=(16, 9))
plt.show()
