# finance-tools
Looking to extract public knowledge into sorting and filtering high quality stocks for long term, cash secured puts, covered calls, and long calls


============================================================
TRAINING MANUAL — FINANCE-TOOLS ANALYZER (VERSION 1.0)
============================================================
Author: [Your Name]
System: Linux Mint (or any Debian/Ubuntu-based distro)
Purpose: Stock + Options Analysis Pipeline with Clean Output
Version: 1.0
============================================================


============================================================
SECTION 1 — HOW TO RUN THE SCRIPT
============================================================

This system analyzes a stock ticker by:

    1. Fetching fresh data from Yahoo Finance
    2. Saving it into a JSON file
    3. Running a rules engine to evaluate fundamentals,
       technicals, options signals, and valuation
    4. Printing a full analysis to the terminal
    5. Optionally cleaning the output to remove N/A fields

------------------------------------------------------------
1.1 — Basic Usage
------------------------------------------------------------

Run a full analysis:

    ./analyze AAPL

This automatically:
    - Fetches data
    - Saves AAPL.json
    - Runs the rules engine
    - Prints the analysis

------------------------------------------------------------
1.2 — Clean Output (Recommended)
------------------------------------------------------------

To remove lines containing:
    - N/A
    - None
    - null
    - missing
    - unknown

Run:

    ./analyze AAPL | ./remove-NA-fields-from-output.py

This produces a clean, readable summary.

------------------------------------------------------------
1.3 — Running Inside the Virtual Environment
------------------------------------------------------------

Your wrapper script already uses:

    ./venv/bin/python

So you do NOT need to activate the venv manually.

If you want to:

    source venv/bin/activate

------------------------------------------------------------
1.4 — Pipeline Overview
------------------------------------------------------------

    fetch_ticker.py
          ↓
    Saves TICKER.json
          ↓
    check_rules2.py
          ↓
    Full analysis printed
          ↓
    remove-NA-fields-from-output.py (optional)
          ↓
    Cleaned output

------------------------------------------------------------
1.5 — Example Commands
------------------------------------------------------------

Analyze TSLA:

    ./analyze TSLA

Clean output:

    ./analyze TSLA | ./remove-NA-fields-from-output.py

Save cleaned output:

    ./analyze TSLA | ./remove-NA-fields-from-output.py > tsla.txt

------------------------------------------------------------
1.6 — Troubleshooting
------------------------------------------------------------

Permission denied:
    chmod +x analyze
    chmod +x remove-NA-fields-from-output.py

Missing yfinance:
    ./venv/bin/pip install yfinance

BrokenPipeError:
    Normal when piping output and stopping early.

============================================================
END OF SECTION 1
============================================================



============================================================
SECTION 2 — WRAPPER SCRIPT (analyze)
============================================================

The wrapper script orchestrates the entire workflow.

It ensures:

    - The correct Python interpreter is used
    - Data is fetched before analysis
    - Output is consistent
    - You can pipe into the cleaner script

------------------------------------------------------------
2.1 — Purpose
------------------------------------------------------------

The wrapper:

    - Converts ticker to uppercase
    - Calls fetch_ticker.py
    - Calls check_rules2.py
    - Allows piping into the cleaner

------------------------------------------------------------
2.2 — How It Works
------------------------------------------------------------

1. Takes the ticker argument
2. Converts it to uppercase
3. Uses venv Python
4. Fetches data
5. Runs the rules engine

------------------------------------------------------------
2.3 — Extending the Wrapper
------------------------------------------------------------

You can add:

    --clean
    --save
    --batch
    --compact

You can also make it read tickers from a file.

============================================================
END OF SECTION 2
============================================================



============================================================
SECTION 3 — FETCH DATA (fetch_ticker.py)
============================================================

This script is the foundation of the system.

It:

    - Connects to Yahoo Finance
    - Pulls raw financial, technical, and options data
    - Computes derived metrics
    - Saves everything into a JSON file

------------------------------------------------------------
3.1 — What the Script Does
------------------------------------------------------------

1. Reads the ticker from command line
2. Fetches data using yfinance
3. Extracts dozens of fields:
       - Price
       - Market cap
       - PE ratios
       - PEG
       - Margins
       - Debt, cash, EBITDA
       - Free cash flow
       - Sector
       - ROE
       - Beta
       - Short interest
       - RSI
       - Implied volatility
       - 52-week high/low
       - Analyst rating
       - Dividend data
       - Price targets
