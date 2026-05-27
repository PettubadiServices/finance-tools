#!/usr/bin/env python3
import json
import sys

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

# Sector P/E ranges
sector_pe_ranges = {
    "Technology": (20, 35),
    "Consumer Cyclical": (15, 25),
    "Industrials": (15, 22),
    "Healthcare": (15, 25),
    "Financial Services": (10, 15),
    "Energy": (8, 12),
    "Utilities": (12, 18),
    "Real Estate": (15, 25),
    "Basic Materials": (12, 18),
    "Communication Services": (15, 25),
    "Consumer Defensive": (15, 22),
}

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
    if ebitda is not None and net_debt and net_debt != 0:
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
    if fcf is not None and net_debt and net_debt != 0:
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

    # ============================
    # DIVIDEND SAFETY
    # ============================
    print("\n=== DIVIDEND SAFETY ===")

    div_yield = data.get("dividend_yield")
    div_5yr = data.get("five_year_avg_dividend_yield")
    payout = data.get("payout_ratio")

    if not div_yield and not payout:
        print("This is a non‑dividend‑paying stock.")
    else:
        if div_yield:
            print(f"Dividend Yield: {div_yield*100:.2f}%")
        else:
            print("Dividend Yield: N/A")

        if div_5yr:
            print(f"5yr Avg Yield:  {div_5yr*100:.2f}%")
        else:
            print("5yr Avg Yield:  N/A")

        if payout is not None:
            icon = "🟢" if payout < 0.5 else "🟡" if payout < 0.8 else "🔴"
            print(f"{icon} Payout Ratio: {payout*100:.2f}%")
        else:
            print("Payout Ratio: N/A")

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
    # PRICE TARGETS
    # ============================
    print("\n=== PRICE TARGETS ===")
    avg_pt = data.get("avg_pt")
    high_pt = data.get("high_pt")
    low_pt = data.get("low_pt")
    pt_up = data.get("pt_up")

    print(f"Average Price Target: {avg_pt}")
    print(f"High Price Target:    {high_pt}")
    print(f"Low Price Target:     {low_pt}")

    if pt_up is not None:
        icon = "🟢" if pt_up > 0 else "🔴"
        print(f"{icon} Upside to Avg PT: {pt_up*100:.1f}%")
    else:
        print("Upside to Avg PT: N/A")

    # ============================
    # VALUATION
    # ============================
    print("\n=== VALUATION ===")

    fpe = data.get("forward_pe")
    tpe = data.get("trailing_pe")
    peg = data.get("peg")
    ev = data.get("ev_ebitda")
    fcfy = data.get("fcf_yield")

    print(f"{pe_icon(fpe)} Forward P/E:     {fpe}")
    print(f"{pe_icon(tpe)} Trailing P/E:    {tpe}")
    print(f"PEG Ratio:         {peg}")
    print(f"{ev_icon(ev)} EV / EBITDA:     {ev}")

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

    # ============================
    # COMPANY PROFILE
    # ============================
    print("\n=== COMPANY PROFILE ===")
    sector = data.get("sector")
    print(f"Sector: {sector}")

    if sector in sector_pe_ranges and fpe is not None:
        low, high = sector_pe_ranges[sector]
        print(f"Sector Avg P/E Range: {low}–{high}")

        if fpe < low:
            print("🟢 Forward P/E is below sector average")
        elif fpe > high:
            print("🔴 Forward P/E is above sector average")
        else:
            print("🟡 Forward P/E is within sector range")
    else:
        print("Sector P/E comparison not available")

    # ============================
    # PROFITABILITY
    # ============================
    print("\n=== PROFITABILITY ===")
    roe = data.get("roe")
    if roe is not None:
        print(f"{roe_icon(roe)} Return on Equity (ROE): {roe*100:.2f}%")
    else:
        print("Return on Equity (ROE): N/A")


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

    # Short Interest
    si = data.get("short_interest")
    if si is not None:
        if si < 0.05:
            print(f"🟢 Short Interest: {si*100:.2f}%  (low squeeze/downside risk)")
        elif si < 0.15:
            print(f"🟡 Short Interest: {si*100:.2f}%  (moderate)")
        else:
            print(f"🔴 Short Interest: {si*100:.2f}%  (high — risky CSP)")
    else:
        print("Short Interest: N/A")

    # IV Rank
    ivr = data.get("ivr")
    if ivr is not None:
        print(f"IV Rank: {ivr*100:.1f}%")
        if ivr > 0.5:
            print("🟢 High IVR — strong CSP premiums")
        else:
            print("🟡 Low IVR — weak CSP premiums")
    else:
        print("IV Rank: N/A")

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

    # Trend (50-day)
    f50 = data.get("fifty_day_avg")
    price = data.get("price")
    if f50 and price:
        if price > f50:
            print(f"🟢 Price above 50-day average — stable trend for CSP")
        else:
            print(f"🔴 Price below 50-day average — downtrend risk")
    else:
        print("50-day trend: N/A")

    # ============================
    # OPTIONS SIGNALS — COVERED CALLS (Existing Position)
    # ============================
    print("\n=== OPTIONS SIGNALS — COVERED CALLS (Existing Position) ===")

    # IV Rank
    if ivr is not None:
        print(f"IV Rank: {ivr*100:.1f}%")
        if ivr > 0.5:
            print("🟢 High IVR — excellent time to sell calls")
        else:
            print("🟡 Low IVR — premiums may be weak")
    else:
        print("IV Rank: N/A")

    # RSI
    rsi = data.get("rsi")
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

    # Analyst Rating
    rating = data.get("analyst_rating")
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

    # ============================
    # OPTIONS SIGNALS — LONG CALLS (Bullish Directional)
    # ============================
    print("\n=== OPTIONS SIGNALS — LONG CALLS (Bullish Directional) ===")

    # RSI
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

    # Analyst Rating
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

    # ============================
    # OPTIONS SUMMARY SCORE
    # ============================
    print("\n=== OPTIONS SUMMARY SCORE ===")

    # Helper scoring function
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

    # Short Interest
    if si is not None:
        if si < 0.05: csp_score += 3
        elif si < 0.15: csp_score += 2
        else: csp_score += 1

    # IV Rank
    if ivr is not None:
        if ivr > 0.5: csp_score += 3
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
    if ivr is not None:
        if ivr > 0.5: cc_score += 3
        else: cc_score += 1

    # RSI
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

    # RSI
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

    # Analyst Rating
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
