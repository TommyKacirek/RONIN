"use client";

import React, { useState, useMemo } from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import { ChevronLeft } from 'lucide-react';

import { Position } from '@/app/types';

interface ExposureChartProps {
    positions: Position[];
    cashValue?: number;
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#6366f1'];

const ISO_TO_COUNTRY: Record<string, string> = {
    "US": "United States", "CN": "China", "DE": "Germany", "GB": "United Kingdom",
    "FR": "France", "CH": "Switzerland", "JP": "Japan", "TW": "Taiwan",
    "HK": "Hong Kong", "IN": "India", "KR": "South Korea", "SG": "Singapore",
    "NL": "Netherlands", "SE": "Sweden", "NO": "Norway", "DK": "Denmark",
    "AU": "Australia", "CA": "Canada", "BR": "Brazil", "MX": "Mexico", "ZA": "South Africa"
};

const getCountryName = (iso: string) => ISO_TO_COUNTRY[iso] || iso;

export function ExposureChart({ positions, cashValue }: ExposureChartProps) {
    const [view, setView] = useState<'region' | 'country'>('region');
    const [selectedRegion, setSelectedRegion] = useState<string | null>(null);

    const data = useMemo(() => {
        if (view === 'region') {
            const regions: Record<string, number> = {};
            positions
                .filter(p => p.region !== 'Derivatives')
                .forEach(p => {
                    const r = p.region || 'Unknown';
                    regions[r] = (regions[r] || 0) + p.market_value_czk;
                });

            const results = Object.entries(regions)
                .map(([name, value]) => ({ name, value }));

            if (cashValue && cashValue > 0) {
                results.push({ name: 'Cash', value: cashValue });
            }

            return results.sort((a, b) => b.value - a.value);
        } else {
            // Country view for selected region
            const countries: Record<string, number> = {};
            positions
                .filter(p => !selectedRegion || p.region === selectedRegion)
                .forEach(p => {
                    const c = p.country || 'Unknown';
                    const name = getCountryName(c); // Map for Display
                    countries[name] = (countries[name] || 0) + p.market_value_czk;
                });
            return Object.entries(countries)
                .map(([name, value]) => ({ name, value }))
                .sort((a, b) => b.value - a.value);
        }
    }, [positions, view, selectedRegion]);

    const totalValue = data.reduce((acc, curr) => acc + curr.value, 0);

    const handleClick = (entry: any) => {
        if (view === 'region') {
            setSelectedRegion(entry.name);
            setView('country');
        }
    };

    const handleBack = () => {
        setSelectedRegion(null);
        setView('region');
    };

    const relevantPositions = useMemo(() => {
        // Filter based on current view depth
        let filtered = positions.filter(p => p.region !== 'Derivatives');

        if (selectedRegion) {
            filtered = filtered.filter(p => p.region === selectedRegion);
        }

        return filtered.sort((a, b) => b.market_value_czk - a.market_value_czk);
    }, [positions, selectedRegion]);

    return (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 h-full flex flex-col">
            <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                    {view === 'country' && (
                        <button
                            onClick={handleBack}
                            className="p-1 hover:bg-slate-800 rounded-full text-slate-400 hover:text-white transition-colors"
                        >
                            <ChevronLeft className="w-4 h-4" />
                        </button>
                    )}
                    <h3 className="text-slate-400 text-sm font-medium">
                        Exposure by {view === 'region' ? 'Market' : selectedRegion}
                    </h3>
                </div>
            </div>

            <div className="flex-1 min-h-[200px] relative">
                <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                        <Pie
                            data={data}
                            cx="50%"
                            cy="50%"
                            innerRadius={60}
                            outerRadius={80}
                            paddingAngle={2}
                            dataKey="value"
                            onClick={handleClick}
                            cursor="pointer"
                        >
                            {data.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} stroke="rgba(0,0,0,0)" />
                            ))}
                        </Pie>
                        <Tooltip
                            contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px' }}
                            itemStyle={{ color: '#e2e8f0' }}
                            formatter={(value: any, name: any) =>
                                [`${(Number(value) / totalValue * 100).toFixed(1)}%`, name]
                            }
                        />
                    </PieChart>
                </ResponsiveContainer>

                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <span className="text-slate-500 text-sm font-medium">
                        {view === 'region' ? 'Regions' : 'Countries'}
                    </span>
                </div>
            </div>

            <div className="mt-4 border-t border-slate-800 pt-3">
                {view === 'region' ? (
                    // Default Legend
                    <div className="grid grid-cols-2 gap-2">
                        {data.slice(0, 6).map((entry, index) => (
                            <div key={entry.name} className="flex items-center gap-2">
                                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }} />
                                <span className="text-xs text-slate-400 truncate flex-1">{entry.name}</span>
                                <span className="text-xs text-slate-500">{(entry.value / totalValue * 100).toFixed(0)}%</span>
                            </div>
                        ))}
                    </div>
                ) : (
                    // Ticker List for Selected Region
                    <div className="flex flex-col gap-1 mt-2">
                        <div className="flex justify-between text-[10px] text-slate-500 pb-1 border-b border-slate-800 mb-1 px-1">
                            <span>Holding</span>
                            <div className="flex gap-3 text-right">
                                <span className="w-12">Avg Price</span>
                                <span className="w-10">% Port</span>
                                <span className="w-10">Value</span>
                            </div>
                        </div>
                        {/* Auto-sizing container: No fixed height, max-height imposes scroll only if extensive */}
                        <div className="flex flex-col gap-1 max-h-[300px] overflow-y-auto custom-scrollbar pr-1">
                            {relevantPositions.map((pos) => (
                                <div key={pos.symbol} className="flex items-center justify-between text-xs hover:bg-slate-800/50 p-1 rounded cursor-pointer transition-colors group">
                                    <div className="flex items-center gap-2">
                                        <div className={`w-1 h-3 rounded-full ${(pos.pnl_percent || 0) >= 0 ? 'bg-emerald-500' : 'bg-rose-500'}`} />
                                        <div>
                                            <div className="font-medium text-slate-200">{pos.symbol}</div>
                                            <div className="text-[10px] text-slate-500 truncate max-w-[120px]">{pos.name}</div>
                                        </div>
                                    </div>
                                    <div className="flex gap-3 text-right">
                                        <div className="w-12 text-slate-400">{pos.average_buy_price?.toFixed(1) || '-'}</div>
                                        <div className="w-10 text-slate-300 font-mono">{(pos.pct_portfolio || 0).toFixed(2)}%</div>
                                        <div className="w-10 text-[10px] text-slate-500">{(pos.market_value_czk / 1000).toFixed(0)}k</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                        {relevantPositions.length === 0 && (
                            <div className="text-xs text-slate-500 text-center py-4">No positions found</div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
