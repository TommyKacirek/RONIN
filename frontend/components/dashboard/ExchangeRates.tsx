import React from 'react';

interface ExchangeRatesProps {
    rates?: Record<string, number>;
}

export function ExchangeRates({ rates }: ExchangeRatesProps) {
    if (!rates) return null;

    const currencies = ["USD", "EUR", "GBP", "HKD", "SEK", "PLN"];

    return (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <h3 className="text-slate-400 text-sm font-medium mb-4">Current FX Rates (to CZK)</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {currencies.map((curr) => {
                    const rate = rates[curr];
                    if (!rate) return null;
                    return (
                        <div key={curr} className="flex flex-col">
                            <span className="text-xs text-slate-500">{curr}/CZK</span>
                            <span className="text-lg font-mono text-slate-200">
                                {rate.toFixed(2)}
                            </span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
