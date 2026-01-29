import os
import pandas as pd
from backend.app.services.parser import IBKRParser
from backend.app.services.merger import DataMerger
from backend.app.services.reconstructor import PortfolioReconstructor

# Setup
parser = IBKRParser()
merger = DataMerger()
reconstructor = PortfolioReconstructor()

data_dir = "backend/data"
files = [f for f in os.listdir(data_dir) if f.endswith(".csv")]
files = [os.path.join(data_dir, f) for f in files]
print(f"Files: {files}")

# Parse
parsed_data = []
for f in files:
    parsed_data.append(parser.parse_csv(f))

# Merge
merged = merger.merge(parsed_data)

# Check Financial Info
fin_info = merged.get('Financial Instrument Information')
if fin_info is not None and not fin_info.empty:
    print("\n--- Financial Instrument Info (First 5 rows) ---")
    print(fin_info.head())
    print("Columns:", list(fin_info.columns))
    
    # Check for EVO
    col0 = next((c for c in fin_info.columns if 'Symbol' in c), None)
    if col0:
        print(f"Using Symbol Column: {col0}")
        evo_rows = fin_info[fin_info[col0].astype(str).str.contains('EVO')]
        print("\n--- EVO Rows ---")
        print(evo_rows)
else:
    print("Financial Instrument Information MISSING or EMPTY")

# Reconstruct
trades = merged.get('Trades')
print(f"\nTrades Count: {len(trades)}")

portfolio = reconstructor.reconstruct(trades, fin_info)

print("\n--- Reconstructed Portfolio Keys ---")
keys = list(portfolio.keys())
print(keys)

if 'EVO' in keys:
    print("SUCCESS: EVO found in keys")
elif 'EVOs' in keys:
    print("FAILURE: EVOs found in keys (Normalization failed)")
else:
    print("FAILURE: EVO/EVOs not found in keys")