4. Computes:
       - Price target upside
       - EV/EBITDA
       - FCF yield
       - IV Rank
       - Expected move
5. Saves everything into TICKER.json

------------------------------------------------------------
3.2 — Key Metrics and Their Meaning
------------------------------------------------------------

PRICE & MARKET DATA
-------------------
price — current trading price  
market_cap — total company value  

VALUATION
---------
forward_pe — valuation based on future earnings  
trailing_pe — valuation based on past earnings  
peg — valuation adjusted for growth  
ev_ebitda — enterprise value vs cash earnings  
fcf_yield — free cash flow relative to market cap  

GROWTH
------
revenue_growth — quarterly YoY revenue  
eps_growth — quarterly YoY earnings  
rev_yoy — annual revenue growth  
eps_yoy — annual earnings growth  

BALANCE SHEET
-------------
total_debt — total debt  
cash — cash on hand  
ebitda — operating cash earnings  
free_cash_flow — cash after capex  
roe — return on equity  

TECHNICALS
----------
fifty_day_avg — 50-day moving average  
200dma — 200-day moving average  
52w_high / 52w_low — yearly range  
rsi — momentum indicator  

OPTIONS
-------
iv_current — implied volatility  
iv_high_52w / iv_low_52w — IV range  
ivr — IV Rank  
put_call_ratio — sentiment indicator  
expected_move — 30-day expected move  

ANALYST
-------
analyst_rating — buy/hold/sell  
short_interest — percent of float short  

DIVIDENDS
---------
dividend_yield  
five_year_avg_dividend_yield  
payout_ratio  

------------------------------------------------------------
3.3 — JSON Output
------------------------------------------------------------

The script saves:

    TICKER.json

This file contains all raw and computed fields.

------------------------------------------------------------
3.4 — Assumptions & Limitations
------------------------------------------------------------

ASSUMPTIONS
-----------
- Yahoo Finance data is accurate
- Missing fields become None
- Expected move uses 30-day IV
- IV Rank uses 52-week IV range

LIMITATIONS
-----------
- Yahoo sometimes returns nulls
- Some fields (like CAGR) are unavailable
- Earnings date may be a list
- Free cash flow may be missing

============================================================
END OF SECTION 3
============================================================



============================================================
SECTION 4 — RULES ENGINE (check_rules2.py)
============================================================

This is the heart of the analysis system.

It loads TICKER.json and evaluates:

    - Balance sheet strength
    - Dividend safety
    - 52-week range position
    - Price target upside
    - Valuation
    - Growth trends
    - Sector comparison
    - Profitability
    - Options signals:
          • CSP (cash-secured puts)
          • Covered calls
          • Long calls
    - Summary scores for each strategy

------------------------------------------------------------
4.1 — Major Sections of the Rules Engine
------------------------------------------------------------

BALANCE SHEET SIGNALS
---------------------
Evaluates:
    - Total debt
    - Cash
    - Net debt
    - EBITDA / Net Debt
    - FCF / Net Debt

Classifies leverage as:
    - STRONG
    - ACCEPTABLE
    - WATCH
    - HIGH DEBT

DIVIDEND SAFETY
----------------
Evaluates:
    - Dividend yield
    - 5-year average yield
    - Payout ratio

52-WEEK RANGE
--------------
Determines where price sits between:
    - 52w low
    - 52w high

Classifies:
    - Value zone (near lows)
    - Mid-range
    - Near highs

PRICE TARGETS
--------------
Evaluates:
    - Average price target
    - High/low targets
    - Upside percentage

VALUATION
---------
Evaluates:
    - Forward PE
    - Trailing PE
    - PEG
    - EV/EBITDA
    - FCF yield

GROWTH TRENDS
--------------
Evaluates:
    - Revenue YoY
    - EPS YoY
    - Revenue CAGR (None)
    - EPS CAGR (None)

COMPANY PROFILE
----------------
Evaluates:
    - Sector
    - Sector PE range
    - Whether forward PE is cheap/expensive vs sector

PROFITABILITY
--------------
Evaluates:
    - ROE (Return on Equity)

OPTIONS SIGNALS — CSP
----------------------
Evaluates:
    - Beta
    - Short interest
    - IV Rank
    - Earnings proximity
    - Trend (50-day)
    - Put/Call ratio

