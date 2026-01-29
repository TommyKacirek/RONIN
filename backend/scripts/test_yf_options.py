import yfinance as yf
import sys

# Test Symbols
# 1. SOFI 20FEB26 26 P -> SOFI260220P00026000
# 2. SPY 30JUN26 660 P -> SPY260630P00660000

symbols = [
    "SOFI260220P00026000",
    "SPY260630P00660000"
]

print(f"Fetching data for: {symbols}")

for sym in symbols:
    print(f"\n--- {sym} ---")
    try:
        t = yf.Ticker(sym)
        fi = t.fast_info
        print(f"Last Price: {fi.last_price}")
        print(f"Prev Close: {fi.previous_close}")
        
        # Also try history
        hist = t.history(period="1d")
        if not hist.empty:
            print(f"History Last: {hist['Close'].iloc[-1]}")
            print(f"Volume: {hist['Volume'].iloc[-1]}")
        else:
            print("History empty")
            
    except Exception as e:
        print(f"Error: {e}")
