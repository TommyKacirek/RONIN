"use client";

import { TrendingDown, TrendingUp, Wallet, DollarSign, PiggyBank, BarChart3 } from "lucide-react";

interface PortfolioMetricsCardProps {
    netLiquidityCzk: number;
    netLiquidityUsd: number;
    stockValueCzk: number;
    stockValueUsd: number;
    costBasisCzk: number;
    costBasisUsd: number;
    totalPnlCzk: number;
}

export default function PortfolioMetricsCard({
    netLiquidityCzk,
    netLiquidityUsd,
    stockValueCzk,
    stockValueUsd,
    costBasisCzk,
    costBasisUsd,
    totalPnlCzk,
}: PortfolioMetricsCardProps) {
    const pnlPercent = costBasisCzk !== 0 ? (totalPnlCzk / costBasisCzk) * 100 : 0;
    const isPositive = totalPnlCzk >= 0;

    const formatCurrency = (value: number, decimals = 0) => {
        return value.toLocaleString(undefined, { maximumFractionDigits: decimals, minimumFractionDigits: decimals });
    };

    const metrics = [
        {
            label: "Net Liquidity",
            tooltip: "Total account value (stocks + cash + accruals)",
            czk: netLiquidityCzk,
            usd: netLiquidityUsd,
            icon: Wallet,
            color: "text-blue-400",
        },
        {
            label: "Stock Value",
            tooltip: "Market value of positions only",
            czk: stockValueCzk,
            usd: stockValueUsd,
            icon: BarChart3,
            color: "text-purple-400",
        },
        {
            label: "Cost Basis",
            tooltip: "Original investment amount",
            czk: costBasisCzk,
            usd: costBasisUsd,
            icon: PiggyBank,
            color: "text-amber-400",
        },
    ];

    return (
        <div className="bg-zinc-900/50 backdrop-blur-sm border border-zinc-800/50 rounded-xl p-6 hover:border-zinc-700/50 transition-all">
            <div className="pb-3 border-b border-zinc-800/50 mb-4">
                <h3 className="text-base font-semibold flex items-center gap-2">
                    <DollarSign className="w-5 h-5 text-blue-400" />
                    Portfolio Metrics
                </h3>
            </div>
            <div className="space-y-4">
                {metrics.map((metric, idx) => {
                    const Icon = metric.icon;
                    return (
                        <div key={idx} className="flex items-start justify-between group">
                            <div className="flex items-start gap-3 flex-1">
                                <Icon className={`w-5 h-5 mt-0.5 ${metric.color}`} />
                                <div className="flex-1">
                                    <div className="flex items-baseline gap-2">
                                        <span className="text-sm text-muted-foreground">{metric.label}</span>
                                        <span className="text-xs text-muted-foreground/60 hidden group-hover:inline">
                                            {metric.tooltip}
                                        </span>
                                    </div>
                                    <div className="font-semibold text-lg">
                                        {formatCurrency(Math.round(metric.czk), 0)} Kč
                                    </div>
                                    <div className="text-xs text-muted-foreground">
                                        ${formatCurrency(Math.round(metric.usd), 0)} USD
                                    </div>
                                </div>
                            </div>
                        </div>
                    );
                })}

                {/* P&L Section */}
                <div className="pt-3 border-t border-border/50">
                    <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3 flex-1">
                            {isPositive ? (
                                <TrendingUp className="w-5 h-5 mt-0.5 text-green-400" />
                            ) : (
                                <TrendingDown className="w-5 h-5 mt-0.5 text-red-400" />
                            )}
                            <div className="flex-1">
                                <div className="text-sm text-muted-foreground">Total P&L</div>
                                <div className={`font-semibold text-lg ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
                                    {isPositive ? '+' : ''}{formatCurrency(Math.round(totalPnlCzk), 0)} Kč
                                </div>
                                <div className={`text-xs ${isPositive ? 'text-green-400/60' : 'text-red-400/60'}`}>
                                    {isPositive ? '+' : ''}{pnlPercent.toFixed(2)}%
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
