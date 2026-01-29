import os
import pandas as pd
from backend.app.services.parser import IBKRParser
from backend.app.services.merger import DataMerger

parser = IBKRParser()
merger = DataMerger()

data_dir = "backend/data"
files = sorted([os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith(".csv")])
print(f"Files: {files}")

parsed_data = [parser.parse_csv(f) for f in files]
merged = merger.merge(parsed_data)

trades = merged.get('Trades')

# 1. Check Available Sections
print("\n=== Available Sections ===")
print(merged.keys())

# 2. Check Report Date in Statement or Account Info
print("\n=== Report Metadata ===")
stmt = merged.get('Statement')
acc_info = merged.get('Account Information')

if stmt is not None and not stmt.empty:
    print("--- Statement Section ---")
    print(stmt.head().to_string())

if acc_info is not None and not acc_info.empty:
    print("\n--- Account Information Section ---")
    print(acc_info.head().to_string())
    
# 3. Check Trade Date Range

# 3. Compare with Open Positions
print("\n=== Open Positions (IBKR Snapshot) ===")
open_pos = merged.get('Open Positions')
if open_pos is not None:
    # Check NU
    nu_pos = open_pos[open_pos['Symbol'] == 'NU']
    if not nu_pos.empty:
        print("NU Position:")
        print(nu_pos[['Symbol', 'Quantity', 'Cost Basis', 'Close Price']].to_string())
    else:
        print("NU not found in Open Positions")
        
    # Check EVO (normalize check handled implicitly by eye, but look for EVO)
    evo_pos = open_pos[open_pos['Symbol'].str.contains('EVO', na=False)]
    if not evo_pos.empty:
        print("EVO Position:")
        print(evo_pos[['Symbol', 'Quantity', 'Cost Basis', 'Close Price']].to_string())
    else:
        print("EVO not found in Open Positions")

# Check NU Trades including Sells and Columns
print("\n=== NU Trades (All) ===")
if trades is not None:
    print("Trades Columns:", list(trades.columns))
    nu_trades = trades[trades['Symbol'] == 'NU']
    cols_to_show = ['Date/Time', 'Quantity', 'T. Price']
    # Add fee columns if exist
    for c in ['Comm/Fee', 'Comm in USD']:
        if c in trades.columns:
            cols_to_show.append(c)
            
    if not nu_trades.empty:
        print(nu_trades[cols_to_show].to_string())
        print(f"\nTotal NU Quantity in Trades: {nu_trades['Quantity'].sum()}")
    else:
        print("No NU Trades found")
