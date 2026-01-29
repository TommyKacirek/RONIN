
"use client";
import React, { useEffect, useState } from 'react';
import { OptionsDashboard } from '@/components/options/OptionsDashboard';
import { OptionsCalculator } from '@/components/options/OptionsCalculator';
import { OptionsJournal } from '@/components/options/OptionsJournal';
import { OptionTrade } from '@/app/types';

export default function OptionsPage() {
    const [trades, setTrades] = useState<OptionTrade[]>([]);
    const [stats, setStats] = useState<any>({});
    const [loading, setLoading] = useState(true);

    const fetchData = async () => {
        try {
            const [tradesRes, statsRes] = await Promise.all([
                fetch('http://127.0.0.1:8000/api/options'),
                fetch('http://127.0.0.1:8000/api/options/stats')
            ]);
            const tradesData = await tradesRes.json();
            const statsData = await statsRes.json();
            setTrades(tradesData);
            setStats(statsData);
        } catch (error) {
            console.error("Failed to load options data", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handleAddTrade = async (trade: OptionTrade) => {
        try {
            const res = await fetch('http://127.0.0.1:8000/api/options', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(trade)
            });
            if (res.ok) {
                // Refresh data
                fetchData();
            }
        } catch (e) {
            console.error(e);
        }
    };

    const handleImport = async () => {
        setLoading(true);
        try {
            const res = await fetch('http://127.0.0.1:8000/api/options/import', { method: 'POST' });
            if (res.ok) {
                const data = await res.json();
                alert(`Imported ${data.imported} options from portfolio.`);
                fetchData();
            }
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    return (
        <main className="min-h-screen bg-black text-white p-8">
            <div className="max-w-7xl mx-auto">
                <div className="flex justify-between items-center mb-6">
                    <h1 className="text-3xl font-bold tracking-tight">Options Portfolio</h1>
                    <button onClick={handleImport} className="bg-zinc-800 hover:bg-zinc-700 text-zinc-300 px-4 py-2 rounded-lg text-sm border border-zinc-700">
                        Sync from Portfolio
                    </button>
                </div>

                <OptionsDashboard stats={stats} trades={trades} />
                <OptionsCalculator onAddTrade={handleAddTrade} />
                <OptionsJournal trades={trades} />
            </div>
        </main>
    );
}
