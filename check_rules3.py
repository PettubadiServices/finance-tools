#!/usr/bin/env python3
import json
import sys

# Sector PE ranges - Always be the first and nothing before it
SECTOR_PE_RANGES = {
    "Technology": (18, 30),
    "Communication Services": (14, 22),
    "Consumer Cyclical": (12, 20),
    "Consumer Defensive": (15, 22),
    "Healthcare": (14, 22),
    "Financial Services": (10, 16),
    "Industrials": (12, 18),
    "Energy": (8, 12),
    "Basic Materials": (10, 16),
    "Real Estate": (25, 35),
    "Utilities": (14, 20)
}

# Trend strength
def trend_strength(price, sma50, sma200):
    """
    Classify trend strength using SMA50 and SMA200 structure.
    Returns (emoji, message)
    """

    if price is None or sma50 is None or sma200 is None:
        return ("⚪", "Trend data unavailable")

    # 1% tolerance around SMA200
    tol = 0.01
    above200 = price >= sma200 * (1 - tol)
    below200 = price <= sma200 * (1 + tol)

    # --- Strong Uptrend ---
    if price > sma50 > sma200:
        return ("🟢", "Strong uptrend")

    # --- Weak Uptrend ---
    if price > sma50 and sma50 < sma200:
        return ("🟡", "Weak uptrend")

    # --- Neutral Trend ---
    if (sma50 > price > sma200) or (sma200 > price > sma50):
        return ("⚪", "Neutral trend")

    # --- Weak Downtrend ---
    # Allow price to be slightly below SMA200 (within tolerance)
    if price < sma50 and above200:
        return ("🟠", "Weak downtrend")

    # --- Strong Downtrend ---
    if price < sma50 < sma200:
        return ("🔴", "Strong downtrend")

    return ("⚪", "Trend unclear")



# ============================
# Helper Functions (Option A)
# ============================

def pe_icon(pe):
    if pe is None:
        return "N/A"
    if pe < 15:
        return "🟢"
    if pe < 25:
        return "🟡"
    return "🔴"

def ev_icon(ev):
    if ev is None:
        return "N/A"
    if ev < 10:
        return "🟢"
    if ev < 20:
        return "🟡"
    return "🔴"

def fcf_icon(y):
    if y is None:
        return "N/A"
    if y > 0.05:
        return "🟢"
    if y > 0.03:
        return "🟡"
    return "🔴"

def roe_icon(r):
    if r is None:
        return "N/A"
    if r > 0.15:
        return "🟢"
    if r > 0.10:
        return "🟡"
    return "🔴"

# Normalize Div yields
def normalize_yield(value):
    """
    Normalize dividend yield values from Yahoo Finance.

    Rules:
    - None → None
    - 0 < value < 1 → already a decimal (e.g., 0.032 = 3.2%)
    - 1 ≤ value ≤ 25 → treat as percentage (e.g., 3.2 = 3.2%)
    - value > 25 → invalid (Yahoo error or special dividend)
    """
    if value is None:
        return None

    try:
        v = float(value)
    except:
        return None

    # Case 1: Already a decimal (0.0–1.0)
    if 0 < v < 1:
        return v

    # Case 2: Looks like a percentage (1–25)
    if 1 <= v <= 25:
        return v / 100.0

    # Case 3: Unrealistic → treat as invalid
    return None

# PE Helper - Issue resolution
def assess_sector_pe(forward_pe, sector_low, sector_high):
    """
    Compare a company's forward P/E to its sector range with graded severity.
    Returns a tuple: (emoji, message)
    """

    if forward_pe is None or sector_low is None or sector_high is None:
        return ("⚪", "Insufficient data for sector comparison")

    # Within sector range
    if sector_low <= forward_pe <= sector_high:
        return ("🟢", "Forward P/E is within sector average range")

    # Slightly above (0–10%)
    if forward_pe > sector_high and forward_pe <= sector_high * 1.10:
        return ("🟡", "Forward P/E slightly above sector average")

    # Moderately above (10–25%)
    if forward_pe > sector_high * 1.10 and forward_pe <= sector_high * 1.25:
        return ("🟠", "Forward P/E moderately above sector average")

    # Significantly above (>25%)
    if forward_pe > sector_high * 1.25:
        return ("🔴", "Forward P/E significantly above sector average")

    # Below sector range (value zone)
    if forward_pe < sector_low:
        return ("🟢", "Forward P/E below sector average — value zone")

    return ("⚪", "Unable to classify P/E relative to sector")



