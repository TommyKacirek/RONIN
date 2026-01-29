import requests
import json

try:
    r = requests.get("http://localhost:8000/api/portfolio")
    data = r.json()
    positions = data.get('positions', [])
    
    targets = ['TTD', 'DIDIY', 'DIDI', 'TENCENT']
    found = []
    
    print(f"Total Positions: {len(positions)}")
    print("-" * 50)
    
    for p in positions:
        sym = p.get('symbol', 'UNKNOWN')
        if any(t in sym.upper() for t in targets):
            found.append(p)
            print(f"FOUND: {sym}")
            print(f"  Qty: {p.get('quantity')}")
            print(f"  Price: {p.get('current_price')} (Source: {p.get('price_source')})")
            print(f"  Mkt Val CZK: {p.get('market_value_czk')}")
            print(f"  Excluded: {p.get('is_excluded')}")
            print("-" * 20)
            
    if not found:
        print("ALERT: TTD or DIDIY not found in positions list!")
        # Print all symbols to see what IS there
        print("All Symbols:", [p.get('symbol') for p in positions])

except Exception as e:
    print(f"Error: {e}")
