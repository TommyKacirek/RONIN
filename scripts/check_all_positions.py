import requests
import json

try:
    r = requests.get("http://localhost:8000/api/portfolio")
    data = r.json()
    positions = data.get('positions', [])
    
    print(f"Total Positions: {len(positions)}")
    print(f"Net Liquidity USD: {data['kpi']['net_liquidity_usd']}")
    print(f"Net Liquidity CZK: {data['kpi']['net_liquidity_czk']}")
    print("-" * 60)
    print(f"{'SYMBOL':<10} {'QTY':<10} {'PRICE':<10} {'VAL (CZK)':<15} {'SOURCE':<10}")
    print("-" * 60)
    
    sorted_pos = sorted(positions, key=lambda x: x['market_value_czk'], reverse=True)
    
    total_val = 0
    for p in sorted_pos:
        sym = p.get('symbol', 'UNKNOWN')
        qty = p.get('quantity')
        price = p.get('current_price')
        val = p.get('market_value_czk')
        total_val += val
        src = p.get('price_source')
        excl = " [EXCLUDED]" if p.get('is_excluded') else ""
        
        print(f"{sym:<10} {qty:<10} {price:<10.2f} {val:<15.0f} {src:<10}{excl}")
        
    print("-" * 60)
    print(f"Total Market Value (Sum): {total_val:,.0f} CZK")

except Exception as e:
    print(f"Error: {e}")
