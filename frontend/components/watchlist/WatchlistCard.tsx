"use client";

import { useMemo } from "react";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { LucideX, LucideTrendingUp, LucideTrendingDown } from "lucide-react";

interface HistoryPoint {
    date: string;
    close: number;
}

interface WatchlistData {
    symbol: string;
    price: number;
    currency: string;
    change_percent: number;
    history: HistoryPoint[];
    error?: string;
    loading?: boolean;
}

interface WatchlistCardProps {
    data: WatchlistData;
    onRemove: (symbol: string) => void;
    onSelect: (symbol: string) => void;
}

export function WatchlistCard({ data, onRemove, onSelect }: WatchlistCardProps) {
    const isPositive = (data.change_percent ?? 0) >= 0;
    const color = isPositive ? "#22c55e" : "#ef4444"; // green-500 : red-500

    if (data.loading) {
        return (
            <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6 h-[300px] animate-pulse relative">
                <div className="h-6 w-24 bg-zinc-800 rounded mb-4" />
                <div className="h-8 w-32 bg-zinc-800 rounded" />
                <div className="absolute top-4 right-4 h-8 w-8 bg-zinc-800 rounded-lg" />
                <div className="mt-8 h-32 w-full bg-zinc-800/50 rounded" />
            </div>
        );
    }


    if (data.error) {
        return (
            <div className="bg-zinc-900/30 border border-red-900/50 rounded-xl p-6 h-[300px] flex flex-col relative group">
                <button
                    onClick={(e) => {
                        e.stopPropagation();
                        onRemove(data.symbol);
                    }}
                    className="absolute top-4 right-4 p-2 text-zinc-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                >
                    <LucideX size={18} />
                </button>
                <div className="flex-1 flex flex-col items-center justify-center text-center">
                    <span className="text-xl font-bold text-zinc-400 mb-2">{data.symbol}</span>
                    <span className="text-red-400 text-sm bg-red-950/30 px-3 py-1 rounded-full border border-red-900/30">
                        {data.error}
                    </span>
                </div>
            </div>
        );
    }

    return (
        <div
            onClick={() => onSelect(data.symbol)}
            className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6 h-[300px] flex flex-col relative group overflow-hidden hover:border-zinc-700 transition-colors cursor-pointer"
        >
            {/* Header */}
            <div className="flex justify-between items-start mb-6 relative z-10">
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <h3 className="text-xl font-bold text-white tracking-tight">{data.symbol}</h3>
                        <span className="text-xs font-medium text-zinc-500 px-2 py-0.5 bg-zinc-800 rounded-full">
                            {data.currency}
                        </span>
                    </div>
                    <div className="flex items-baseline gap-3">
                        <span className="text-3xl font-bold text-zinc-100">
                            {(data.price ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </span>
                        <div className={`flex items-center text-sm font-medium ${isPositive ? 'text-green-500' : 'text-red-500'}`}>
                            {isPositive ? <LucideTrendingUp size={14} className="mr-1" /> : <LucideTrendingDown size={14} className="mr-1" />}
                            {isPositive ? "+" : ""}{(data.change_percent ?? 0).toFixed(2)}%
                        </div>
                    </div>
                </div>

                <button
                    onClick={(e) => {
                        e.stopPropagation();
                        onRemove(data.symbol);
                    }}
                    className="p-2 text-zinc-500 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                >
                    <LucideX size={18} />
                </button>
            </div>

            {/* Chart */}
            <div className="flex-1 w-[120%] -ml-[10%] -mb-4">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={data.history}>
                        <defs>
                            <linearGradient id={`gradient-${data.symbol}`} x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor={color} stopOpacity={0.3} />
                                <stop offset="95%" stopColor={color} stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <YAxis domain={['auto', 'auto']} hide />
                        <Area
                            type="monotone"
                            dataKey="close"
                            stroke={color}
                            strokeWidth={2}
                            fill={`url(#gradient-${data.symbol})`}
                        />
                        {/* Minimal Tooltip? Maybe, or keep it clean for dashboard look */}
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