# ============================
# MAIN
# ============================

def main():
    if len(sys.argv) < 2:
        print("Usage: ./check_rules.py TICKER")
        sys.exit(1)

    ticker = sys.argv[1].upper()
    filename = f"{ticker}.json"

    # Load JSON
    try:
        with open(filename, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"

    print("\n=== BALANCE SHEET SIGNALS ===")

    debt = data.get("total_debt")
    cash = data.get("cash")
    ebitda = data.get("ebitda")
    fcf = data.get("free_cash_flow")

    # Net Debt
    if debt is not None and cash is not None:
        net_debt = debt - cash
        print(f"Total Debt: ${debt/1e9:.2f}B")
        print(f"Total Cash: ${cash/1e9:.2f}B")
        print(f"Net Debt:   ${net_debt/1e9:.2f}B")
    else:
        net_debt = None
        print("Net Debt: N/A")

    # EBITDA / Net Debt
    if ebitda is not None and net_debt is not None and net_debt != 0:
        ratio = ebitda / net_debt

        if ratio > 3:
            icon, color, label = "🟢", GREEN, "STRONG"
        elif ratio > 1:
            icon, color, label = "🟢", GREEN, "ACCEPTABLE"
        elif ratio > 0.5:
            icon, color, label = "🟡", YELLOW, "WATCH"
        else:
            icon, color, label = "🔴", RED, "HIGH DEBT"

        print(f"EBITDA: ${ebitda/1e9:.2f}B")
        print(f"{icon} {color}EBITDA / Net Debt: {ratio:.2f}x  {label}{RESET}")
    else:
        print("EBITDA / Net Debt: N/A")

    # FCF / Net Debt
    if fcf is not None and net_debt is not None and net_debt != 0:
        fcf_ratio = fcf / net_debt

        if fcf_ratio > 1:
            icon, color, label = "🟢", GREEN, "EXCELLENT — FCF covers all net debt"
        elif fcf_ratio > 0.3:
            icon, color, label = "🟢", GREEN, "GOOD — FCF covers debt over time"
        elif fcf_ratio >= 0:
            icon, color, label = "🟡", YELLOW, "WEAK — slow debt coverage"
        else:
            icon, color, label = "🔴", RED, "DANGER — negative FCF"

        print(f"Free Cash Flow: ${fcf/1e9:.2f}B")
        print(f"{icon} {color}FCF / Net Debt: {fcf_ratio:.2f}x  {label}{RESET}")
    else:
        print("FCF / Net Debt: N/A")

# --- IV Rank & Volatility Regime (using fields from JSON) ---

    iv = data.get("iv_current")
    iv_low = data.get("iv_low_52w")
    iv_high = data.get("iv_high_52w")
    iv_percentile = data.get("iv_percentile")
    vol_regime = data.get("vol_regime")

# IV Rank
    if iv_percentile is not None:
        print(f"IV Rank: {iv_percentile*100:.1f}%")
        if iv_percentile > 0.5:
            print("🟢 High IVR — strong premiums")
        else:
            print("🟡 Low IVR — weak premiums")
    else:
        print("IV Rank: N/A")

# Volatility Regime
    if vol_regime:
        print(f"Volatility Regime: {vol_regime.upper()} (IV percentile: {iv_percentile*100:.1f}%)")
    else:
        print("Volatility Regime: N/A")


    # ============================
    # DIVIDEND SAFETY
    # ============================
    div_yield_raw = data.get("dividendYield")
    avg_yield_raw = data.get("fiveYearAvgDividendYield")
    payout_ratio = data.get("payoutRatio")

    div_yield = normalize_yield(div_yield_raw)
    avg_yield = normalize_yield(avg_yield_raw)

    print("\n=== DIVIDEND SAFETY ===")

    # Dividend Yield
    if div_yield is None:
        print("Dividend Yield: unavailable (data error)")
    else:
        print(f"Dividend Yield: {div_yield*100:.2f}%")

    # 5yr Avg Yield
    if avg_yield is None:
        print("5yr Avg Yield:  unavailable (data error)")
    else:
        print(f"5yr Avg Yield:  {avg_yield*100:.2f}%")

    # Payout Ratio
    if payout_ratio is not None:
        print(f"🟢 Payout Ratio: {payout_ratio*100:.2f}%")


    # ============================
    # 52-WEEK RANGE
    # ============================
    price = data.get("price")
    high = data.get("52w_high")
    low = data.get("52w_low")

    if price and high and low and high != low:
        pos = (price - low) / (high - low)

        if pos < 0.2:
            icon, color, label = "🟢", GREEN, "value zone (near lows)"
        elif pos < 0.8:
            icon, color, label = "🟡", YELLOW, "mid-range"
        else:
            icon, color, label = "🔴", RED, "near highs"

        print(f"\n52-Week Range Position: {pos*100:.1f}%")
        print(f"{icon} {color}{label}{RESET}")
    else:
        print("\n52-Week Range Position: N/A")

    # ============================
    # PRICE TARGETS (Merged)
    # ============================
    print("\n=== PRICE TARGETS ===")

    pt = data.get("price_target_merged")

    if pt is not None:
        print(f"Price Target (Finviz): {pt}")
    else:
        print("Price Target: N/A")

    # ============================
    # VALUATION (Merged)
    # ============================
    print("\n=== VALUATION ===")

    fpe = data.get("forward_pe_merged")
    tpe = data.get("pe_ratio_merged")
    peg = data.get("peg_merged")

    # Enterprise Value and EV/EBITDA
    ev = data.get("enterprise_value")
    ev_ebitda = None
    if ev is not None and ebitda is not None and ebitda != 0:
        ev_ebitda = ev / ebitda

    # Free Cash Flow Yield
    market_cap = data.get("market_cap")
    fcfy = None
    if fcf is not None and market_cap:
        fcfy = fcf / market_cap

    print(f"{pe_icon(fpe)} Forward P/E:     {fpe}")
    print(f"{pe_icon(tpe)} Trailing P/E:    {tpe}")
    print(f"PEG Ratio:         {peg}")

    if ev_ebitda is not None:
        print(f"{ev_icon(ev_ebitda)} EV / EBITDA:     {ev_ebitda:.2f}")
    else:
        print("EV / EBITDA: N/A")

    if fcfy is not None:
        print(f"{fcf_icon(fcfy)} Free Cash Flow Yield: {fcfy*100:.2f}%")
    else:
        print("Free Cash Flow Yield: N/A")


    # ============================
    # GROWTH TRENDS
    # ============================
    print("\n=== GROWTH TRENDS ===")
    print(f"Revenue YoY Growth: {data.get('rev_yoy')}")
    print(f"EPS YoY Growth:     {data.get('eps_yoy')}")
    print(f"Revenue 3Y CAGR:    {data.get('rev_cagr')}")
    print(f"EPS 3Y CAGR:        {data.get('eps_cagr')}")

    # === COMPANY PROFILE ===
    print("\n=== COMPANY PROFILE ===")
    sector = data.get("sector")
    sector_low = data.get("sectorPELow")
    sector_high = data.get("sectorPEHigh")

    # From FinVIZ
    forward_pe = data.get("forward_pe_merged")


    print(f"Sector: {sector}")

    # Normalize sector key for fallback lookup
    sector_key = (sector or "").strip()

    # Apply fallback if Yahoo Finance did not provide sector P/E range
    if sector_low is None or sector_high is None:
        if sector_key in SECTOR_PE_RANGES:
            sector_low, sector_high = SECTOR_PE_RANGES[sector_key]

    print(f"Sector Avg P/E Range: {sector_low}–{sector_high}")

    emoji, msg = assess_sector_pe(forward_pe, sector_low, sector_high)
    print(f"{emoji} {msg}")


    # ============================
    # PROFITABILITY
    # ============================
    print("\n=== PROFITABILITY ===")
    roe = data.get("roe_merged")

    if roe is not None:
        print(f"{roe_icon(roe)} Return on Equity (ROE): {roe*100:.2f}%")
    else:
        print("Return on Equity (ROE): N/A")



    # Options signals prep work
    # Compute trend strength once
    f50 = data.get("sma50_merged")
    f200 = data.get("sma200_merged")

    price = data.get("price")

    # Compute trend stregnth once - for all csp, cc, and long call - option signals
    trend_emoji, trend_msg = trend_strength(price, f50, f200)

    # Trend Strength Scoring Adjustments
    trend_score_csp = 0
    trend_score_cc = 0
    trend_score_long = 0

    if trend_msg == "Strong uptrend":
        trend_score_csp += 1
        trend_score_cc -= 3
        trend_score_long += 3

    elif trend_msg == "Weak uptrend":
        trend_score_csp += 2
        trend_score_cc += 1
        trend_score_long += 2

    elif trend_msg == "Neutral trend":
        trend_score_csp += 2
        trend_score_cc += 2
        trend_score_long -= 1

    elif trend_msg == "Weak downtrend":
        trend_score_csp += 3
        trend_score_cc += 2
        trend_score_long -= 2

    elif trend_msg == "Strong downtrend":
        trend_score_csp -= 2
        trend_score_cc += 1
        trend_score_long -= 4

    
    # ============================
    # Volatility Regime Scoring Adjustments
    # ============================

    if vol_regime == "low":
        # Low IV → safer CSP, weaker CC, terrible for long calls
        trend_score_csp += 2
        trend_score_cc  -= 1
        trend_score_long -= 2

    elif vol_regime == "normal":
        # Neutral → no major adjustments
        pass

    elif vol_regime == "high":
        # High IV → risky CSP, great CC premiums, explosive long calls
        trend_score_csp -= 2
        trend_score_cc  += 2
        trend_score_long += 2

    # ============================
    # OPTIONS SIGNALS — CSP (Cash-Secured Puts)
    # ============================

    print("\n=== OPTIONS SIGNALS — CSP (New or Adding Position) ===")

    # Beta
    beta = data.get("beta")
    if beta is not None:
        if beta < 1:
            print(f"🟢 Beta: {beta:.2f}  (low volatility — safer CSP)")
        elif beta < 1.5:
            print(f"🟡 Beta: {beta:.2f}  (moderate volatility)")
        else:
            print(f"🔴 Beta: {beta:.2f}  (high volatility — risky CSP)")
    else:
        print("Beta: N/A")

    # Short Interest (Merged)
    si = data.get("short_float_merged")
    if si is not None:
        if si < 0.05:
            print(f"🟢 Short Interest: {si*100:.2f}%  (low squeeze/downside risk)")
        elif si < 0.15:
            print(f"🟡 Short Interest: {si*100:.2f}%  (moderate)")
        else:
            print(f"🔴 Short Interest: {si*100:.2f}%  (high — risky CSP)")
    else:
        print("Short Interest: N/A")



    # Earnings Countdown
    ed = data.get("earnings_date")
    if isinstance(ed, list) and len(ed) > 0:
        from datetime import datetime
        ed_date = datetime.fromtimestamp(ed[0])
        days = (ed_date - datetime.now()).days
        print(f"Earnings in {days} days")

        if days < 7:
            print("🔴 Earnings soon — high assignment risk")
        elif days < 21:
            print("🟡 Earnings approaching — moderate risk")
        else:
            print("🟢 Earnings not near — low CSP risk")
    else:
        print("Earnings Date: N/A")

    # Trend (50-day) — Merged
    f50 = data.get("sma50_merged")
    price = data.get("price")
    if f50 and price:
        if price > f50:
            print(f"🟢 Price above 50-day average — stable trend for CSP")
        else:
            print(f"🔴 Price below 50-day average — downtrend risk")
    else:
        print("50-day trend: N/A")

    print(f"{trend_emoji} {trend_msg}")

    if vol_regime:
        print(f"Volatility Regime: {vol_regime.upper()} (IV percentile: {iv_percentile*100:.1f}%)")
    else:
        print("Volatility Regime: N/A")

    if iv_percentile is not None:
        if iv_percentile < 0.3:
            print("🟡 Premiums: Low — CSP yield weaker in low IV")
        elif iv_percentile < 0.7:
            print("🟢 Premiums: Normal — balanced CSP premiums")
        else:
            print("🟢 Premiums: High — strong CSP premiums (but higher risk)")
    else:
        print("Premium Quality: N/A")


    # ============================
    # OPTIONS SIGNALS — COVERED CALLS (Existing Position)
    # ============================
    print("\n=== OPTIONS SIGNALS — COVERED CALLS (Existing Position) ===")

# IV Rank (Covered Calls)
    if iv_percentile is not None:
        print(f"IV Rank: {iv_percentile*100:.1f}%")
    else:
        print("IV Rank: N/A")

# Volatility Regime (Covered Calls)
    if vol_regime:
        print(f"Volatility Regime: {vol_regime.upper()} (IV percentile: {iv_percentile*100:.1f}%)")
    else:
        print("Volatility Regime: N/A")


    # RSI (Merged)
    rsi = data.get("rsi_merged")
    if rsi is not None:
        if rsi > 70:
            print(f"🟢 RSI: {rsi:.1f}  (overbought — great CC opportunity)")
        elif rsi < 30:
            print(f"🔴 RSI: {rsi:.1f}  (oversold — avoid CC)")
        else:
            print(f"🟡 RSI: {rsi:.1f}  (neutral)")
    else:
        print("RSI: N/A")

    # Trend
    if f50 and price:
        if price > f50:
            print(f"🟡 Price above 50-day — CC okay but may cap upside")
        else:
            print(f"🟢 Price below 50-day — CC safer (less upside risk)")
    else:
        print("50-day trend: N/A")

    # Analyst Rating (Merged)
    rating = data.get("analyst_rating_merged")
    if rating:
        print(f"Analyst Rating: {rating}")
    else:
        print("Analyst Rating: N/A")

    # Earnings Countdown
    if isinstance(ed, list) and len(ed) > 0:
        if days < 7:
            print("🔴 Earnings soon — avoid CC (IV crush risk)")
        elif days < 21:
            print("🟡 Earnings approaching — CC okay but cautious")
        else:
            print("🟢 Earnings not near — CC safe")
    else:
        print("Earnings Date: N/A")

    if vol_regime:
        print(f"Volatility Regime: {vol_regime.upper()} (IV percentile: {iv_percentile*100:.1f}%)")
    else:
        print("Volatility Regime: N/A")


    # ============================
    # OPTIONS SIGNALS — LONG CALLS (Bullish Directional)
    # ============================
    print("\n=== OPTIONS SIGNALS — LONG CALLS (Bullish Directional) ===")

    # RSI (already merged earlier)
    if rsi is not None:
        if rsi < 30:
            print(f"🟢 RSI: {rsi:.1f}  (oversold — good long call setup)")
        elif rsi > 70:
            print(f"🔴 RSI: {rsi:.1f}  (overbought — avoid long calls)")
        else:
            print(f"🟡 RSI: {rsi:.1f}  (neutral)")
    else:
        print("RSI: N/A")

    # Trend
    if f50 and price:
        if price > f50:
            print(f"🟢 Price above 50-day — bullish trend")
        else:
            print(f"🔴 Price below 50-day — bearish trend")
    else:
        print("50-day trend: N/A")

    # Analyst Rating (Merged)
    rating = data.get("analyst_rating_merged")
    if rating:
        print(f"Analyst Rating: {rating}")
    else:
        print("Analyst Rating: N/A")

    # Earnings Countdown
    if isinstance(ed, list) and len(ed) > 0:
        if days < 7:
            print("🔴 Earnings soon — avoid long calls (IV crush)")
        elif days < 21:
            print("🟡 Earnings approaching — risky long calls")
        else:
            print("🟢 Earnings not near — safer for long calls")
    else:
        print("Earnings Date: N/A")

    # Beta
    if beta is not None:
        if beta < 1:
            print(f"🟡 Beta: {beta:.2f}  (low volatility — weak for long calls)")
        elif beta < 1.5:
            print(f"🟢 Beta: {beta:.2f}  (good volatility for long calls)")
        else:
            print(f"🟡 Beta: {beta:.2f}  (high volatility — risky but explosive)")
    else:
        print("Beta: N/A")

    if vol_regime:
        print(f"Volatility Regime: {vol_regime.upper()} (IV percentile: {iv_percentile*100:.1f}%)")
    else:
        print("Volatility Regime: N/A")

    # ============================
    # OPTIONS SUMMARY SCORE
    # ============================
    print("\n=== OPTIONS SUMMARY SCORE ===")

    def score_icon(score):
        if score >= 7:
            return "🟢"
        if score >= 4:
            return "🟡"
        return "🔴"

    # --- CSP Score ---
    csp_score = 0

    # Beta
    if beta is not None:
        if beta < 1: csp_score += 3
        elif beta < 1.5: csp_score += 2
        else: csp_score += 1

    # Short Interest (already merged earlier)
    if si is not None:
        if si < 0.05: csp_score += 3
        elif si < 0.15: csp_score += 2
        else: csp_score += 1

    # IV Rank
    if iv_percentile is not None:
        if iv_percentile > 0.5: csp_score += 3
        else: csp_score += 1

    # Trend
    if f50 and price:
        if price > f50: csp_score += 2
        else: csp_score += 1

    # Put/Call Ratio
    pcr = data.get("put_call_ratio")
    if pcr is not None:
        if pcr < 0.8: csp_score += 3
        elif pcr < 1.2: csp_score += 2
        else: csp_score += 1

    print(f"CSP Suitability: {score_icon(csp_score)} {csp_score}/10")

    # --- COVERED CALL Score ---
    cc_score = 0

    # IV Rank
    if iv_percentile is not None:
        if iv_percentile > 0.5: cc_score += 3
        else: cc_score += 1

    # RSI (already merged earlier)
    if rsi is not None:
        if rsi > 70: cc_score += 3
        elif rsi < 30: cc_score += 1
        else: cc_score += 2

    # Trend
    if f50 and price:
        if price < f50: cc_score += 3
        else: cc_score += 1

    # PCR
    if pcr is not None:
        if pcr > 1.2: cc_score += 3
        elif pcr > 0.8: cc_score += 2
        else: cc_score += 1

    print(f"Covered Call Suitability: {score_icon(cc_score)} {cc_score}/10")

    # --- LONG CALL Score ---
    lc_score = 0

    # RSI (already merged earlier)
    if rsi is not None:
        if rsi < 30: lc_score += 3
        elif rsi > 70: lc_score += 1
        else: lc_score += 2

    # Trend
    if f50 and price:
        if price > f50: lc_score += 3
        else: lc_score += 1

    # Beta
    if beta is not None:
        if beta < 1: lc_score += 1
        elif beta < 1.5: lc_score += 3
        else: lc_score += 2

    # Analyst Rating (Merged)
    rating = data.get("analyst_rating_merged")
    if rating:
        if rating in ("strong_buy", "buy"): lc_score += 3
        elif rating == "hold": lc_score += 2
        else: lc_score += 1

    # PCR
    if pcr is not None:
        if pcr < 0.8: lc_score += 3
        elif pcr < 1.2: lc_score += 2
        else: lc_score += 1

    print(f"Long Call Suitability: {score_icon(lc_score)} {lc_score}/10")

if __name__ == "__main__":
    main()



