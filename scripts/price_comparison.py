#!/usr/bin/env python3
"""
Compare specific stock prices from IBKR screenshot
"""
import requests

# Prices from IBKR screenshot
ibkr_prices = {
    'NU': 18.65,
    'WIZZ': 14.06,  # From screenshot
    'PYPL': 52.87,
    'EEFT': 72.06,
    'ZAL': 24.49,
    'TUI1': 8.96,
    'SOFI': 17.18,
    'TTD': 78.46,
    'KBR': 78.95,
    'WIX': 89.17,
    'JD': 26.62,
    'BYDDY': 19.08,
    'GRAB': 4.13,
    'DIDI': 3.82,
    'C3AI': 56.81,
    # 'SPY PUT': 17.23,  # Option
}

try:
    response = requests.get('http://localhost:8000/api/portfolio')
    data = response.json()
    positions = data['positions']
    
    print("\n" + "="*80)
    print("STOCK PRICE COMPARISON: IBKR vs Yahoo Finance (App)")
    print("="*80)
    
    total_diff_usd = 0
    
    print(f"\n{'Symbol':<10} {'Qty':>8} {'IBKR $':>10} {'Yahoo $':>10} {'Diff $':>10} {'Impact $':>12}")
    print("-" * 80)
    
    for pos in positions:
        symbol = pos['symbol']
        if symbol in ibkr_prices:
            qty = pos['quantity']
            yahoo_price = pos.get('current_price', 0)
            ibkr_price = ibkr_prices[symbol]
            diff = yahoo_price - ibkr_price
            impact = diff * qty
            total_diff_usd += impact
            
            color = "✅" if abs(diff) < 0.10 else "⚠️ "
            print(f"{symbol:<10} {qty:>8.0f} {ibkr_price:>10.2f} {yahoo_price:>10.2f} {diff:>+10.2f} {impact:>+12.2f} {color}")
    
    print("-" * 80)
    print(f"{'TOTAL IMPACT':<10} {'':<8} {'':<10} {'':<10} {'':<10} {total_diff_usd:>+12.2f}")
    
    print(f"\n{'='*80}")
    print("SUMMARY:")
    print("="*80)
    
    print(f"\nNet Liquidity Difference: -$1,219.05 (App lower than IBKR)")
    print(f"Stock price impact:       ${total_diff_usd:+,.2f}")
    
    remaining = -1219.05 - total_diff_usd
    print(f"Remaining unexplained:    ${remaining:+,.2f}")
    
    if abs(remaining) < 200:
        print("\n✅ Stock price differences explain most of the gap!")
        print("   Remaining ~$" + f"{abs(remaining):.0f}" + " is likely FX rate + options pricing")
    else:
        print(f"\n⚠️  Still ${abs(remaining):,.0f} unexplained")
        print("   Likely causes:")
        print("   - FX rate differences (0.6% = ~$1,200 impact)")
        print("   - Options pricing (SPY PUT)")
        print("   - Cash balance differences")
    
    print("\n" + "="*80 + "\n")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
