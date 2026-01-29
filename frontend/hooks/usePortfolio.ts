"use client";

import { useState, useMemo } from "react";
import useSWR from "swr";
import { PortfolioData, Position } from "../app/types";
import { Simulation } from "../components/dashboard/SimulationPanel";

const fetcher = (url: string) => fetch(url).then((res) => res.json());

export function usePortfolio() {
    const { data, error, isLoading, mutate } = useSWR<PortfolioData & { status?: string }>(
        "http://localhost:8000/api/portfolio",
        fetcher,
        { refreshInterval: 60000 }
    );

    const [simulations, setSimulations] = useState<Simulation[]>([]);

    // 1. Base Stats
    const netLiqUsd = data?.kpi?.net_liquidity_usd || 1;
    const positions = data?.positions || [];
    const currentMarketValUsd = positions.reduce((acc, p) => acc + (p.market_value_usd || 0), 0);

    // Use backend-calculated leverage (Gross Position / Net Liq, IBKR style)
    const grossPositionUsd = data?.kpi?.gross_position_usd || currentMarketValUsd;
    const currentLeverage = data?.kpi?.leverage || (grossPositionUsd / netLiqUsd);

    // 2. Simulation Logic
    const simMarketValUsd = simulations.reduce((acc, s) => acc + (s.price * s.quantity), 0);
    const simCostUsd = simMarketValUsd; // Assuming pure buy

    // Cash Impact
    const currentCashUsd = data?.kpi.cash_balance_usd || 0;
    const projectedCashUsd = currentCashUsd - simCostUsd;

    // FX Rates (fx_rates has keys like "USD", "EUR", etc.)
    const usdCzkRate = data?.fx_rates?.["USD"] || 20.3;
    const eurCzkRate = data?.fx_rates?.["EUR"] || 24.5;

    // Net Liq - use backend CZK value directly for accuracy
    const netLiqCzk = data?.kpi?.net_liquidity_czk || (netLiqUsd * usdCzkRate);
    const projectedNetLiqUsd = netLiqUsd;
    // For simulations, we add/subtract in CZK
    const simMarketValCzk = simulations.reduce((acc, s) => {
        const rate = s.currency === "USD" ? usdCzkRate : (s.currency === "EUR" ? eurCzkRate : 1);
        return acc + (s.price * s.quantity * rate);
    }, 0);
    const projectedNetLiqCzk = netLiqCzk; // Net Liq unchanged for pure purchase

    // Projected values for simulations
    // Simulations are assumed to be long positions, so they add to both net and gross
    const projectedGrossPositionUsd = grossPositionUsd + simMarketValUsd;
    const projectedLeverage = projectedGrossPositionUsd / projectedNetLiqUsd;
    const projectedPctInvested = ((currentMarketValUsd + simMarketValUsd) / projectedNetLiqUsd) * 100;

    // 3. Merged Positions Calculation
    const mergedPositions = useMemo(() => {
        if (!data) return [];

        // Start with a map of existing positions
        const mergedMap = new Map<string, Position>();
        positions.forEach(p => {
            mergedMap.set(p.symbol, { ...p });
        });

        // Apply simulations
        simulations.forEach(s => {
            const mvNative = s.price * s.quantity;
            const rate = s.currency === "USD" ? usdCzkRate : (s.currency === "EUR" ? 25 : 1);
            const mvUsd = s.currency === "USD" ? mvNative : mvNative / usdCzkRate;
            const mvCzk = mvNative * rate;

            if (mergedMap.has(s.symbol)) {
                // Merge with existing
                const existing = mergedMap.get(s.symbol)!;
                existing.quantity += s.quantity;
                existing.market_value_native += mvNative;
                existing.market_value_usd += mvUsd;
                existing.market_value_czk += mvCzk;
                existing.cost_basis_czk += mvCzk; // Treat sim price as entry cost
                existing.name = (existing.name || existing.symbol) + " (+Sim)";
                existing.is_simulated = true;
            } else {
                // New ghost position
                mergedMap.set(s.symbol, {
                    symbol: s.symbol,
                    name: (s.name || s.symbol) + " (Sim)",
                    currency: s.currency,
                    quantity: s.quantity,
                    current_price: s.price,
                    market_value_native: mvNative,
                    market_value_usd: mvUsd,
                    market_value_czk: mvCzk,
                    pct_portfolio: 0,
                    cost_basis_czk: mvCzk,
                    unrealized_pnl_czk: 0,
                    instruction: "Hold",
                    is_excluded: false,
                    is_simulated: true,
                });
            }
        });

        const all = Array.from(mergedMap.values());

        return all.map(p => ({
            ...p,
            pct_portfolio: projectedNetLiqCzk > 0 ? (p.market_value_czk / projectedNetLiqCzk) * 100 : 0
        })).sort((a, b) => b.market_value_czk - a.market_value_czk);

    }, [data, positions, simulations, usdCzkRate, eurCzkRate, projectedNetLiqCzk]);

    const addSimulation = (sim: Simulation) => setSimulations(prev => [...prev, sim]);
    const removeSimulation = (id: string) => setSimulations(prev => prev.filter(s => s.id !== id));

    // Total portfolio value (all positions including simulations)
    const projectedMarketValCzk = mergedPositions.reduce((acc, p) => acc + (p.market_value_czk || 0), 0);

    return {
        data,
        error,
        isLoading,
        mutate,
        simulations,
        addSimulation,
        removeSimulation,
        mergedPositions,
        currentLeverage,
        projectedLeverage,
        projectedPctInvested,
        projectedCashUsd,
        projectedNetLiqUsd,
        projectedNetLiqCzk,
        projectedMarketValCzk,
        usdCzkRate,
        positionsCount: positions.length
    };
}
