
import os
import sys
sys.path.append(os.getcwd())
import pandas as pd
from backend.app.services.parser import IBKRParser

data_dir = "backend/data"
found_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith('.csv')]
parser = IBKRParser()

for f in found_files:
    print(f"File: {f}")
    data = parser.parse_csv(f)
    
    # Check Open Positions
    pos = data.get('Open Positions', pd.DataFrame())
    if not pos.empty:
        print("\nOpen Positions Symbols and Categories:")
        for _, row in pos.iterrows():
            print(f" Symbol: '{row.get('Symbol')}', Category: '{row.get('Asset Category')}', Qty: {row.get('Quantity')}, MktVal: {row.get('Market Value')}")
            
    # Check Forex Balances
    fx = data.get('Forex Balances', pd.DataFrame())
    if not fx.empty:
        print("\nForex Balances:")
        for _, row in fx.iterrows():
             print(f" Cat: '{row.get('Asset Category')}', Desc: '{row.get('Description')}', Qty: {row.get('Quantity')}, MktVal: {row.get('Market Value')}")

    # Check Net Liquidation from Statement
    # Often in 'Change in Net Asset Value' or 'Net Asset Value'
    nav = data.get('Net Asset Value', pd.DataFrame())
    if not nav.empty:
        print("\nNet Asset Value Section (might have actual Net Liq):")
        print(nav.head(20).to_string())

    print("-" * 20)
