
import React from 'react';
import { OptionTrade } from '@/app/types';
import { LucideWallet, LucideTrendingUp, LucideActivity } from 'lucide-react';

interface OptionsDashboardProps {
    stats: any;
    trades: OptionTrade[];
}

export function OptionsDashboard({ stats, trades }: OptionsDashboardProps) {
    const formatCurrency = (val: number, curr: string = "USD") => {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: curr }).format(val);
    };

    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            {/* KPI 1: Total Puts Exposure */}
            <div className="p-6 rounded-2xl bg-zinc-900 border border-zinc-800">
                <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 bg-red-500/10 rounded-lg">
                        <LucideWallet className="text-red-400" size={20} />
                    </div>
                    <span className="text-sm font-medium text-zinc-400">Put Exposure (Risk)</span>
                </div>
                <div className="text-2xl font-bold text-white mt-1">
                    {formatCurrency(stats?.total_exposure_usd || 0, "USD")}
                </div>
                <div className="text-xs text-zinc-500 mt-2">
                    Blocked Margin (Est. 20%) ≈ {formatCurrency((stats?.total_exposure_usd || 0) * 0.2, "USD")}
                </div>
            </div>

            {/* KPI 2: Cash Flow Check */}
            <div className="p-6 rounded-2xl bg-zinc-900 border border-zinc-800">
                <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 bg-emerald-500/10 rounded-lg">
                        <LucideTrendingUp className="text-emerald-400" size={20} />
                    </div>
                    <span className="text-sm font-medium text-zinc-400">Yearly Premiums (Gross)</span>
                </div>
                <div className="flex flex-col gap-1 mt-1">
                    {Object.entries(stats?.yearly_premium_by_currency || {}).map(([curr, val]: any) => (
                        val > 0 && (
                            <div key={curr} className="text-lg font-bold text-white">
                                + {formatCurrency(val, curr)}
                            </div>
                        )
                    ))}
                    {Object.keys(stats?.yearly_premium_by_currency || {}).length === 0 && (
                        <div className="text-lg font-bold text-white">$0.00</div>
                    )}
                </div>
            </div>

            {/* KPI 3: Active Trades */}
            <div className="p-6 rounded-2xl bg-zinc-900 border border-zinc-800">
                <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 bg-blue-500/10 rounded-lg">
                        <LucideActivity className="text-blue-400" size={20} />
                    </div>
                    <span className="text-sm font-medium text-zinc-400">Active Contracts</span>
                </div>
                <div className="text-2xl font-bold text-white mt-1">
                    {stats?.active_trades || 0}
                </div>
                <div className="text-xs text-zinc-500 mt-2">
                    Open positions managing now
                </div>
            </div>
        </div>
    );
}
