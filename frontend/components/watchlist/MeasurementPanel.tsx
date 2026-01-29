"use client";

import { Measurement } from "./DetailChart";
import { LucideTrash2, LucideDownload, LucideInfo } from "lucide-react";

interface MeasurementPanelProps {
    measurements: Measurement[];
    selectedId: string | null;
    symbol: string;
    onDelete: (id: string) => void;
    onUpdate: (id: string, updates: Partial<Measurement>) => void;
    onDownloadCsv: () => void;
    candleData: any[]; // Used to calculate metrics
}

export function MeasurementPanel({ measurements, selectedId, symbol, onDelete, onUpdate, onDownloadCsv, candleData }: MeasurementPanelProps) {

    const calculateMetrics = (m: Measurement) => {
        const startIdx = candleData.findIndex(c => c.time === m.start.time);
        const endIdx = candleData.findIndex(c => c.time === m.end.time);

        if (startIdx === -1 || endIdx === -1) return null;

        const realStart = Math.min(startIdx, endIdx);
        const realEnd = Math.max(startIdx, endIdx);
        const slice = candleData.slice(realStart, realEnd + 1);

        const startPrice = m.start.price;
        const endPrice = m.end.price;
        const absChange = endPrice - startPrice;
        const pctChange = (absChange / startPrice) * 100;

        const totalVol = slice.reduce((acc, c) => acc + (c.volume || 0), 0);
        const days = slice.length;
        const avgDailyPct = pctChange / days;

        return {
            absChange,
            pctChange,
            totalVol,
            days,
            avgDailyPct
        };
    };

    const selectedMeasure = measurements.find(m => m.id === selectedId);
    const metrics = selectedMeasure ? calculateMetrics(selectedMeasure) : null;

    return (
        <div className="w-80 border-l border-zinc-800 bg-zinc-900/50 flex flex-col h-full overflow-hidden">
            <div className="p-4 border-b border-zinc-800 flex items-center justify-between">
                <h3 className="font-bold text-white text-sm">Measurements</h3>
                <button
                    onClick={onDownloadCsv}
                    className="p-1.5 text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-md transition-colors"
                    title="Export CSV"
                >
                    <LucideDownload size={16} />
                </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {selectedMeasure && metrics ? (
                    <div className="space-y-4 animate-in fade-in slide-in-from-right-4 duration-300">
                        <div className="p-3 bg-indigo-600/10 rounded-xl border border-indigo-500/30">
                            <div className="flex justify-between items-start mb-2">
                                <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider px-2 py-0.5 bg-indigo-500/10 rounded">Selected</span>
                                <button onClick={() => onDelete(selectedMeasure.id)} className="text-zinc-500 hover:text-rose-400 p-1">
                                    <LucideTrash2 size={14} />
                                </button>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <p className="text-[10px] text-zinc-500 uppercase font-medium">Change</p>
                                    <p className={`text-lg font-bold ${metrics.pctChange >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                                        {metrics.pctChange.toFixed(2)}%
                                    </p>
                                    <p className="text-xs text-zinc-400">${metrics.absChange.toFixed(2)}</p>
                                </div>
                                <div>
                                    <p className="text-[10px] text-zinc-500 uppercase font-medium">Duration</p>
                                    <p className="text-lg font-bold text-white">{metrics.days} Bars</p>
                                    <p className="text-xs text-zinc-400">{metrics.avgDailyPct.toFixed(2)}% / bar</p>
                                </div>
                            </div>

                            <div className="mt-4 pt-4 border-t border-indigo-500/10">
                                <p className="text-[10px] text-zinc-500 uppercase font-medium">Total Volume</p>
                                <p className="text-base font-bold text-white">
                                    {metrics.totalVol.toLocaleString()}
                                </p>
                            </div>
                            <div className="mt-4 pt-4 border-t border-indigo-500/10 space-y-2">
                                <p className="text-[10px] text-zinc-500 uppercase font-medium">Notes</p>
                                <textarea
                                    className="w-full bg-zinc-950/50 border border-zinc-800 rounded-lg p-2 text-xs text-zinc-300 focus:outline-none focus:border-indigo-500/50 transition-colors resize-none h-20"
                                    placeholder="Add analysis note..."
                                    value={selectedMeasure.note || ''}
                                    onChange={(e) => onUpdate(selectedMeasure.id, { note: e.target.value })}
                                />
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="h-40 flex flex-col items-center justify-center text-center space-y-2 opacity-50">
                        <LucideInfo size={24} className="text-zinc-600" />
                        <p className="text-xs text-zinc-500">Select a measurement on the chart<br />to see detailed metrics.</p>
                    </div>
                )}

                <div className="space-y-2 pt-4">
                    <p className="text-[10px] text-zinc-500 uppercase font-bold tracking-widest pl-1">All History</p>
                    {measurements.map(m => (
                        <div
                            key={m.id}
                            className={`p-3 rounded-lg border transition-all ${selectedId === m.id ? 'bg-zinc-800 border-zinc-700' : 'bg-zinc-900/30 border-transparent hover:border-zinc-800'}`}
                        >
                            <div className="flex justify-between items-center">
                                <div className="space-y-0.5">
                                    <p className="text-xs font-medium text-zinc-300">
                                        {((m.end.price - m.start.price) / m.start.price * 100).toFixed(2)}%
                                    </p>
                                    <p className="text-[10px] text-zinc-500">
                                        {typeof m.start.time === 'string' ? m.start.time : new Date((m.start.time as number) * 1000).toLocaleDateString()}
                                    </p>
                                </div>
                                {selectedId === m.id && (
                                    <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.5)]" />
                                )}
                            </div>
                        </div>
                    ))}
                    {measurements.length === 0 && (
                        <p className="text-[10px] text-center text-zinc-600 italic py-4">No measurements yet</p>
                    )}
                </div>
            </div>
        </div>
    );
}
