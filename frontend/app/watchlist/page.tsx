"use client";

import { useEffect, useState, useRef } from "react";
import useSWR from "swr";
import { WatchlistCard } from "@/components/watchlist/WatchlistCard";
import { ChartModal } from "@/components/watchlist/ChartModal";
import { LucidePlus, LucideSearch } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";

// Helper fetcher
const fetcher = (url: string) => fetch(url).then((res) => res.json());

interface WatchlistData {
    symbol: string;
    price: number;
    currency: string;
    change_percent: number;
    history: any[]; // Defined in Card
    error?: string;
    loading?: boolean;
}

export default function WatchlistPage() {
    // 1. Get List of Symbols
    const { data: watchlistSymbols, mutate: mutateList } = useSWR<string[]>(
        "http://localhost:8000/api/watchlist",
        fetcher
    );

    // 2. State for Card Data
    const [marketData, setMarketData] = useState<Record<string, WatchlistData>>({});
    const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
    const [newSymbol, setNewSymbol] = useState("");
    const [timeRange, setTimeRange] = useState("1m");
    const eventSourceRef = useRef<EventSource | null>(null);

    // 3. Effect: Initialize State & Start Stream
    useEffect(() => {
        if (!watchlistSymbols) return;

        // A. Init Skeletons for missing data
        // ... (keep logic to not wipe data if already exists, unless range changed? 
        // actually if range changes we probably want to show loading or just update in place)

        const initialState: Record<string, WatchlistData> = { ...marketData };
        // If range changed, we might want to mark as loading? 
        // For simplicity, we just keep current data and let it update

        let needsFetch = false;
        watchlistSymbols.forEach(sym => {
            if (!initialState[sym]) {
                initialState[sym] = { symbol: sym, price: 0, currency: '', change_percent: 0, history: [], loading: true };
                needsFetch = true;
            }
        });
        setMarketData(initialState);

        // B. Start SSE Stream
        if (eventSourceRef.current) eventSourceRef.current.close();

        const es = new EventSource(`http://localhost:8000/api/watchlist/stream?range=${timeRange}`);
        eventSourceRef.current = es;

        es.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                setMarketData(prev => ({
                    ...prev,
                    [data.symbol]: { ...data, loading: false }
                }));
            } catch (e) {
                console.error("Parse error", e);
            }
        };

        es.addEventListener("DONE", () => {
            es.close();
        });

        es.onerror = () => {
            es.close();
        };

        return () => {
            if (eventSourceRef.current) eventSourceRef.current.close();
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [watchlistSymbols, timeRange]); // Re-run when list OR range changes

    // 4. Actions
    const handleAdd = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newSymbol) return;

        try {
            await axios.post("http://localhost:8000/api/watchlist", { symbol: newSymbol });
            setNewSymbol("");
            mutateList();
            toast.success(`Added ${newSymbol}`);
        } catch (e) {
            toast.error("Failed to add symbol");
        }
    };

    const handleRemove = async (symbol: string) => {
        try {
            await axios.delete(`http://localhost:8000/api/watchlist/${symbol}`);
            const newData = { ...marketData };
            delete newData[symbol];
            setMarketData(newData);
            mutateList();
            toast.success(`Removed ${symbol}`);
        } catch (e) {
            toast.error("Failed to remove symbol");
        }
    };

    const RANGES = ["1d", "1w", "1m", "3m", "1y"];

    return (
        <div className="max-w-7xl mx-auto p-8 space-y-8">
            {/* Header */}
            <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-white">Watchlist</h1>
                    <p className="text-zinc-500 text-sm">Market Overview & Trends</p>
                </div>

                <div className="flex items-center gap-4">
                    {/* Timeframe Selector */}
                    <div className="flex bg-zinc-900 border border-zinc-800 rounded-lg p-1 gap-1">
                        {RANGES.map((r) => (
                            <button
                                key={r}
                                onClick={() => setTimeRange(r)}
                                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${timeRange === r
                                        ? "bg-indigo-600 text-white shadow-sm"
                                        : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800"
                                    }`}
                            >
                                {r.toUpperCase()}
                            </button>
                        ))}
                    </div>

                    <form onSubmit={handleAdd} className="flex items-center space-x-2">
                        <div className="relative">
                            <LucideSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" size={16} />
                            <input
                                type="text"
                                value={newSymbol}
                                onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
                                placeholder="Add Ticker..."
                                className="pl-9 pr-4 py-1.5 bg-zinc-900 border border-zinc-800 rounded-lg text-white placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 w-48 text-sm"
                            />
                        </div>
                        <button
                            type="submit"
                            disabled={!newSymbol}
                            className="p-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <LucidePlus size={20} />
                        </button>
                    </form>
                </div>
            </header>

            {/* Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {Object.values(marketData).map((stock) => (
                    <WatchlistCard
                        key={stock.symbol}
                        data={stock}
                        onRemove={handleRemove}
                        onSelect={setSelectedSymbol}
                    />
                ))}

                {(!watchlistSymbols || watchlistSymbols.length === 0) && (
                    <div className="col-span-full h-64 border-2 border-dashed border-zinc-800 rounded-xl flex flex-col items-center justify-center text-zinc-500 gap-2">
                        <LucideSearch size={32} className="opacity-50" />
                        <p>Your watchlist is empty. Add a symbol to get started.</p>
                    </div>
                )}
            </div>

            {selectedSymbol && (
                <ChartModal
                    symbol={selectedSymbol}
                    onClose={() => setSelectedSymbol(null)}
                />
            )}
        </div>
    );
}
