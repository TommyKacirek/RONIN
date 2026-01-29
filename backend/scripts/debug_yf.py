import yfinance as yf

print("Testing AAPL...")
try:
    data = yf.download("AAPL", period="1d")
    print(data)
except Exception as e:
    print(f"AAPL failed: {e}")

print("\nTesting CZK=X...")
try:
    data = yf.download("CZK=X", period="1d")
    print(data)
except Exception as e:
    print(f"CZK=X failed: {e}")

print("\nTesting USDCZK=X...")
try:
    data = yf.download("USDCZK=X", period="1d") # Try alternate
    print(data)
except Exception as e:
    print(f"USDCZK=X failed: {e}")
