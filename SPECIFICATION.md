# RONIN - Technical Specification

This document details the core logic and calculation methodologies.

## 1. Options Module Calculations
The options journal calculates metrics to evaluate the "Wheel" strategy or generic premium selling.

- **RoR (Return on Risk):** `Premium / Strike Price`. Note: This is an approximation of capital allocation efficiency.
- **Annualized Return (p.a.):** `(Premium / Strike) * (365 / Days To Expiration) * 100`.
- **Downside Protection:** `(Current Price - Break Even) / Current Price`, where `Break Even = Strike - Premium`.
- **Put Exposure:** `Sum(Strike * 100)` for all `OPEN` Put contracts.

## 2. Global Exposure & Country Detection
Positions are grouped by Region and Country using a multi-step detection pipeline:
1. **ISIN Prefix:** High confidence (e.g., `US...` -> US, `DE...` -> Germany).
2. **Symbol Suffix:** Market specific (e.g., `.DE` -> Germany, `.L` -> UK).
3. **Live Metadata:** Fetched from Yahoo Finance 'country' field.
4. **Currency Fallback:** Last resort (e.g., `CZK` -> Czechia, `GBP` -> UK).

**Filtering:** "Derivatives" are excluded from the main Market Exposure pie charts to prevent skewed equity weights.

## 3. Shadow Ledger (PnL Accuracy)
To ensure reliable P&L:
- **Trade Replay:** Replays all buy/sell orders.
- **FX Conversion:** Every transaction is converted to CZK using the FX rate **on that specific trade date**.
- **Average Cost Basis:** Calculated as a weighted average in CZK.
- **Current P&L:** `(Quantity * Live Price * Current FX Rate) - (Shadow Cost Basis CZK)`.

## 4. Live FX Rates
The system fetches live FX rates from Yahoo Finance for display purposes:
- Pairs: `USDCZK=X`, `EURCZK=X`, `GBPCZK=X`, etc.
- This ensures the "Net Liquidity" in CZK reflects the most recent market conditions.

## 5. Margin & Interest
- **Margin Interest:** Calculated daily based on the benchmark rate + spread (Tiered logic applied for balances over $100k).
- **Leverage Limit:** Projected leverage over **1.5x** triggers visual warnings in the UI.
