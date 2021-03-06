
# TODO

- Make strategies and present them

# Road Map

## Trading Engine

### Strategies for a few indices
1. Enter on higher low and sell 50% on first reversal, verify multi-frame
2. Choppiness Index + Price Action + Support/Resistance + Volume

## Engine Web Viewer (nodejs based)
 - Accept the proposed instrument
 - instrument proposal based on volume, PE, EBIDA etc (criteria can be fully automated)

# Trend

## Trading strategies

1. Histogram for Resistance/Support Areas
2. MAEE strategy: Market, Area, Entry, Exit
    - Area - support, resistance, EMA 50, 100, 200
    - Exit - with success, with failure
3. Dow strategy
    - Enter on higher low with good risk/reward ratio (the latest high and low)

### Price Action (bull market)

- Green candles are bigger
- More consecutive green bars, red bars alone
- Big low wicks in the candles (hammers)
- The end of the trend - pull-backs are getting stronger

### Short Squeeze - False Break Out

- Close with loss if build-up is observed

### 3 EMA technique (50,100,150 EMA)

- All 3 EMA's are parallel
- Enter trade when the price dip and reverse from 50 EMA
- Stop-loss at the lowest pull-back, enter trade when price cross back 50 EMA

### Some tickers

gdx, sil, silj
zkb gold
zkb silver
nom.cn
trade break-outs with build-up
RSP/SPX - the equally weighted index to S&P500
MMTH - how many stocks are above SMA-200

### Pullback in Up-Trend

- trend above 200 EMA
- entry RSI(10) < 30 (buy on the next day open)
- exit RSI(10) > 40 or 10 trading days (sell on the next day open)

### Follow Trend against Contra-Trend Players

- when in the down-trend
- strong green bar
- strong red bar
- quit, no price change makes contra-trend players to lose confidence
- time to sell

### Market Sentiment

- PUT/CALL ratio
- Sentiment Research
- Funds cash flow
- Position of commercials on the dollar index
- Truck Tonnage vs S&P500
- Fear & Greed Index
- Dollar Index (reverse correlation to the stock)
- Margin Debt
- Wskaźnik Koniunktury DNA Rynków

### Global Financial Indices

- Euro Stoxx 50	Strefa
- DAX	Niemcy
- FTSE 100	W.Brytania
- CAC 40	Francja
- IBEX 35	Hiszpania
- FTSE MIB	Włochy
- ASE	Grecja
- BUX	Węgry
- PX	Czechy
- RTS INDEX (w USD)	Rosja
- BIST 100	Turcja
- WIG 20	Polska
- WIG	Polska
- mWIG 40	Polska

# CLI

```bash
./manage.py --engine exante yahoo stooq --security update verify analyse --log-to-screen
cat ~/.ssh/config
Host lightsail
  HostName 54.216.1.84
    IdentityFile /home/kris/.ssh/lightsail
    User ubuntu
curl -u tik:<pass> -XPOST https://gecko-code.info/schedule/
curl -u admin -p -XPOST https://gecko-code.info/schedule/
time ./run.py --show-symbol-range | jq '.[] | select(.symbol | contains("XOM"))'
curl -s -u app_id:key https://api-demo.exante.eu/md/1.0/accounts
cat symbols1.json|jq -c '.[]|select(.ticker == "XOM" and .type == "STOCK")'|jq .
curl -k 'https://cloud.iexapis.com/stable/ref-data/exchanges?token=???'|jq .
./run.py --show-instrument-range|jq '."ZBRA.NASDAQ"'
```

```
            FOR series IN series_yahoo_1d
                COLLECT symbol = series.symbol
                AGGREGATE min_ts = MIN(series.timestamp), max_ts = MAX(series.timestamp)
                RETURN {symbol, min_ts, max_ts}

            FOR series IN series_yahoo_1d
                FILTER series.timestamp == 1600214400
                REMOVE series IN series_yahoo_1d
```
