#!/usr/bin/env python3
import yfinance as yf
import json
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
datetime.now(timezone.utc)
import math
import pandas as pd


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
# Black-Scholes IV Solver
# -----------------------------
def norm_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))

def bs_call_price(S, K, T, r, sigma):
    if sigma <= 0 or T <= 0:
        return max(S - K, 0)
    d1 = (math.log(S/K) + (r + 0.5*sigma*sigma)*T) / (sigma*math.sqrt(T))
    d2 = d1 - sigma*math.sqrt(T)
    return S * norm_cdf(d1) - K * math.exp(-r*T) * norm_cdf(d2)

def implied_vol_call(S, K, T, r, market_price, tol=1e-4, max_iter=100):
    low, high = 1e-4, 5.0
    for _ in range(max_iter):
        mid = (low + high) / 2
        price = bs_call_price(S, K, T, r, mid)
        if abs(price - market_price) < tol:
            return mid
        if price > market_price:
            high = mid
        else:
            low = mid
    return None


# -----------------------------
# Compute ATM IV from option chain
# -----------------------------
def compute_atm_iv_from_chain(ticker, price):
    try:
        tk = yf.Ticker(ticker)
        expiries = tk.options
        if not expiries:
            return None

        expiry = expiries[0]  # nearest expiry
        chain = tk.option_chain(expiry)
        calls = chain.calls
        if calls.empty:
            return None

        calls = calls.copy()

        # Compute mid price
        calls["bid"] = calls["bid"].fillna(0.0)
        calls["ask"] = calls["ask"].fillna(0.0)
        calls["mid"] = (calls["bid"] + calls["ask"]) / 2.0

        # Filter to only calls with real quotes
        tradable = calls[calls["mid"] > 0]

        if tradable.empty:
            # Market likely closed → fallback to lastPrice
            calls["mid"] = calls["lastPrice"].fillna(0.0)
            tradable = calls[calls["mid"] > 0]

        if tradable.empty:
            # Final fallback → use Yahoo's impliedVolatility
            return tk.info.get("impliedVolatility", None)

        # Choose ATM from tradable calls
        tradable["dist"] = (tradable["strike"] - price).abs()
        atm = tradable.sort_values("dist").iloc[0]

        K = float(atm["strike"])
        mid = float(atm["mid"])

        # time to expiry in years
        exp_dt = datetime.strptime(expiry, "%Y-%m-%d")

        from datetime import timezone
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)

        T = max((exp_dt - now_utc).days, 1) / 365.0
        r = 0.02  # constant risk-free rate

        return implied_vol_call(price, K, T, r, mid)

    except Exception as e:
        print("IV ERROR:", e)
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
    "put_call_ratio": info.get("putCallRatio"),

}


# -----------------------------
# Compute IV from option chain
# -----------------------------
price = data["price"]
iv_current = compute_atm_iv_from_chain(ticker, price)

data["iv_current"] = iv_current
data["iv_low_52w"] = iv_current
data["iv_high_52w"] = iv_current

# -----------------------------
# IV History (local 52-week tracking)
# -----------------------------
HIST_FILE = "iv_history.json"

# Load history
try:
    with open(HIST_FILE, "r") as f:
        iv_hist = json.load(f)
except:
    iv_hist = {}

from datetime import timezone
today = datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d")


if ticker not in iv_hist:
    iv_hist[ticker] = []

# Append today's IV
if iv_current is not None:
    iv_hist[ticker].append({"date": today, "iv": iv_current})
    iv_hist[ticker] = iv_hist[ticker][-400:]  # keep last 400 entries

# Save history
with open(HIST_FILE, "w") as f:
    json.dump(iv_hist, f, indent=2)

# Compute 52-week high/low
vals = [x["iv"] for x in iv_hist[ticker] if x["iv"] is not None]
if vals:
    data["iv_low_52w"] = min(vals)
    data["iv_high_52w"] = max(vals)
else:
    data["iv_low_52w"] = None
    data["iv_high_52w"] = None

def compute_atm_iv_from_chain(ticker, price):
    try:
        tk = yf.Ticker(ticker)
        expiries = tk.options
        if not expiries:
            return None

        # nearest expiry
        expiry = expiries[0]
        chain = tk.option_chain(expiry)
        calls = chain.calls
        if calls.empty:
            return None

        # find ATM call
        calls["dist"] = (calls["strike"] - price).abs()
        atm = calls.sort_values("dist").iloc[0]

        K = float(atm["strike"])
        bid = float(atm.get("bid", 0.0))
        ask = float(atm.get("ask", 0.0))
        mid = (bid + ask) / 2.0
        if mid <= 0:
            return None

        # -----------------------------
        # FIXED TIME-TO-EXPIRY BLOCK
        # -----------------------------
        exp_dt = datetime.strptime(expiry, "%Y-%m-%d")

        from datetime import timezone
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)

        T = max((exp_dt - now_utc).days, 1) / 365.0
        r = 0.02  # constant risk-free rate

        return implied_vol_call(price, K, T, r, mid)

    except Exception as e:
        print("IV ERROR:", e)
        return None



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
# Implied Volatility Rank (from our own IV engine)
# -----------------------------
iv = data.get("iv_current")
iv_low = data.get("iv_low_52w")
iv_high = data.get("iv_high_52w")

iv_percentile = None
vol_regime = None

if iv is not None and iv_low is not None and iv_high is not None:
    if iv_high > iv_low:
        iv_percentile = (iv - iv_low) / (iv_high - iv_low)
        iv_percentile = max(0.0, min(1.0, iv_percentile))
    else:
        # No range yet → treat as neutral
        iv_percentile = 0.5

    if iv_percentile < 0.3:
        vol_regime = "low"
    elif iv_percentile < 0.7:
        vol_regime = "normal"
    else:
        vol_regime = "high"

data["iv_percentile"] = iv_percentile
data["vol_regime"] = vol_regime




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
