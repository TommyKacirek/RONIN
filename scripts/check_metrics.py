#!/usr/bin/env python3
"""
Quick check of portfolio metrics to verify values
"""
import requests
import json

try:
    response = requests.get('http://localhost:8000/api/portfolio')
    data = response.json()
    
    kpi = data.get('kpi', {})
    
    print("\n" + "="*60)
    print("PORTFOLIO METRICS CHECK")
    print("="*60)
    
    # Net Liquidity
    net_liq_czk = kpi.get('net_liquidity_czk', 0)
    net_liq_usd = kpi.get('net_liquidity_usd', 0)
    print(f"\n💰 Net Liquidity:")
    print(f"   CZK: {net_liq_czk:,.2f} Kč")
    print(f"   USD: ${net_liq_usd:,.2f}")
    print(f"   USD (rounded k): ${round(net_liq_usd / 1000)}k")
    
    # Stock Value
    stock_val_czk = kpi.get('total_market_czk', 0)
    stock_val_usd = stock_val_czk / 20.291  # Current USD/CZK rate
    print(f"\n📊 Stock Value:")
    print(f"   CZK: {stock_val_czk:,.2f} Kč")
    print(f"   USD (est): ${stock_val_usd:,.2f}")
    print(f"   USD (rounded k): ${round(stock_val_usd / 1000)}k")
    
    # Cost Basis
    total_pnl_czk = kpi.get('total_pnl_czk', 0)
    cost_basis_czk = stock_val_czk - total_pnl_czk
    cost_basis_usd = cost_basis_czk / 20.291
    print(f"\n🐖 Cost Basis:")
    print(f"   CZK: {cost_basis_czk:,.2f} Kč")
    print(f"   USD (est): ${cost_basis_usd:,.2f}")
    print(f"   USD (rounded k): ${round(cost_basis_usd / 1000)}k")
    
    # P&L
    print(f"\n📈 Total P&L:")
    print(f"   CZK: {total_pnl_czk:,.0f} Kč")
    pnl_pct = (total_pnl_czk / cost_basis_czk * 100) if cost_basis_czk != 0 else 0
    print(f"   %: {pnl_pct:+.2f}%")
    
    # FX Rate Check
    print(f"\n💱 FX Rate Used:")
    print(f"   USD/CZK: 20.291 (CNB)")
    
    print("\n" + "="*60)
    print("FRONTEND FORMATTING TEST:")
    print("="*60)
    
    # Simulate frontend formatting
    def formatCurrency(value, decimals=0):
        return f"{value:,.{decimals}f}"
    
    print(f"\nNet Liquidity USD:")
    print(f"  Raw: ${net_liq_usd}")
    print(f"  /1000: {net_liq_usd / 1000}")
    print(f"  Math.round(/1000): {round(net_liq_usd / 1000)}")
    print(f"  Formatted: ${formatCurrency(round(net_liq_usd / 1000), 0)}k USD")
    
    print("\n" + "="*60 + "\n")
    
except Exception as e:
    print(f"Error: {e}")
