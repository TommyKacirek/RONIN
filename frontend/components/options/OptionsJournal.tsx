
import React from 'react';
import { OptionTrade } from '@/app/types';

interface OptionsJournalProps {
    trades: OptionTrade[];
}

export function OptionsJournal({ trades }: OptionsJournalProps) {
    const getStatusColor = (status: string) => {
        switch (status) {
            case 'OPEN': return 'bg-red-500/10 text-red-500 border-red-500/20';
            case 'EXPIRED': return 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20';
            case 'CLOSED': return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
            case 'ASSIGNED': return 'bg-purple-500/10 text-purple-500 border-purple-500/20';
            default: return 'bg-zinc-800 text-zinc-400';
        }
    };

    const calculatePA = (trade: OptionTrade) => {
        if (!trade.premium || !trade.strike) return 0;
        // Simple Approximation if dates not parsed perfectly
        // Assume 30 days if not calculated dynamically or use open date vs expiryme
        // For now: Just (Premium/Strike) * 12 * 100 roughly
        return ((trade.premium / trade.strike) * 100).toFixed(1) + "%";
    };

    return (
        <div className="rounded-2xl bg-zinc-900 border border-zinc-800 overflow-hidden">
            <div className="p-4 border-b border-zinc-800 flex justify-between items-center">
                <h3 className="font-semibold text-white">Trade Journal</h3>
                <div className="flex gap-2">
                    {/* Filters could go here */}
                </div>
            </div>
            <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                    <thead className="bg-zinc-950 text-zinc-400 uppercase text-xs">
                        <tr>
                            <th className="px-4 py-3">Status</th>
                            <th className="px-4 py-3">Date</th>
                            <th className="px-4 py-3">Ticker</th>
                            <th className="px-4 py-3">Type</th>
                            <th className="px-4 py-3">Strike</th>
                            <th className="px-4 py-3">Exp</th>
                            <th className="px-4 py-3 text-right">Premium</th>
                            <th className="px-4 py-3 text-right">Yield</th>
                            <th className="px-4 py-3">Notes</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800">
                        {trades.map((trade) => (
                            <tr key={trade.id || Math.random()} className="hover:bg-zinc-800/50">
                                <td className="px-4 py-3">
                                    <span className={`px-2 py-1 rounded-full text-xs border ${getStatusColor(trade.status)}`}>
                                        {trade.status}
                                    </span>
                                </td>
                                <td className="px-4 py-3 text-zinc-300">{trade.date_opened}</td>
                                <td className="px-4 py-3 font-bold text-white">{trade.ticker}</td>
                                <td className="px-4 py-3 text-zinc-400">{trade.type}</td>
                                <td className="px-4 py-3 text-zinc-300">{trade.strike}</td>
                                <td className="px-4 py-3 text-zinc-300">{trade.expiration}</td>
                                <td className="px-4 py-3 text-right text-emerald-400 font-mono">
                                    {trade.premium} {trade.currency}
                                </td>
                                <td className="px-4 py-3 text-right text-zinc-400">
                                    {calculatePA(trade)}
                                </td>
                                <td className="px-4 py-3 text-zinc-500 truncate max-w-xs">{trade.notes}</td>
                            </tr>
                        ))}
                        {trades.length === 0 && (
                            <tr>
                                <td colSpan={9} className="px-4 py-8 text-center text-zinc-500">
                                    No trades recorded in journal.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
