"use client";

import { useState, useEffect } from "react";
import useSWR from "swr";
import { DetailChart, Measurement } from "./DetailChart";
import { LucideX, LucideLoader2, LucideRuler } from "lucide-react";
import { MeasurementPanel } from "./MeasurementPanel";

interface ChartModalProps {
    symbol: string;
    onClose: () => void;
}

const fetcher = (url: string) => fetch(url).then((res) => res.json());

const RANGES = ["1d", "1w", "1m", "3m", "6m", "1y", "5y", "max"];

import axios from "axios";

export function ChartModal({ symbol, onClose }: ChartModalProps) {
    const [mounted, setMounted] = useState(false);
    const [range, setRange] = useState("1y");
    const [isMeasuring, setIsMeasuring] = useState(false);
    const [measurements, setMeasurements] = useState<Measurement[]>([]);
    const [selectedId, setSelectedId] = useState<string | null>(null);
    const [dataLoaded, setDataLoaded] = useState(false);

    const { data, isLoading } = useSWR(
        `http://localhost:8000/api/market-data/${symbol}/ohlcv?range=${range}`,
        fetcher
    );

    const { data: metadata } = useSWR(
        `http://localhost:8000/api/metadata/${symbol}`,
        fetcher
    );

    // Initial Load from Metadata
    useEffect(() => {
        setMounted(true);
        if (metadata && !dataLoaded) {
            if (metadata.measurements) {
                setMeasurements(metadata.measurements);
            }
            setDataLoaded(true);
        }
    }, [metadata, dataLoaded]);

    // Save on Change (Debounced)
    useEffect(() => {
        if (!dataLoaded) return;

        const timer = setTimeout(() => {
            axios.post("http://localhost:8000/api/metadata", {
                symbol,
                measurements
            }).catch(e => console.error("Failed to save measurements", e));
        }, 1000);

        return () => clearTimeout(timer);
    }, [measurements, symbol, dataLoaded]);

    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key.toLowerCase() === 'm') {
                setIsMeasuring(prev => !prev);
            }
            if (e.key === 'Escape') {
                if (isMeasuring) setIsMeasuring(false);
                else onClose();
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isMeasuring, onClose]);

    const handleDownloadCsv = () => {
        if (measurements.length === 0) return;

        const headers = "ID,Symbol,Start Time,Start Price,End Time,End Price,Note\n";
        const rows = measurements.map(m => {
            return `${m.id},${symbol},${m.start.time},${m.start.price},${m.end.time},${m.end.price},"${m.note || ''}"`;
        }).join("\n");

        const blob = new Blob([headers + rows], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `measurements_${symbol}_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
    };

    const handleAddMeasure = (m: Measurement) => {
        setMeasurements(prev => [...prev, m]);
    };

    const handleDeleteMeasure = (id: string) => {
        setMeasurements(prev => prev.filter(m => m.id !== id));
        if (selectedId === id) setSelectedId(null);
    };

    const handleUpdateMeasure = (id: string, updates: Partial<Measurement>) => {
        setMeasurements(prev => prev.map(m => m.id === id ? { ...m, ...updates } : m));
    };

    if (!mounted) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
            <div className="bg-zinc-900 border border-zinc-800 rounded-2xl w-full max-w-6xl h-[700px] flex flex-col shadow-2xl relative overflow-hidden animate-in zoom-in-95 duration-200">

                {/* Header */}
                <div className="p-4 border-b border-zinc-800 flex items-center justify-between bg-zinc-900/50">
                    <div className="flex items-center gap-4">
                        <h2 className="text-2xl font-bold text-white tracking-tight">{symbol}</h2>

                        {/* Timeframe Selector */}
                        <div className="flex bg-zinc-800/50 rounded-lg p-1 gap-1">
                            {RANGES.map((r) => (
                                <button
                                    key={r}
                                    onClick={() => setRange(r)}
                                    className={`px-3 py-1 rounded-md text-sm font-medium transition-all ${range === r
                                        ? "bg-indigo-600 text-white shadow-sm"
                                        : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700/50"
                                        }`}
                                >
                                    {r.toUpperCase()}
                                </button>
                            ))}
                        </div>

                        <div className="h-6 w-px bg-zinc-800" />

                        <button
                            onClick={() => setIsMeasuring(!isMeasuring)}
                            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${isMeasuring
                                ? "bg-indigo-600/20 text-indigo-400 border border-indigo-500/50"
                                : "text-zinc-400 hover:text-white hover:bg-zinc-800 border border-transparent"
                                }`}
                            title="Measure (M)"
                        >
                            <LucideRuler size={16} />
                            <span>Measure</span>
                        </button>
                    </div>

                    <button
                        onClick={onClose}
                        className="p-2 text-zinc-500 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors"
                    >
                        <LucideX size={20} />
                    </button>
                </div>

                {/* Content Area */}
                <div className="flex-1 flex overflow-hidden bg-black/20">
                    <div className="flex-1 relative">
                        {isLoading && (
                            <div className="absolute inset-0 flex items-center justify-center z-10 bg-black/10">
                                <LucideLoader2 className="animate-spin text-indigo-500" size={32} />
                            </div>
                        )}

                        {data && !data.error && (
                            <div className="absolute inset-0 p-4">
                                <DetailChart
                                    data={data}
                                    symbol={symbol}
                                    isMeasuring={isMeasuring}
                                    measurements={measurements}
                                    selectedId={selectedId}
                                    onAddMeasure={handleAddMeasure}
                                    onSelectMeasure={(m) => setSelectedId(m ? m.id : null)}
                                    onClearAll={() => setMeasurements([])}
                                />
                            </div>
                        )}

                        {data && data.error && (
                            <div className="absolute inset-0 flex items-center justify-center text-red-400">
                                Error loading chart data: {data.error}
                            </div>
                        )}
                    </div>

                    {/* Side Panel */}
                    <MeasurementPanel
                        measurements={measurements}
                        selectedId={selectedId}
                        symbol={symbol}
                        onDelete={handleDeleteMeasure}
                        onUpdate={handleUpdateMeasure}
                        onDownloadCsv={handleDownloadCsv}
                        candleData={data?.candles || []}
                    />
                </div>
            </div>
        </div>
    );
}
