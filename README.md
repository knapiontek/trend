
# Road Map

## Trading Engine

### Strategies for a few indices
1. Enter on higher low and sell 50% on first reversal, verify multi-frame
2. Choppiness Index + Price Action + Support/Resistance + Volume

### Run the engine on all instruments passing criteria (volume, short-allowance, etc)

## JSONStorage
 - based on arango-db

## Engine Web Viewer (nodejs based)
 - Accept the proposed instrument
 - instrument proposal based on volume, PE, EBIDA etc (criteria can be fully automated)

## Deployment
 - Traefik
 - Register Domain
 - Deploy Trading Engine
 - Deploy Web Viewer

# Trend

## Trading strategies

1. Histogram for Resistance/Support Areas
2. MAEE strategy: Market, Area, Entry, Exit
    - Area - support, resistance, EMA 50, 100, 200
    - Exit - with success, with failure
3. Dow strategy
    - Enter on higher low with good risk/reward ratio (latest high and low)

## Notes

```bash
curl -s -u app_id:key https://api-demo.exante.eu/md/1.0/accounts
cat symbols1.json|jq -c '.[]|select(.ticker == "XOM" and .type == "STOCK")'|jq .
https://rapidapi.com/apidojo/api/yahoo-finance1

https://towardsdatascience.com/best-5-free-stock-market-apis-in-2019-ad91dddec984
curl -k 'https://cloud.iexapis.com/stable/ref-data/exchanges?token=???'|jq .
```

### Price Action (bull market)

- Green candles are bigger
- More consecutive green bars, red bars alone
- Big low wicks in the candles (hammers)

### Short Squeeze - False Break Out

- Close with loss if build-up is observed

### 3 EMA technique (50,100,150 EMA)

- All 3 EMA's are parrallel
- Enter trade when price dip and reverse from 50 EMA
- Stop-loss at the lowest pull-back, enter trade when price cross back 50 EMA

gdx, sil, silj
zkb gold
zkb silver
trade break-outs with build-up

```bash
time python src/run.py --entry show-symbol-range | jq '.[] | select(.symbol | contains("XOM"))'
```

```bash
conda env create -n trend-py37 -f requirements.yml
conda env update -n trend-py37 -f requirements.yml
conda activate trend-py37
```

### TODO

- Parameterize code with data providers (yahoo, exante)
- Fix Progress class issues with flush and complete
- tuple_it() or a new function should work with single key
- interval_to_yahoo and interval_name can be unified

