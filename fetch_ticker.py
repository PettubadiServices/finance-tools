#!/usr/bin/env python3
import yfinance as yf
import json
import sys

if len(sys.argv) < 2:
    print("Usage: fetch_ticker.py TICKER")
    sys.exit(1)

ticker = sys.argv[1].upper()
t = yf.Ticker(ticker)
info = t.info

# Some dividend fields may be missing for non-dividend stocks
current_yield = info.get("dividendYield")
five_year_yield = info.get("fiveYearAvgDividendYield")

data = {
    "ticker": ticker,
    "price": info.get("currentPrice"),
    "market_cap": info.get("marketCap"),
    "forward_pe": info.get("forwardPE"),
    "trailing_pe": info.get("trailingPE"),
    "peg": info.get("pegRatio"),
    "revenue_growth": info.get("revenueGrowth"),
    "eps_growth": info.get("earningsQuarterlyGrowth"),
    "gross_margin": info.get("grossMargins"),
    "operating_margin": info.get("operatingMargins"),
    "net_margin": info.get("profitMargins"),
    "total_debt": info.get("totalDebt"),
    "cash": info.get("totalCash"),
    "ebitda": info.get("ebitda"),
    "free_cash_flow": info.get("freeCashflow"),
    "sector": info.get("sector"),
    "roe": info.get("returnOnEquity"),
    "beta": info.get("beta"),
    "short_interest": info.get("shortPercentOfFloat"),
    "earnings_date": info.get("earningsDate"),
    "fifty_day_avg": info.get("fiftyDayAverage"),
    "analyst_rating": info.get("recommendationKey"),
    "rsi": info.get("rsi"),
    "iv_current": info.get("impliedVolatility"),
    "iv_high_52w": info.get("impliedVolatility52WeekHigh"),
    "iv_low_52w": info.get("impliedVolatility52WeekLow"),
    "iv_current": info.get("impliedVolatility"),
    "put_call_ratio": info.get("putCallRatio"),



    # Dividend fields
    "dividend_yield": current_yield,
    "five_year_avg_dividend_yield": five_year_yield,
    "payout_ratio": info.get("payoutRatio"),

    # Technicals
    "52w_high": info.get("fiftyTwoWeekHigh"),
    "52w_low": info.get("fiftyTwoWeekLow"),
    "200dma": info.get("twoHundredDayAverage"),
}

# -----------------------------
# Price Targets
# -----------------------------
data["avg_pt"] = info.get("targetMeanPrice")
data["high_pt"] = info.get("targetHighPrice")
data["low_pt"] = info.get("targetLowPrice")

if data["avg_pt"] and data["price"]:
    data["pt_up"] = (data["avg_pt"] - data["price"]) / data["price"]
else:
    data["pt_up"] = None

# -----------------------------
# Valuation Signals
# -----------------------------
data["ev_ebitda"] = info.get("enterpriseToEbitda")

fcf = data.get("free_cash_flow")
mc = data.get("market_cap")
data["fcf_yield"] = (fcf / mc) if (fcf and mc) else None

# -----------------------------
# Growth Trends
# -----------------------------
data["rev_yoy"] = info.get("revenueGrowth")
data["eps_yoy"] = info.get("earningsGrowth")

# Yahoo does NOT provide 3Y CAGR — set to None
data["rev_cagr"] = None
data["eps_cagr"] = None


# ----
# Compute Implied Volatility
# ----
iv = info.get("impliedVolatility")
ivh = info.get("impliedVolatility52WeekHigh")
ivl = info.get("impliedVolatility52WeekLow")

if iv and ivh and ivl and (ivh - ivl) != 0:
    data["ivr"] = (iv - ivl) / (ivh - ivl)
else:
    data["ivr"] = None


# ---
# Compute Expected Move
# ---
# Expected Move (30-day default)
iv = info.get("impliedVolatility")
price = info.get("currentPrice")

if iv and price:
    dte = 30  # default 30 days
    data["expected_move"] = price * iv * ((dte / 365) ** 0.5)
else:
    data["expected_move"] = None



# -----------------------------
# Save JSON
# -----------------------------
with open(f"{ticker}.json", "w") as f:
    json.dump(data, f, indent=4)

print(f"Saved {ticker}.json")

