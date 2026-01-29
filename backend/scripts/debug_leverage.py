import pandas as pd
import asyncio
import os
from app.services.engine import PortfolioEngine
from app.services.parser import IBKRParser
from app.services.merger import DataMerger
from app.services.store import StoreService

async def debug_leverage():
    parser = IBKRParser()
    merger = DataMerger()
    engine = PortfolioEngine()
    store = StoreService()
    
    data_dir = "data"
    csv_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith('.csv')]
    
    parsed_data = [parser.parse_csv(f) for f in csv_files]
    merged = merger.merge(parsed_data)
    metadata = store.load()
    
    # 1. Run Engine Process
    result = await engine.process(merged, metadata)
    
    kpi = result['kpi']
    print(f"--- APP CALCULATION ---")
    print(f"Net Liquidity USD:     {kpi['net_liquidity_usd']:.2f}")
    print(f"Gross Position USD:    {kpi.get('gross_position_usd', 0):.2f}")
    print(f"Cash Balance USD:      {kpi['cash_balance_usd']:.2f}")
    print(f"Leverage (NEW):        {kpi.get('leverage', 0):.4f}x")
    
    # Old calculation for comparison
    market = sum(p['market_value_usd'] for p in result['positions'])
    nav = kpi['net_liquidity_usd']
    old_leverage = market / nav if nav != 0 else 0
    print(f"Leverage (OLD):        {old_leverage:.4f}x")
    print(f"Invested %:            {kpi.get('pct_invested', 0):.2f}%")
    
    # 2. Extract IBKR NAV Section for Comparison
    if 'Net Asset Value' in merged:
        print(f"\n--- IBKR NAV SECTION ---")
        nav_df = merged['Net Asset Value']
        # Columns: Asset Class, Prior Total, Current Long, Current Short, Current Total, Change
        # We want Current Total
        for _, row in nav_df.iterrows():
            asset = str(row.get('Asset Class')).strip()
            val = row.get('Current Total')
            if asset in ['Cash', 'Stock', 'Options', 'Interest Accruals', 'Dividend Accruals', 'Total']:
                print(f"{asset}: {val}")

if __name__ == "__main__":
    asyncio.run(debug_leverage())
