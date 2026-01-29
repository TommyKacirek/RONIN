#!/usr/bin/env python3
"""
Corrected IBKR comparison - app is LOWER
"""
import requests

try:
    response = requests.get('http://localhost:8000/api/portfolio')
    data = response.json()
    
    kpi = data['kpi']
    positions = data['positions']
    
    print("\n" + "="*70)
    print("CORRECTED IBKR COMPARISON")
    print("="*70)
    
    # Corrected values
    ibkr_net_liq = 189434.64
    app_net_liq = kpi['net_liquidity_usd']
    difference = app_net_liq - ibkr_net_liq
    
    print(f"\n📊 Net Liquidity:")
    print(f"   IBKR:       ${ibkr_net_liq:,.2f}")
    print(f"   App:        ${app_net_liq:,.2f}")
    print(f"   Difference: ${difference:+,.2f} ({difference/ibkr_net_liq*100:+.2f}%)")
    print(f"\n   ⚠️  App shows LESS than IBKR by ${abs(difference):,.2f}")
    
    # Cash - need to check from screenshot
    print(f"\n💵 Cash Balance:")
    print(f"   App: ${kpi['cash_balance_usd']:,.2f}")
    print(f"   (Need IBKR cash value from screenshot to compare)")
    
    print(f"\n{'='*70}")
    print("POSSIBLE CAUSES (App LOWER than IBKR):")
    print("="*70)
    
    # 1. Yahoo prices might be stale/delayed
    print(f"\n1. YAHOO FINANCE DELAY:")
    print(f"   Yahoo free tier has 15-min delay")
    print(f"   App cache: 5 minutes")
    print(f"   → Stocks could have risen since last Yahoo update")
    
    # 2. Options pricing
    options = [p for p in positions if 'Option' in p.get('description', '')]
    if options:
        total_opt_val = sum(p['market_value_czk'] for p in options)
        total_opt_usd = total_opt_val / 20.291
        print(f"\n2. OPTIONS PRICING:")
        print(f"   Total options value: ${abs(total_opt_usd):,.0f}")
        for opt in options:
            val = opt['market_value_czk'] / 20.291
            print(f"   - {opt['symbol']}: ${val:+,.0f}")
        print(f"   → IBKR uses 'Mark' (mid), Yahoo uses 'Last' (can differ)")
    
    # 3. FX Rate - if app is lower, maybe CNB rate is too high?
    stock_val_czk = kpi['total_market_czk']
    app_stock_val_usd = stock_val_czk / 20.291
    
    print(f"\n3. FX RATE IMPACT:")
    print(f"   Stock value: {stock_val_czk:,.0f} Kč")
    print(f"   App uses: 20.291 USD/CZK → ${app_stock_val_usd:,.0f}")
    
    # What rate would make them equal?
    # Assuming cash is same, stock value diff = net liq diff
    if abs(difference) > 100:
        implied_stock_diff = difference  # Simplified
        required_fx = stock_val_czk / (app_stock_val_usd - implied_stock_diff)
        print(f"   To match IBKR would need: {required_fx:.4f} USD/CZK")
        print(f"   Difference: {20.291 - required_fx:+.4f} ({(20.291 - required_fx)/required_fx*100:+.2f}%)")
    
    # 4. Individual stock prices
    print(f"\n4. INDIVIDUAL STOCK PRICES:")
    print(f"   Top 5 positions - check if Yahoo prices match IBKR:")
    sorted_pos = sorted(positions, key=lambda p: abs(p['market_value_czk']), reverse=True)[:5]
    for i, pos in enumerate(sorted_pos, 1):
        price = pos.get('current_price', 0)
        qty = pos.get('quantity', 0)
        symbol = pos['symbol']
        print(f"   {i}. {symbol}: {qty:.0f} @ ${price:.2f}")
        print(f"      → Compare with IBKR screenshot")
    
    # 5. Accruals
    print(f"\n5. ACCRUALS/DIVIDENDS:")
    print(f"   Check IBKR if 'Accrued Interest' is included")
    print(f"   App includes accruals from CSV")
    
    print(f"\n{'='*70}")
    print("RECOMMENDATION:")
    print("="*70)
    print(f"""
The -$1,050 difference (0.55%) could be:

a) **Yahoo delay** - Stock prices up since last update
   → Wait 5 min for cache refresh, check if gap closes

b) **FX Rate** - CNB vs IBKR rate differs by ~0.5%
   → Compare USD/CZK rate in IBKR settings

c) **Options pricing** - Different bid/ask/mark prices
   → Check SPY option price in both platforms

d) **Individual stocks** - Compare top positions:
   NU, WIZZ, PYPL, EEFT, ZAL prices in both platforms

**Next steps:**
1. Refresh app in 5 min, see if gap changes
2. Check IBKR's USD/CZK rate
3. Compare NU and WIZZ prices specifically
""")
    print("="*70 + "\n")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
