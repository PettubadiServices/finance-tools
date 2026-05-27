#!/usr/bin/env python3
import yfinance as yf
import json
import sys
import requests
from bs4 import BeautifulSoup

# -----------------------------
# Finviz Scraper
# -----------------------------
def fetch_finviz_data(ticker):
    url = f"https://finviz.com/quote.ashx?t={ticker}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception:
        return {}

    soup = BeautifulSoup(response.text, "html.parser")
    finviz = {}

    # Finviz fundamentals table
    for row in soup.find_all("tr", class_="table-dark-row"):
        cells = row.find_all("td")
        for i in range(0, len(cells), 2):
            key = cells[i].text.strip()
            val = cells[i+1].text.strip()
            finviz[key] = val

    return finviz


# -----------------------------
# Helpers
# -----------------------------
def safe_float(x):
    if not x:
        return None
    try:
        return float(x.replace('%','').replace(',','').replace('$',''))
    except:
        return None


# -----------------------------
# Main Program
# -----------------------------
if len(sys.argv) < 2:
    print("Usage: fetch_ticker.py TICKER")
    sys.exit(1)

ticker = sys.argv[1].upper()
t = yf.Ticker(ticker)
info = t.info


# -----------------------------
# YFINANCE DATA
# -----------------------------
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
    "two_hundred_day_avg": info.get("twoHundredDayAverage"),
    "analyst_rating": info.get("recommendationKey"),
    "rsi": info.get("rsi"),
    "iv_current": info.get("impliedVolatility"),
    "iv_high_52w": info.get("impliedVolatility52WeekHigh"),
    "iv_low_52w": info.get("impliedVolatility52WeekLow"),
    "put_call_ratio": info.get("putCallRatio"),
}


# -----------------------------
# FINVIZ DATA
# -----------------------------
finviz_raw = fetch_finviz_data(ticker)

# Map Finviz fields into JSON
data["finviz_pe"] = safe_float(finviz_raw.get("P/E"))
data["finviz_forward_pe"] = safe_float(finviz_raw.get("Forward P/E"))
data["finviz_peg"] = safe_float(finviz_raw.get("PEG"))
data["finviz_eps_next_5y"] = safe_float(finviz_raw.get("EPS next 5Y"))
data["finviz_eps_next_y"] = safe_float(finviz_raw.get("EPS next Y"))
data["finviz_roa"] = safe_float(finviz_raw.get("ROA"))
data["finviz_roe"] = safe_float(finviz_raw.get("ROE"))
data["finviz_roi"] = safe_float(finviz_raw.get("ROI"))
data["finviz_target_price"] = safe_float(finviz_raw.get("Target Price"))
data["finviz_recom"] = finviz_raw.get("Recom")
data["finviz_sma20"] = safe_float(finviz_raw.get("SMA20"))
data["finviz_sma50"] = safe_float(finviz_raw.get("SMA50"))
data["finviz_sma200"] = safe_float(finviz_raw.get("SMA200"))
data["finviz_rsi"] = safe_float(finviz_raw.get("RSI"))
data["finviz_short_float"] = safe_float(finviz_raw.get("Short Float"))
data["finviz_short_ratio"] = safe_float(finviz_raw.get("Short Ratio"))


# -----------------------------
# Growth Trends (YF)
# -----------------------------
data["rev_yoy"] = info.get("revenueGrowth")
data["eps_yoy"] = info.get("earningsGrowth")

data["rev_cagr"] = None
data["eps_cagr"] = None


# -----------------------------
# Implied Volatility Rank
# -----------------------------
iv = info.get("impliedVolatility")
ivh = info.get("impliedVolatility52WeekHigh")
ivl = info.get("impliedVolatility52WeekLow")

if iv and ivh and ivl and (ivh - ivl) != 0:
    data["ivr"] = (iv - ivl) / (ivh - ivl)
else:
    data["ivr"] = None


# -----------------------------
# Expected Move (30 days)
# -----------------------------
iv = info.get("impliedVolatility")
price = info.get("currentPrice")

if iv and price:
    dte = 30
    data["expected_move"] = price * iv * ((dte / 365) ** 0.5)
else:
    data["expected_move"] = None

# -----------------------------
# MERGE LOGIC — Unified Fields (FINAL)
# -----------------------------

# --- P/E ---
data["pe_ratio_merged"] = (
    data.get("finviz_pe")
    if data.get("finviz_pe") is not None
    else data.get("trailing_pe")
)

data["forward_pe_merged"] = (
    data.get("finviz_forward_pe")
    if data.get("finviz_forward_pe") is not None
    else data.get("forward_pe")
)

# --- PEG ---
data["peg_merged"] = (
    data.get("finviz_peg")
    if data.get("finviz_peg") is not None
    else data.get("peg")
)

# --- EPS Growth ---
data["eps_next_5y_merged"] = (
    data.get("finviz_eps_next_5y")
    if data.get("finviz_eps_next_5y") is not None
    else None
)

data["eps_next_y_merged"] = (
    data.get("finviz_eps_next_y")
    if data.get("finviz_eps_next_y") is not None
    else None
)

# --- ROE ---
data["roe_merged"] = (
    (data.get("finviz_roe") / 100)
    if data.get("finviz_roe") is not None
    else data.get("roe")
)

# --- Short Float ---
data["short_float_merged"] = (
    (data.get("finviz_short_float") / 100)
    if data.get("finviz_short_float") is not None
    else data.get("short_interest")
)

# --- SMA50 / SMA200 ---
# Finviz SMA values are % differences — NOT usable as SMAs.
data["sma50_merged"] = data.get("fifty_day_avg")
data["sma200_merged"] = data.get("two_hundred_day_avg")


# --- RSI ---
data["rsi_merged"] = (
    data.get("finviz_rsi")
    if data.get("finviz_rsi") is not None
    else data.get("rsi")
)

# --- Analyst Rating ---
def convert_finviz_recom(val):
    if val is None:
        return data.get("analyst_rating")
    try:
        v = float(val)
    except:
        return data.get("analyst_rating")

    if v <= 1.5:
        return "strong_buy"
    if v <= 2.5:
        return "buy"
    if v <= 3.5:
        return "hold"
    if v <= 4.5:
        return "sell"
    return "strong_sell"

data["analyst_rating_merged"] = convert_finviz_recom(data.get("finviz_recom"))

# --- Price Target ---
data["price_target_merged"] = (
    data.get("finviz_target_price")
    if data.get("finviz_target_price") is not None
    else None
)

enterprise_value = info.get("enterpriseValue")


# -----------------------------
# Save JSON
# -----------------------------
with open(f"{ticker}.json", "w") as f:
    json.dump(data, f, indent=4)

print(f"Saved {ticker}.json")
