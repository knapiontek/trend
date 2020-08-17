
# Road Map

## Trading Engine

### Strategies for a few indices
1. Enter on higher low and sell 50% on first reversal, verify multi-frame
2. Choppiness Index + Price Action + Support/Resistance + Volume

### Run the engine on all instruments passing criteria (volume, short-allowance, etc)

## JSONStorage
 - based on MongoDB or ArangoDB

## Engine Web Viewer (nodejs based)
 - Accept the proposed intrument
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

curl -s -u app_id:key https://api-demo.exante.eu/md/1.0/accounts
cat symbols1.json|jq -c '.[]|select(.ticker == "XOM" and .type == "STOCK")'|jq .
https://rapidapi.com/apidojo/api/yahoo-finance1
