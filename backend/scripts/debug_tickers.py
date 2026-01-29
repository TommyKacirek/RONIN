
import sys
import os
import pandas as pd
# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.parser import IBKRParser
from app.services.engine import PortfolioEngine

def inspect_ticker(ticker_symbol):
    print(f"--- Inspecting {ticker_symbol} ---")
    
    # 1. Parse Raw CSVs
    data_dir = "data"
    parser = IBKRParser()
    frames = []
    
    for f in os.listdir(data_dir):
        if f.endswith(".csv"):
            fpath = os.path.join(data_dir, f)
            print(f"Parsing {f}...")
            try:
                df = parser.parse_csv(fpath)
                if 'Open Positions' in df:
                    op = df['Open Positions']
                    # Filter for ticker
                    # IBKR symbols might be 'BOSS', 'BOSS GY', etc.
                    mask = op['Symbol'].str.contains(ticker_symbol, case=False, na=False)
                    matches = op[mask]
                    if not matches.empty:
                        print(f"Found in {f}:")
                        print(matches[['Symbol', 'Quantity', 'Cost Basis', 'Cost Price', 'Value', 'Currency']].to_string())
                        frames.append(matches)
            except Exception as e:
                print(f"Error parsing {f}: {e}")

# 2. Pipeline Processing
print("\n--- Pipeline Processing ---")
parser = IBKRParser()
from app.services.merger import DataMerger
merger = DataMerger()
from app.services.store import StoreService
store = StoreService()
engine = PortfolioEngine()

import asyncio

async def run_pipeline():
    print("1. Parsing CSVs...")
    data_dir = "data"
    parsed_data = []
    
    found_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith('.csv')]
    for fpath in found_files:
        try:
             parsed_data.append(parser.parse_csv(fpath))
        except Exception as e:
             print(f"Error parsing {fpath}: {e}")

    print("2. Merging Data...")
    merged = merger.merge(parsed_data)
    
    print("3. Loading Metadata...")
    metadata = {} # Simple empty dict or store.load() if available
    # store needs proper path init, let's try strict basics
    try: metadata = store.load()
    except: pass
    
    print("4. Running Engine Process...")
    try:
        res = await engine.process(merged, metadata)
        print("Engine finished.")
        
        # Filter result
        for p in res.get('positions', []):
            if 'P911' in p['symbol'] or 'BOSS' in p['symbol']:
                 print(f"Result Check {p['symbol']}: CostBasis={p.get('cost_basis_czk')} Val={p.get('market_value_czk')} PnL={p.get('pnl_percent')}")
    except Exception as e:
        print(f"Engine crashed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_pipeline())
