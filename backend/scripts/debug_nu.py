
import sys
import os
import pandas as pd
from app.services.parser import IBKRParser
from app.services.reconstructor import PortfolioReconstructor

# Setup paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

def debug_nu():
    print(f"Loading data from {DATA_DIR}...")
    parser = IBKRParser()
    reconstructor = PortfolioReconstructor()
    
    # Load CSVs
    dfs = []
    if os.path.exists(DATA_DIR):
        for f in os.listdir(DATA_DIR):
            if f.endswith(".csv"):
                try:
                    df = parser.parse_csv(os.path.join(DATA_DIR, f))
                    dfs.append(df)
                    print(f"Loaded {f}")
                except Exception as e:
                    print(f"Error loading {f}: {e}")
    
    if not dfs:
        print("No CSVs found.")
        return

    # Merge Trades
    trades = []
    for df in dfs:
        if 'Trades' in df:
            trades.append(df['Trades'])
    
    if not trades:
        print("No trades found.")
        return
        
    all_trades = pd.concat(trades, ignore_index=True)
    all_trades['Date/Time'] = pd.to_datetime(all_trades['Date/Time'])
    all_trades = all_trades.sort_values('Date/Time')
    
    print("\n--- NU Transaction History ---")
    print(f"{'Date':<12} {'Qty':<10} {'Price (USD)':<12} {'FX':<8} {'Fees (USD)':<10} {'Native Val':<12} {'CZK Cost':<12}")
    
    total_qty = 0
    total_cost_czk = 0
    
    for _, row in all_trades.iterrows():
        symbol = row.get('Symbol', '')
        if symbol != 'NU': continue
        
        qty = float(row.get('Quantity', 0))
        price = float(row.get('T. Price', 0))
        date = row['Date/Time']
        date_str = date.strftime("%Y-%m-%d")
        
        # Get FX from Reconstructor's service
        fx = reconstructor.forex.get_rate('USD', date_str, 'CZK')
        
        # Extract Fee
        comm_col_fee = next((c for c in all_trades.columns if 'Comm/Fee' in c or 'Fee' in c), None)
        comm_col_usd = next((c for c in all_trades.columns if 'Comm in USD' in c), None)
        fee = 0.0
        if comm_col_fee:
             try: fee += abs(float(row.get(comm_col_fee, 0)))
             except: pass
        if comm_col_usd and fee == 0:
             try: fee += abs(float(row.get(comm_col_usd, 0)))
             except: pass

        native_val = qty * price
        
        # Cost Basis Logic mimicking Reconstructor
        if qty > 0:
            czk_cost = (native_val + fee) * fx
            total_cost_czk += czk_cost
            total_qty += qty
        else:
            # Sell logic
            # Simplistic for debug print, strictly for last 2 buys verification check manually
            # But let's print the line cost
            czk_cost = (native_val) * fx # Sell proceeds
            
            # Reduce total cost basis proportionally
            sell_qty = abs(qty)
            if total_qty > 0:
                 fraction = sell_qty / total_qty
                 cost_removed = total_cost_czk * fraction
                 total_cost_czk -= cost_removed
                 total_qty -= sell_qty
        
        print(f"{date_str:<12} {qty:<10} {price:<12.2f} {fx:<8.2f} {fee:<10.2f} {native_val:<12.2f} {czk_cost:<12.2f}")
        
    print("-" * 80)
    if total_qty > 0:
        avg_price_czk = total_cost_czk / total_qty
        print(f"Total Qty: {total_qty}")
        print(f"Total Cost Basis (CZK): {total_cost_czk:,.2f}")
        print(f"Avg Price (CZK implied): {avg_price_czk:.2f}")

if __name__ == "__main__":
    debug_nu()
