import pandas as pd
from backend.app.services.parser import IBKRParser
from backend.app.services.merger import DataMerger
from backend.app.services.forex import ForexService
import os
from datetime import datetime

# Setup Services
parser = IBKRParser()
merger = DataMerger()
forex = ForexService()

# Load Data
data_dir = "backend/data"
files = sorted([os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith(".csv")])
parsed_data = [parser.parse_csv(f) for f in files]
merged = merger.merge(parsed_data)
trades = merged.get('Trades')

if trades is None or trades.empty:
    print("No Trades found!")
    exit()

trades['Date/Time'] = pd.to_datetime(trades['Date/Time'])
trades = trades.sort_values('Date/Time')

# 1. Verify Scope: List all unique symbols found
unique_symbols = trades[trades['DataDiscriminator'] == 'Order']['Symbol'].unique()
print(f"\n=== Found {len(unique_symbols)} Unique Symbols in Trades ===")
print(sorted(unique_symbols))

# 2. Verify Forex Rates for specific samples
print("\n=== Verifying FX Rates ===")
# Pick a few distinct currencies and dates
samples = [
    {'Symbol': 'NU', 'Currency': 'USD'},
    {'Symbol': 'EVOs', 'Currency': 'SEK'}, # Check normalized or raw
    {'Symbol': 'ZAL', 'Currency': 'EUR'},
    {'Symbol': 'WIZZ', 'Currency': 'GBP'}
]

for sample in samples:
    sym = sample['Symbol']
    curr = sample['Currency']
    
    # Get first BUY trade for this symbol
    mask = (trades['Symbol'] == sym) & (trades['Quantity'].astype(float) > 0)
    subset = trades[mask]
    
    if not subset.empty:
        row = subset.iloc[0]
        date_obj = row['Date/Time']
        date_str = date_obj.strftime("%Y-%m-%d")
        
        # Fetch Rate
        rate = forex.get_rate(curr, date_str, "CZK")
        
        print(f"Trade: {sym} on {date_str} in {curr}")
        print(f"  -> FX Rate Used ({curr}->CZK): {rate}")
        print(f"  -> Validation: 1 {curr} = {rate} CZK")
    else:
        print(f"No Buy trades found for {sym}")
