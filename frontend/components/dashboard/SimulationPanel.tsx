"use client";

import { useState } from "react";
import axios from "axios";
import { LucidePlus, LucideLoader2, LucideX } from "lucide-react";
import { toast } from "sonner";

export interface Simulation {
    id: string;
    symbol: string;
    quantity: number;
    price: number;
    currency: string;
    name?: string;
}

interface SimulationPanelProps {
    simulations: Simulation[];
    onAdd: (sim: Simulation) => void;
    onRemove: (id: string) => void;
    netLiqUsd: number;
    fxRates: Record<string, number> | undefined;
}

export function SimulationPanel({ simulations, onAdd, onRemove, netLiqUsd, fxRates }: SimulationPanelProps) {
    const [symbol, setSymbol] = useState("");
    const [qty, setQty] = useState("");
    const [price, setPrice] = useState("");
    const [alloc, setAlloc] = useState("");
    const [currency, setCurrency] = useState("USD");
    const [loading, setLoading] = useState(false);

    const getFxConversion = (targetCurr: string) => {
        if (!fxRates) return 1;
        const rateUsd = fxRates["USD"] || 20.3;
        const rateTarget = fxRates[targetCurr] || rateUsd; // Default to USD rate if missing
        // Convert USD to Target: (AmountUSD * RateUSD) / RateTarget
        // Factor to multiply USD by to get Target Currency:
        return rateUsd / rateTarget;
    };

    const handleFetchPrice = async () => {
        if (!symbol) return;
        setLoading(true);
        try {
            const res = await axios.get(`http://localhost:8000/api/quote?symbol=${symbol.toUpperCase()}`);
            if (res.data.found) {
                setPrice(res.data.price);
                const curr = res.data.currency || "USD";
                setCurrency(curr);

                // Auto-recalculate if we have allocation set
                if (alloc && netLiqUsd) {
                    recalcQtyFromAlloc(alloc, res.data.price, curr);
                }
            } else {
                toast.error("Symbol not found");
            }
        } catch (e) {
            toast.error("Error fetching quote");
        } finally {
            setLoading(false);
        }
    };

    const recalcQtyFromAlloc = (allocVal: string, priceVal: string | number, curr: string) => {
        const pct = parseFloat(allocVal);
        const priceNum = Number(priceVal);
        if (!isNaN(pct) && !isNaN(priceNum) && priceNum > 0 && netLiqUsd > 0) {
            const amountUsd = netLiqUsd * (pct / 100);
            const conversion = getFxConversion(curr); // Multiplier to go from USD -> Target
            const amountNative = amountUsd * conversion;
            const newQty = Math.floor(amountNative / priceNum); // Integer shares
            setQty(newQty.toString());
        }
    };

    const handleAllocChange = (val: string) => {
        setAlloc(val);
        recalcQtyFromAlloc(val, price, currency);
    };

    const handleQtyChange = (val: string) => {
        setQty(val);
        const q = parseFloat(val);
        const p = parseFloat(price);
        if (!isNaN(q) && !isNaN(p) && netLiqUsd > 0) {
            const conversion = getFxConversion(currency); // USD -> Target
            // ValueNative = q * p
            // ValueUSD = ValueNative / conversion
            const valNative = q * p;
            const valUsd = valNative / conversion;
            const pct = (valUsd / netLiqUsd) * 100;
            setAlloc(pct.toFixed(2));
        } else {
            setAlloc("");
        }
    };

    const handleAdd = () => {
        if (!symbol || !qty || !price) return;
        onAdd({
            id: Math.random().toString(36).substring(7),
            symbol: symbol.toUpperCase(),
            quantity: parseFloat(qty),
            price: parseFloat(price),
            currency: currency,
            name: "Simulation"
        });
        setSymbol("");
        setQty("");
        setPrice("");
        setAlloc("");
        setCurrency("USD");
    };

    return (
        <div className="p-4 bg-zinc-900/50 border border-zinc-800 rounded-xl space-y-4">
            <div className="flex justify-between items-center">
                <h3 className="text-sm font-medium text-zinc-400">Trade Simulator</h3>
                {simulations.length > 0 && (
                    <div className="flex gap-2 flex-wrap">
                        {simulations.map(sim => (
                            <div key={sim.id} className="flex items-center gap-2 px-2 py-1 bg-blue-500/10 border border-blue-500/20 rounded text-xs text-blue-400">
                                <span className="font-bold">{sim.symbol}</span>
                                <span>{sim.quantity}x @ {sim.price} {sim.currency}</span>
                                <button
                                    onClick={() => onRemove(sim.id)}
                                    className="hover:text-blue-200"
                                >
                                    <LucideX size={12} />
                                </button>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            <div className="flex gap-2 items-end">
                <div className="space-y-1">
                    <label className="text-xs text-zinc-500">Ticker</label>
                    <input
                        className="w-20 bg-zinc-950 border border-zinc-800 rounded px-2 py-1.5 text-sm uppercase placeholder:text-zinc-700 focus:border-blue-500 focus:outline-none"
                        placeholder="AAPL"
                        value={symbol}
                        onChange={(e) => setSymbol(e.target.value)}
                        onBlur={handleFetchPrice}
                    />
                </div>

                <div className="space-y-1">
                    <label className="text-xs text-zinc-500">Price <span className="text-zinc-600">({currency})</span></label>
                    <div className="relative">
                        <input
                            type="number"
                            className="w-24 bg-zinc-950 border border-zinc-800 rounded px-2 py-1.5 text-sm focus:border-blue-500 focus:outline-none pr-7"
                            placeholder="0.00"
                            value={price}
                            onChange={(e) => {
                                setPrice(e.target.value);
                                if (alloc) recalcQtyFromAlloc(alloc, e.target.value, currency);
                                else if (qty) handleQtyChange(qty); // Recalc alloc if price changes and qty exists
                            }}
                        />
                        {loading && <LucideLoader2 className="absolute right-2 top-2 animate-spin text-zinc-500" size={14} />}
                    </div>
                </div>

                <div className="space-y-1">
                    <label className="text-xs text-zinc-500">Qty</label>
                    <input
                        type="number"
                        className="w-20 bg-zinc-950 border border-zinc-800 rounded px-2 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
                        placeholder="100"
                        value={qty}
                        onChange={(e) => handleQtyChange(e.target.value)}
                    />
                </div>

                <div className="space-y-1">
                    <label className="text-xs text-zinc-500">% Alloc</label>
                    <div className="relative">
                        <input
                            type="number"
                            className="w-16 bg-zinc-950 border border-zinc-800 rounded px-2 py-1.5 text-sm focus:border-blue-500 focus:outline-none text-right pr-6"
                            placeholder="5.0"
                            value={alloc}
                            onChange={(e) => handleAllocChange(e.target.value)}
                        />
                        <span className="absolute right-2 top-1.5 text-zinc-500 text-sm">%</span>
                    </div>
                </div>

                <button
                    onClick={handleAdd}
                    className="h-[34px] px-3 bg-blue-600 hover:bg-blue-700 text-white rounded flex items-center gap-1 text-sm font-medium transition-colors mb-[1px]"
                >
                    <LucidePlus size={16} /> Add
                </button>
            </div>

            <div className="text-[10px] text-zinc-600 flex justify-between px-1">
                <span>Net Liq: ${netLiqUsd?.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                {alloc && <span>Target: ${(netLiqUsd * (parseFloat(alloc) / 100)).toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>}
            </div>
        </div>
    );
}
