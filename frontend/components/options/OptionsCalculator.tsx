
import React, { useState, useEffect } from 'react';
import { LucideCalculator, LucidePlus } from 'lucide-react';
import { OptionTrade } from '@/app/types';

interface OptionsCalculatorProps {
    onAddTrade: (trade: OptionTrade) => void;
}

export function OptionsCalculator({ onAddTrade }: OptionsCalculatorProps) {
    const [ticker, setTicker] = useState("");
    const [price, setPrice] = useState<string>("");
    const [strike, setStrike] = useState<string>("");
    const [premium, setPremium] = useState<string>("");
    const [dte, setDte] = useState<string>("30"); // Days to expiration
    const [type, setType] = useState("SELL PUT");

    // Calculated metrics
    const [annualized, setAnnualized] = useState(0);
    const [ror, setRor] = useState(0);
    const [protection, setProtection] = useState(0);

    useEffect(() => {
        const s = parseFloat(strike);
        const p = parseFloat(premium);
        const d = parseInt(dte);
        const pr = parseFloat(price);

        // Calc logic
        if (s > 0 && p > 0 && d > 0) {
            // Return on Risk (Capital at Risk = Strike * 100 - Premium * 100, simplified to Strike usually or Strike - Premium)
            // User formula: (Premium / Strike)
            const raw_return = p / s;
            setRor(raw_return * 100);

            // Annualized: raw * (365 / dte)
            setAnnualized(raw_return * (365 / d) * 100);

            // Distance / Protection
            // Break even = Strike - Premium
            if (pr > 0) {
                const be = s - p;
                const dist = (pr - be) / pr;
                setProtection(dist * 100);
            }
        } else {
            setAnnualized(0);
            setRor(0);
            setProtection(0);
        }
    }, [ticker, price, strike, premium, dte]);

    const handleSubmit = () => {
        const s = parseFloat(strike);
        const p = parseFloat(premium);
        const d = parseInt(dte);

        if (!s || !p || !d) return;

        // Calculate Expiration Date from DTE
        const date = new Date();
        date.setDate(date.getDate() + d);
        const expStr = date.toISOString().split('T')[0];
        const todayStr = new Date().toISOString().split('T')[0];

        const newTrade: OptionTrade = {
            ticker: ticker.toUpperCase(),
            type,
            strike: s,
            premium: p,
            fees: 1.0, // Default IBKR fee approx
            currency: "USD", // Default
            expiration: expStr,
            status: "OPEN",
            date_opened: todayStr,
            notes: `Calc: ${annualized.toFixed(1)}% p.a.`
        };
        onAddTrade(newTrade);
        // Reset? or Keep?
    };

    return (
        <div className="p-6 rounded-2xl bg-zinc-900 border border-zinc-800 mb-8">
            <div className="flex items-center gap-2 mb-4">
                <LucideCalculator className="text-indigo-400" size={20} />
                <h3 className="text-lg font-semibold text-white">Calculator</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-6 gap-4 items-end">
                <div className="md:col-span-1">
                    <label className="text-xs text-zinc-400 block mb-1">Ticker</label>
                    <input type="text" value={ticker} onChange={e => setTicker(e.target.value)}
                        className="w-full bg-black border border-zinc-700 rounded p-2 text-white uppercase" placeholder="SOFI" />
                </div>
                <div className="md:col-span-1">
                    <label className="text-xs text-zinc-400 block mb-1">Price ($)</label>
                    <input type="number" value={price} onChange={e => setPrice(e.target.value)}
                        className="w-full bg-black border border-zinc-700 rounded p-2 text-white" placeholder="7.50" />
                </div>
                <div className="md:col-span-1">
                    <label className="text-xs text-zinc-400 block mb-1">Strike</label>
                    <input type="number" value={strike} onChange={e => setStrike(e.target.value)}
                        className="w-full bg-black border border-zinc-700 rounded p-2 text-white" placeholder="7.0" />
                </div>
                <div className="md:col-span-1">
                    <label className="text-xs text-zinc-400 block mb-1">Premium</label>
                    <input type="number" value={premium} onChange={e => setPremium(e.target.value)}
                        className="w-full bg-black border border-zinc-700 rounded p-2 text-white" placeholder="0.15" />
                </div>
                <div className="md:col-span-1">
                    <label className="text-xs text-zinc-400 block mb-1">Days to Exp</label>
                    <input type="number" value={dte} onChange={e => setDte(e.target.value)}
                        className="w-full bg-black border border-zinc-700 rounded p-2 text-white" />
                </div>

                <div className="md:col-span-1">
                    <button onClick={handleSubmit} className="w-full bg-indigo-600 hover:bg-indigo-700 text-white rounded p-2 flex items-center justify-center gap-2">
                        <LucidePlus size={16} /> Add
                    </button>
                </div>
            </div>

            {annualized > 0 && (
                <div className="grid grid-cols-3 gap-4 mt-6 border-t border-zinc-800 pt-4">
                    <div className="text-center md:text-left">
                        <div className="text-xs text-zinc-500">Annualized Return</div>
                        <div className={`text-xl font-bold ${annualized > 15 ? 'text-emerald-400' : 'text-yellow-400'}`}>
                            {annualized.toFixed(2)}%
                        </div>
                    </div>
                    <div className="text-center md:text-left">
                        <div className="text-xs text-zinc-500">Return on Risk</div>
                        <div className="text-xl font-bold text-white">
                            {ror.toFixed(2)}%
                        </div>
                    </div>
                    <div className="text-center md:text-left">
                        <div className="text-xs text-zinc-500">Protection (Downside)</div>
                        <div className="text-xl font-bold text-white">
                            {protection.toFixed(2)}%
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
