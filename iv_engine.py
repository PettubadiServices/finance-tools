import math
import json
import os
from datetime import datetime, timedelta

IV_HISTORY_FILE = "iv_history.json"

def _norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def _bs_call_price(S, K, T, r, sigma):
    if sigma <= 0 or T <= 0:
        return max(S - K, 0.0)
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return S * _norm_cdf(d1) - K * math.exp(-r * T) * _norm_cdf(d2)

def implied_vol_call(S, K, T, r, market_price, tol=1e-4, max_iter=100):
    # Simple bisection
    low, high = 1e-4, 5.0
    for _ in range(max_iter):
        mid = 0.5 * (low + high)
        price = _bs_call_price(S, K, T, r, mid)
        if abs(price - market_price) < tol:
            return mid
        if price > market_price:
            high = mid
        else:
            low = mid
    return None

def load_iv_history():
    if not os.path.exists(IV_HISTORY_FILE):
        return {}
    with open(IV_HISTORY_FILE, "r") as f:
        try:
            return json.load(f)
        except Exception:
            return {}

def save_iv_history(history):
    with open(IV_HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def update_iv_history(ticker, iv_value):
    history = load_iv_history()
    today = datetime.utcnow().strftime("%Y-%m-%d")
    if ticker not in history:
        history[ticker] = []
    history[ticker].append({"date": today, "iv": iv_value})
    # keep last 400 entries
    history[ticker] = history[ticker][-400:]
    save_iv_history(history)
    return history[ticker]

def compute_iv_stats(ticker, iv_current):
    # returns iv_current, iv_52w_low, iv_52w_high, iv_percentile
    if iv_current is None:
        return None, None, None, None

    hist = update_iv_history(ticker, iv_current)
    # last 252 trading days approx
    cutoff = (datetime.utcnow() - timedelta(days=365)).strftime("%Y-%m-%d")
    vals = [h["iv"] for h in hist if h["date"] >= cutoff and h["iv"] is not None]

    if not vals:
        return iv_current, None, None, None

    iv_low = min(vals)
    iv_high = max(vals)
    if iv_high > iv_low:
        iv_pct = (iv_current - iv_low) / (iv_high - iv_low)
        iv_pct = max(0.0, min(1.0, iv_pct))
    else:
        iv_pct = None

    return iv_current, iv_low, iv_high, iv_pct