OPTIONS SIGNALS — COVERED CALLS
--------------------------------
Evaluates:
    - IV Rank
    - RSI
    - Trend
    - Analyst rating
    - Earnings proximity
    - Put/Call ratio

OPTIONS SIGNALS — LONG CALLS
-----------------------------
Evaluates:
    - RSI
    - Trend
    - Analyst rating
    - Earnings proximity
    - Beta
    - Put/Call ratio

SUMMARY SCORES
---------------
Each strategy (CSP, CC, Long Call) receives a score out of 10.

============================================================
END OF SECTION 4
============================================================



============================================================
SECTION 5 — CLEANING OUTPUT
============================================================

The cleaner script removes lines containing:

    - N/A
    - None
    - null
    - missing
    - unknown

It preserves:

    - Section headers
    - All meaningful data
    - Formatting

This produces a clean, readable summary.

------------------------------------------------------------
5.1 — How It Works
------------------------------------------------------------

1. Reads all lines from stdin  
2. Removes lines matching skip patterns  
3. Collapses multiple blank lines  
4. Prints cleaned output  

------------------------------------------------------------
5.2 — Why It Matters
------------------------------------------------------------

Yahoo Finance often returns nulls.

The cleaner ensures:

    - Clean output
    - No clutter
    - No noise
    - Easy scanning
    - Better readability

============================================================
END OF SECTION 5
============================================================



============================================================
SECTION 6 — FILES SAVED
============================================================

The system saves:

    TICKER.json

This file contains:

    - Raw data
    - Computed metrics
    - Derived fields

You can:

    - Re-analyze old JSON files
    - Build historical datasets
    - Import into Excel
    - Use for batch processing

------------------------------------------------------------
6.1 — Archiving JSON Files
------------------------------------------------------------

Recommended structure:

    data/
        2024-01-01/
            AAPL.json
            MSFT.json
        2024-01-02/
            AAPL.json
            MSFT.json

------------------------------------------------------------
6.2 — Using JSON for Excel
------------------------------------------------------------

You can convert JSON → Excel columns for:

    - Sorting
    - Filtering
    - Ranking
    - Portfolio analysis

============================================================
END OF SECTION 6
============================================================



============================================================
SECTION 7 — FUTURE ENHANCEMENTS
============================================================

This section outlines the roadmap for Version 2 and beyond.

------------------------------------------------------------
7.1 — Excel Integration
------------------------------------------------------------

Add the ability to:

    - Export JSON fields into Excel columns
    - Auto-run fetcher for tickers with empty rows
    - Update Excel daily (pre-market or post-market)
    - Track:
          • P/L
          • Net worth
          • Position sizing
          • Options income

------------------------------------------------------------
7.2 — Multi-Ticker Automation
------------------------------------------------------------

Enhance the wrapper to:

    - Read tickers from Excel column A
    - Loop through each
    - Fetch → Analyze → Write results
    - Skip tickers already updated today

------------------------------------------------------------
7.3 — Cloud Access
------------------------------------------------------------

Store Excel in:

    - OneDrive
    - Google Drive
    - iCloud

Access from:

    - iPad
    - iPhone
    - Any browser

------------------------------------------------------------
7.4 — AI Upload Workflow
------------------------------------------------------------

Upload Excel to:

    - Claude
    - ChatGPT
    - Gemini

Ask questions like:

    - “Which positions are overvalued?”
    - “Which stocks have the strongest CSP score?”
    - “What is my net worth trend?”

------------------------------------------------------------
7.5 — Net Worth Management System
------------------------------------------------------------

Track:

    - Positions
    - Average cost
    - Market value
    - Unrealized P/L
    - Realized P/L
    - Dividends
    - Options income
    - Cash
    - Debt
    - Savings

Build:

    - Monthly net worth chart
    - Income vs expenses
    - Options income tracker
    - CSP/CC performance tracker

------------------------------------------------------------
7.6 — Advanced Analytics
------------------------------------------------------------

Add:

    - IV trend
    - MACD
    - Volume surge
    - Max pain
    - Expected move bands
    - Breakout probability
    - Multi-sigma ranges
    - Earnings volatility crush
    - Sector heatmaps
    - Portfolio risk metrics

============================================================
END OF SECTION 7
============================================================


============================================================
END OF TRAINING MANUAL (VERSION 1.0)
============================================================

