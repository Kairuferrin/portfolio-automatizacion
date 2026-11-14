# Project 2 · Requesting data from an API and reading the JSON

## The problem
The clothing brand from [project 1](../01-mapa-proceso/) also sells outside the eurozone. For the monthly report it needs to convert sales paid in dollars (USD) or pounds (GBP) into euros. Doing it by hand means looking up the exchange rate every time.

## The solution
Request the exchange rate from a free public **API**, [Frankfurter](https://frankfurter.dev). It publishes the European Central Bank's reference rates and needs no sign-up or key.

- **API:** the service window through which one program asks another for data.
- **Endpoint:** the specific address of that window (a URL).
- **JSON:** the format the answer comes back in. It is made of `"name": value` pairs, like a form with boxes.

## How to use it

### 1. Today's exchange rate
```bash
curl "https://api.frankfurter.dev/v1/latest?base=EUR&symbols=USD,GBP"
```
Real response (12 November 2026):
```json
{"amount":1.0,"base":"EUR","date":"2026-11-12","rates":{"GBP":0.83595,"USD":1.1081}}
```
How to read it: €1 = $1.1081 and €1 = £0.83595.

### 2. Exchange rates for a whole month (for the monthly report)
```bash
curl "https://api.frankfurter.dev/v1/2026-10-01..2026-10-31?base=EUR&symbols=USD"
```
It returns one rate for each business day. For example, on 1 October 2026 it was `"USD":1.1298`.

## What I learned
- The URL carries **parameters** after the `?`: `base=EUR` (the starting currency) and `symbols=USD,GBP` (the currencies I want).
- The JSON has **boxes inside boxes**: `rates` contains `USD` and `GBP`.
- In project 1, the step "collect data from Shopify" will work the same way: a URL, some parameters and a JSON response. The difference is that Shopify asks for a key, because its data is private.
