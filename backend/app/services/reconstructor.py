from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime
from .forex import ForexService

class PortfolioReconstructor:
    def __init__(self):
        self.forex = ForexService()

    def _parse_float(self, val: Any) -> float:
        """Safely parses a float from string, handling commas."""
        if pd.isna(val): import math; return 0.0
        if isinstance(val, (int, float)): return float(val)
        if isinstance(val, str):
            clean = val.replace(',', '').strip()
            try:
                return float(clean)
            except:
                return 0.0
        return 0.0

    def reconstruct(self, trades_df: pd.DataFrame, fin_info_df: Optional[pd.DataFrame] = None) -> Dict[str, Dict[str, Any]]:
        """
        Replays trades to calculate the current portfolio state with precise Cost Basis in CZK.
        
        Args:
            trades_df: DataFrame of Trades.
            fin_info_df: DataFrame of Financial Instrument Information (Symbol, Description, etc.) for normalization.
        
        Returns: { 'SYMBOL': { 'quantity': 100, 'cost_basis_czk': 50000.0, 'currency': 'SEK' } }
        """
        portfolio = {} # Symbol -> { qty, cost_basis_czk, avg_price_czk }
        
        # 1. Build Symbol Map (Normalization)
        # IBKR often uses 'EVOs' in Trades but 'EVO' in OpenPositions.
        # Financial Instrument Info usually has "Symbol, Description, Conid..."
        # We need to map Trade Symbol -> Standard Symbol (if possible) or just verify.
        # Actually, best heuristic:
        # If 'Financial Instrument Information' exists, parsing the first column which often looks like "EVOs, EVO"
        # Let's inspect the `fin_info_df` format based on previous grep:
        # "EVOs, EVO",EVOLUTION AB,366244347,...
        # The first column seems to contain aliases? Or is it "Symbol" and "Local Symbol"?
        
        symbol_map = {}
        if fin_info_df is not None and not fin_info_df.empty:
            # Find 'Symbol' column (it might be named 'Symbol' or similar)
            symbol_col = next((c for c in fin_info_df.columns if 'Symbol' in c), None)
            
            if symbol_col:
                for _, row in fin_info_df.iterrows():
                    val = str(row[symbol_col])
                    if ',' in val:
                        parts = [p.strip() for p in val.split(',')]
                        # Map all parts to the LAST part (Canonical)
                        # e.g. "EVOs, EVO" -> canonical="EVO"
                        canonical = parts[-1]
                        for p in parts:
                            symbol_map[p] = canonical
            
            # Manual Overrides for specific issues
            if 'ZALd' in symbol_map or 'ZAL' in symbol_map:
                 symbol_map['ZALd'] = 'ZAL'
                 symbol_map['ZAL'] = 'ZAL'
        
        # 2. Sort Trades
        if 'Date/Time' not in trades_df.columns:
            return {}
            
        trades_df['Date/Time'] = pd.to_datetime(trades_df['Date/Time'])
        trades_df = trades_df.sort_values('Date/Time')
        
        # Detect Commission Columns
        # We might have 'Comm in USD' OR 'Comm/Fee' depending on the batch header
        comm_col_usd = next((c for c in trades_df.columns if 'Comm in USD' in c), None)
        comm_col_fee = next((c for c in trades_df.columns if 'Comm/Fee' in c or 'Fee' in c), None)
        
        for _, row in trades_df.iterrows():
            if row.get('DataDiscriminator') != 'Order':
                continue
                
            raw_symbol = row.get('Symbol')
            # Normalize Symbol
            symbol = symbol_map.get(raw_symbol, raw_symbol)
            
            qty = self._parse_float(row.get('Quantity', 0))
            price = self._parse_float(row.get('T. Price', 0)) 
            currency = row.get('Currency', 'USD')
            date_obj = row.get('Date/Time')
            
            if not pkgy_val(qty, price): continue
            
            date_str = date_obj.strftime("%Y-%m-%d")
            fx_rate = self.forex.get_rate(currency, date_str, "CZK")
            
            # Extract Commission (Fee)
            # Check both columns. Usually mutually exclusive or one is NaN.
            fee_native = 0.0
            
            # Try 'Comm/Fee' first (generic)
            if comm_col_fee:
                try:
                    val = self._parse_float(row.get(comm_col_fee, 0))
                    if not pd.isna(val):
                        fee_native += abs(val)
                except: pass
                
            # Try 'Comm in USD' (if above was 0 or missing, or additive? usually mutually exclusive)
            # If we already found fee in comm_col_fee, we assume that's it.
            # But let's be safe and max? or sum?
            # Creating a robust check:
            if comm_col_usd and fee_native == 0.0:
                 try:
                    val = self._parse_float(row.get(comm_col_usd, 0))
                    if not pd.isna(val):
                        fee_native += abs(val)
                 except: pass
            
            if symbol not in portfolio:
                portfolio[symbol] = {'quantity': 0.0, 'cost_basis_czk': 0.0, 'currency': currency}
            
            pos = portfolio[symbol]
            current_qty = pos['quantity']
            current_basis = pos['cost_basis_czk']
            
            # BUY
            if qty > 0:
                # Cost Basis = (Price * Qty) + Fee
                trade_val_native = qty * price
                trade_cost_czk = (trade_val_native + fee_native) * fx_rate
                
                pos['quantity'] += qty
                pos['cost_basis_czk'] += trade_cost_czk
            
            # SELL
            elif qty < 0:
                # Selling reduces cost basis proportionally to the quantity sold.
                # Fees on Sell reduce Realized P&L, but do NOT affect the cost basis of the REMAINING shares.
                sell_qty_abs = abs(qty)
                if current_qty > 0:
                    fraction = sell_qty_abs / current_qty
                    if fraction > 1.0: fraction = 1.0 
                    
                    cost_removed = current_basis * fraction
                    
                    pos['quantity'] -= sell_qty_abs
                    pos['cost_basis_czk'] -= cost_removed
                else:
                    pos['quantity'] += qty 
            
            if abs(pos['quantity']) < 0.0001:
                pos['quantity'] = 0
                pos['cost_basis_czk'] = 0
        
        active_portfolio = {k: v for k, v in portfolio.items() if abs(v['quantity']) > 0}
        return active_portfolio

def pkgy_val(qty, price):
    # Allow price 0? Maybe for asset transfers? Safe to ignore for cost basis calculation if 0?
    # If price is 0, cost is 0. Safe.
    return abs(qty) > 0 and price >= 0

if __name__ == "__main__":
    pass
