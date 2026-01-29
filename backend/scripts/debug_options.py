import pandas as pd
import asyncio
import os
from app.services.engine import PortfolioEngine
from app.services.parser import IBKRParser
from app.services.merger import DataMerger
from app.services.store import StoreService

async def debug_options_detail():
    parser = IBKRParser()
    merger = DataMerger()
    engine = PortfolioEngine()
    store = StoreService()
    
    data_dir = "data"
    csv_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith('.csv')]
    parsed_data = [parser.parse_csv(f) for f in csv_files]
    merged = merger.merge(parsed_data)
    metadata = store.load()
    result = await engine.process(merged, metadata)
    
    print("=== ALL OPTIONS IN POSITIONS ===")
    options_found = []
    for p in result['positions']:
        sym = p['symbol']
        # Check if option-like symbol
        if 'P' in sym or 'C' in sym or 'Option' in p.get('region', ''):
            options_found.append(p)
            print(f"  {sym}: MV_USD={p['market_value_usd']:.2f}, Qty={p['quantity']}, Excluded={p['is_excluded']}, Region={p.get('region')}")
    
    if not options_found:
        print("  No options found in positions!")
    
    print("\n=== OPEN POSITIONS (Options Category) ===")
    df = merged.get('Open Positions', pd.DataFrame())
    if not df.empty:
        for _, row in df.iterrows():
            if 'Option' in str(row.get('Asset Category', '')):
                print(f"  {row.get('Symbol')}: Qty={row.get('Quantity')}, Value={row.get('Value')}")

if __name__ == "__main__":
    asyncio.run(debug_options_detail())
