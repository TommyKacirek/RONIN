#!/usr/bin/env python3
"""
Analyze price discrepancy with IBKR
"""
import requests

try:
    response = requests.get('http://localhost:8000/api/portfolio')
    data = response.json()
    
    kpi = data['kpi']
    positions = data['positions']
    
    print("\n" + "="*70)
    print("IBKR COMPARISON ANALYSIS")
    print("="*70)
    
    print(f"\nApp Net Liquidity: ${kpi['net_liquidity_usd']:,.2f}")
    print("IBKR Net Liquidity: $________ (fill in what you see)")
    
    print(f"\n{'='*70}")
    print("POTENTIAL DISCREPANCY SOURCES:")
    print("="*70)
    
    # 1. Check for option positions
    options = [p for p in positions if 'Option' in p.get('description', '')]
    if options:
        total_options_value = sum(p['market_value_czk'] for p in options)
        print(f"\n1. OPTIONS POSITIONS:")
        print(f"   Count: {len(options)}")
        print(f"   Total Value: {total_options_value:,.0f} Kč")
        for opt in options:
            print(f"   - {opt['symbol']}: {opt['market_value_czk']:,.0f} Kč")
        print(f"   ⚠️  Options prices can vary significantly between sources")
    
    # 2. Cash balance
    cash_usd = kpi.get('cash_balance_usd', 0)
    print(f"\n2. CASH BALANCE:")
    print(f"   App: ${cash_usd:,.2f}")
    print(f"   IBKR: $________ (check if it matches)")
    
    # 3. FX Rate impact
    print(f"\n3. FX RATE (USD/CZK):")
    print(f"   App uses: 20.291 (CNB daily)")
    print(f"   IBKR uses: _______ (check your IBKR screen)")
    
    # Calculate impact of 1% FX difference
    stock_val_czk = kpi['total_market_czk']
    fx_impact_1pct = (stock_val_czk * 0.01) / 20.291
    print(f"   Impact of 0.1% FX diff: ~${fx_impact_1pct:,.0f}")
    
    # 4. Accruals
    print(f"\n4. ACCRUED INTEREST/DIVIDENDS:")
    print(f"   App includes: Yes (from CSV 'Accruals' section)")
    print(f"   IBKR shows: _______ (check if IBKR includes pending dividends)")
    
    # 5. Top positions by value
    print(f"\n5. TOP 5 POSITIONS (biggest FX/price impact):")
    sorted_pos = sorted(positions, key=lambda p: abs(p['market_value_czk']), reverse=True)[:5]
    for i, pos in enumerate(sorted_pos, 1):
        price = pos.get('current_price', 0)
        qty = pos.get('quantity', 0)
        val_czk = pos['market_value_czk']
        val_usd = val_czk / 20.291
        print(f"   {i}. {pos['symbol']}: {qty:.0f} @ ${price:.2f} = ${val_usd:,.0f}")
    
    print(f"\n{'='*70}")
    print("RECOMMENDATION:")
    print("="*70)
    print("""
1. Check if IBKR Net Liq includes 'Accrued Interest' - toggle it off if yes
2. Compare the USD/CZK rate between IBKR and app (20.291)
3. Options prices can vary ±5-10% between data sources
4. If still >$1k diff, check individual stock prices for EUR/GBP stocks
""")
    print("="*70 + "\n")
    
except Exception as e:
    print(f"Error: {e}")
