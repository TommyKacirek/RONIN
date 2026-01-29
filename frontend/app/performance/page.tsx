"use client";

import { usePortfolio } from "@/hooks/usePortfolio";
import useSWR from "swr";
import { PerformanceData, Trade, Interest } from "../types";
import { useState, useMemo } from "react";
import Link from "next/link";
import { LucideArrowLeft, LucideCalendar, LucideTrendingUp, LucideWallet, LucidePieChart } from "lucide-react";

const fetcher = (url: string) => fetch(url).then((res) => res.json());

export default function PerformancePage() {
    const { data: portfolioData } = usePortfolio();
    const { data: perfData, isLoading } = useSWR<PerformanceData>(
        "http://localhost:8000/api/performance",
        fetcher
    );

    const [viewCurrency, setViewCurrency] = useState<'USD' | 'CZK'>('CZK');

    // FX Rates helper
    const rates = portfolioData?.fx_rates || {};
    const usdCzk = rates["USD"] || 20.3; // Fallback

    const getRateToCzk = (currency: string) => {
        if (currency === "CZK") return 1;
        if (currency === "USD") return usdCzk;
        return rates[currency] || usdCzk; // Fallback to USD rate if unknown or assume 1? Safer to use USD
    };

    const convert = (amount: number, currency: string) => {
        const rate = getRateToCzk(currency);
        const valCzk = amount * rate;
        if (viewCurrency === 'CZK') return valCzk;
        return valCzk / usdCzk; // Back to USD
    };

    const formatMoney = (val: number) => {
        return val.toLocaleString(undefined, {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
            style: 'currency',
            currency: viewCurrency
        });
    };

    // Helper to calculate risk basis
    const getRiskBasis = (t: Trade) => {
        const optionMatch = t.symbol.match(/^([A-Z0-9]+)\s+(\d{2}[A-Z]{3}\d{2})\s+([\d\.]+)\s+([PC])/);
        if (optionMatch) {
            const strike = parseFloat(optionMatch[3]);
            return strike * 100 * Math.abs(t.quantity);
        }
        return t.basis ? Math.abs(t.basis) : 0;
    };

    // Goals Calculation (Current Year)
    const currentYear = new Date().getFullYear();
    const goalsMetrics = useMemo(() => {
        if (!perfData) return { totalRoi: 0, avgMonthly: 0, monthsPassed: 1 };

        const currentYearTrades = perfData.trades.filter(t => new Date(t.date).getFullYear() === currentYear);

        // Sum of percentages
        const totalRoi = currentYearTrades.reduce((acc, t) => {
            const risk = getRiskBasis(t);
            if (!risk || risk === 0 || t.realized_pnl === 0) return acc;

            const roi = (t.realized_pnl / risk) * 100;
            return acc + roi;
        }, 0);

        // Calculate months passed
        const now = new Date();
        const startOfYear = new Date(currentYear, 0, 1);
        const diffTime = Math.abs(now.getTime() - startOfYear.getTime());
        const daysPassed = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        const exactMonths = (daysPassed / 365.25) * 12;

        return {
            totalRoi,
            avgMonthly: exactMonths > 0 ? totalRoi / exactMonths : 0,
            monthsPassed: exactMonths
        };
    }, [perfData, currentYear]);

    // Aggregate Data by Month
    const monthlyStats = useMemo(() => {
        if (!perfData) return [];

        const stats: Record<string, {
            month: string,
            year: number,
            sortKey: number,
            interest: number,
            pnl: number,
            net: number
        }> = {};

        // Process Trades
        perfData.trades.forEach(t => {
            const date = new Date(t.date);
            const key = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}`;

            if (!stats[key]) {
                const monthName = date.toLocaleString('cs-CZ', { month: 'long' });
                stats[key] = {
                    month: monthName.charAt(0).toUpperCase() + monthName.slice(1),
                    year: date.getFullYear(),
                    sortKey: date.getFullYear() * 100 + date.getMonth(),
                    interest: 0,
                    pnl: 0,
                    net: 0
                };
            }

            // Realized PnL is usually net of commission in IBKR reports?
            // CSV has "Realized P/L" and "Comm/Fee".
            // Usually Realized P/L is net. 
            // Let's assume Realized P/L is the gain.
            // Convert to Target Currency
            stats[key].pnl += convert(t.realized_pnl, t.currency);
        });

        // Process Interest
        perfData.interest.forEach(i => {
            const date = new Date(i.date);
            const key = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}`;

            // Interest creates stats entry if not exists?
            // Usually trades happen too. But if only interest:
            if (!stats[key]) {
                const monthName = date.toLocaleString('cs-CZ', { month: 'long' });
                stats[key] = {
                    month: monthName.charAt(0).toUpperCase() + monthName.slice(1),
                    year: date.getFullYear(),
                    sortKey: date.getFullYear() * 100 + date.getMonth(),
                    interest: 0,
                    pnl: 0,
                    net: 0
                };
            }

            stats[key].interest += convert(i.amount, i.currency);
        });

        // Calculate Net
        Object.values(stats).forEach(s => {
            s.net = s.pnl + s.interest; // Interest is negative
        });

        return Object.values(stats).sort((a, b) => b.sortKey - a.sortKey);
    }, [perfData, viewCurrency, usdCzk, rates]);

    // Group by Year for display
    const byYear = useMemo(() => {
        const groups: Record<number, typeof monthlyStats> = {};
        monthlyStats.forEach(s => {
            if (!groups[s.year]) groups[s.year] = [];
            groups[s.year].push(s);
        });
        return groups;
    }, [monthlyStats]);

    if (isLoading) return <div className="min-h-screen bg-black text-white flex items-center justify-center">Loading Performance...</div>;

    return (
        <div className="min-h-screen bg-black text-white font-sans selection:bg-zinc-800 p-8 space-y-8">
            {/* Header */}
            <header className="flex justify-between items-center">
                <div className="flex items-center gap-4">
                    <Link href="/" className="p-2 bg-zinc-900 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors">
                        <LucideArrowLeft size={20} />
                    </Link>
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight">Performance Report</h1>
                        <p className="text-zinc-500 text-sm">Realized P&L & Interest History</p>
                    </div>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={() => setViewCurrency(c => c === 'USD' ? 'CZK' : 'USD')}
                        className="px-4 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-sm font-medium hover:bg-zinc-800 transition-colors"
                    >
                        Display: {viewCurrency}
                    </button>
                </div>
            </header>

            {/* Goals Widget */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="bg-zinc-900/50 border border-zinc-800 p-6 rounded-xl">
                    <div className="text-zinc-500 text-xs font-medium uppercase">YTD ROI Sum</div>
                    <div className={`text-3xl font-bold mt-2 ${goalsMetrics.totalRoi >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                        {goalsMetrics.totalRoi.toFixed(2)}%
                    </div>
                    <div className="text-zinc-600 text-xs mt-1">Sum of trade %</div>
                </div>
                <div className="bg-zinc-900/50 border border-zinc-800 p-6 rounded-xl">
                    <div className="text-zinc-500 text-xs font-medium uppercase">Avg Monthly ROI</div>
                    <div className={`text-3xl font-bold mt-2 ${goalsMetrics.avgMonthly >= 25 ? "text-emerald-400" : goalsMetrics.avgMonthly > 0 ? "text-yellow-400" : "text-rose-400"}`}>
                        {goalsMetrics.avgMonthly.toFixed(2)}%
                    </div>
                    <div className="text-zinc-600 text-xs mt-1">Target: 25.00%</div>
                </div>
                <div className="bg-zinc-900/50 border border-zinc-800 p-6 rounded-xl flex flex-col justify-center">
                    <div className="text-zinc-500 text-xs font-medium uppercase mb-2">Year Progress</div>
                    <div className="w-full bg-zinc-800 rounded-full h-3">
                        <div
                            className="h-3 rounded-full bg-indigo-500"
                            style={{ width: `${(goalsMetrics.monthsPassed / 12) * 100}%` }}
                        ></div>
                    </div>
                    <div className="text-right text-xs text-zinc-500 mt-2">
                        {((goalsMetrics.monthsPassed / 12) * 100).toFixed(1)}% of {currentYear}
                    </div>
                </div>
                <div className="bg-zinc-900/50 border border-zinc-800 p-6 rounded-xl flex flex-col justify-center">
                    <div className="text-zinc-500 text-xs font-medium uppercase mb-2">Goal Progress</div>
                    <div className="w-full bg-zinc-800 rounded-full h-3">
                        <div
                            className={`h-3 rounded-full ${goalsMetrics.avgMonthly >= 25 ? "bg-emerald-500" : "bg-blue-500"}`}
                            style={{ width: `${Math.min((goalsMetrics.avgMonthly / 25) * 100, 100)}%` }}
                        ></div>
                    </div>
                    <div className="text-right text-xs text-zinc-500 mt-2">
                        {((goalsMetrics.avgMonthly / 25) * 100).toFixed(0)}% of Target
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left Column: Monthly Stats */}
                <div className="lg:col-span-1 space-y-8">
                    {Object.keys(byYear).sort((a, b) => Number(b) - Number(a)).map(year => {
                        const stats = byYear[Number(year)];
                        const totalInterest = stats.reduce((acc, s) => acc + s.interest, 0);
                        const totalPnl = stats.reduce((acc, s) => acc + s.pnl, 0);
                        const totalNet = totalPnl + totalInterest;

                        return (
                            <div key={year} className="space-y-4">
                                <h3 className="text-xl font-bold text-indigo-400">{year} Summary</h3>
                                <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl overflow-hidden">
                                    <table className="w-full text-sm">
                                        <thead className="bg-zinc-900 text-xs text-zinc-500 font-medium">
                                            <tr>
                                                <th className="px-4 py-3 text-left">Month</th>
                                                <th className="px-4 py-3 text-right">Interest</th>
                                                <th className="px-4 py-3 text-right">Realized</th>
                                                <th className="px-4 py-3 text-right">Net</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-zinc-800">
                                            {stats.map(s => (
                                                <tr key={s.sortKey} className="hover:bg-zinc-800/50">
                                                    <td className="px-4 py-3 text-zinc-300">{s.month}</td>
                                                    <td className="px-4 py-3 text-right text-rose-400">{formatMoney(s.interest)}</td>
                                                    <td className={`px-4 py-3 text-right ${s.pnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                                                        {formatMoney(s.pnl)}
                                                    </td>
                                                    <td className={`px-4 py-3 text-right font-medium ${s.net >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                                                        {formatMoney(s.net)}
                                                    </td>
                                                </tr>
                                            ))}
                                            <tr className="bg-indigo-500/10 font-bold border-t-2 border-zinc-800">
                                                <td className="px-4 py-3 text-indigo-200">TOTAL</td>
                                                <td className="px-4 py-3 text-right text-rose-400">{formatMoney(totalInterest)}</td>
                                                <td className="px-4 py-3 text-right text-emerald-400">{formatMoney(totalPnl)}</td>
                                                <td className={`px-4 py-3 text-right ${totalNet >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                                                    {formatMoney(totalNet)}
                                                </td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        );
                    })}
                </div>

                {/* Right Column: Trade Log */}
                <div className="lg:col-span-2 space-y-4">
                    <h3 className="text-xl font-bold text-zinc-200">Trade Journal</h3>
                    <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl overflow-hidden">
                        <div className="max-h-[800px] overflow-y-auto">
                            <table className="w-full text-sm">
                                <thead className="bg-zinc-900 text-xs text-zinc-500 font-medium sticky top-0">
                                    <tr>
                                        <th className="px-4 py-3 text-left">Date</th>
                                        <th className="px-4 py-3 text-left">Ticker</th>
                                        <th className="px-4 py-3 text-right">Qty</th>
                                        <th className="px-4 py-3 text-right">Price</th>
                                        <th className="px-4 py-3 text-right">Basis</th>
                                        <th className="px-4 py-3 text-right">ROI %</th>
                                        <th className="px-4 py-3 text-right">P&L (Native)</th>
                                        <th className="px-4 py-3 text-right">P&L ({viewCurrency})</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-zinc-800">
                                    {perfData?.trades.map((t, i) => {
                                        const risk = getRiskBasis(t);
                                        const roi = risk ? (t.realized_pnl / risk) * 100 : 0;
                                        return (
                                            <tr key={i} className="hover:bg-zinc-800/50">
                                                <td className="px-4 py-3 text-zinc-400 font-mono text-xs">{t.date}</td>
                                                <td className="px-4 py-3 font-medium">
                                                    <span className={t.quantity > 0 ? "text-emerald-400" : "text-rose-400"}>
                                                        {t.quantity > 0 ? "BUY" : "SELL"}
                                                    </span>{" "}
                                                    <span className="text-white ml-2">{t.symbol}</span>
                                                </td>
                                                <td className="px-4 py-3 text-right text-zinc-300">{Math.abs(t.quantity)}</td>
                                                <td className="px-4 py-3 text-right text-zinc-300">
                                                    {t.price} {t.currency}
                                                </td>
                                                <td className="px-4 py-3 text-right text-zinc-500 text-xs">
                                                    {risk ? risk.toFixed(0) : '-'}
                                                </td>
                                                <td className={`px-4 py-3 text-right font-medium ${roi >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                                                    {roi.toFixed(1)}%
                                                </td>
                                                <td className={`px-4 py-3 text-right ${t.realized_pnl >= 0 ? "text-emerald-400" : "text-rose-400"} opacity-70`}>
                                                    {t.realized_pnl !== 0 ? `${t.realized_pnl > 0 ? '+' : ''}${t.realized_pnl.toFixed(2)}` : '-'}
                                                </td>
                                                <td className={`px-4 py-3 text-right font-medium ${t.realized_pnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                                                    {t.realized_pnl !== 0 ? formatMoney(convert(t.realized_pnl, t.currency)) : '-'}
                                                </td>
                                            </tr>
                                        )
                                    })}
                                    {perfData?.trades.length === 0 && (
                                        <tr>
                                            <td colSpan={6} className="px-4 py-8 text-center text-zinc-500">
                                                No closed trades found in loaded reports.
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
