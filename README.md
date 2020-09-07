
# TODO

- Create scheduler based on aiohttp

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
time ./run.py --show-symbol-range | jq '.[] | select(.symbol | contains("XOM"))'
```

```bash
conda env create -n trend-py37 -f requirements.yml
conda env update -n trend-py37 -f requirements.yml
conda activate trend-py37
```

```bash
sudo apt install apache-utils
echo $(htpasswd -nb <username> <password>) | sed -e s/\\$/\\$\\$/g
docker run -d -p 8080:8080 -p 80:80 \
-v $PWD/traefik.yml:/etc/traefik/traefik.yml \
-v /var/run/docker.sock:/var/run/docker.sock \
traefik:v2.0
```
