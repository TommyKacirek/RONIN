"use client";

import { LucideActivity } from "lucide-react";
import clsx from "clsx";

interface LeverageCardProps {
    currentLeverage: number;
    projectedLeverage: number;
    hasSimulations: boolean;
}

export function LeverageCard({ currentLeverage, projectedLeverage, hasSimulations }: LeverageCardProps) {
    const isHighRisk = projectedLeverage > 1.5;

    return (
        <div className={clsx(
            "p-6 rounded-2xl border transition-colors relative overflow-hidden",
            isHighRisk ? "bg-red-950/20 border-red-900/50" : "bg-zinc-900/50 border-zinc-800"
        )}>
            <div className="relative z-10">
                <div className="flex justify-between items-start">
                    <div>
                        <p className="text-zinc-500 text-sm font-medium">Leverage</p>
                        <div className="mt-2 flex items-baseline gap-2">
                            <span className={clsx("text-2xl font-bold", isHighRisk ? "text-red-400" : "text-white")}>
                                {projectedLeverage.toFixed(2)}x
                            </span>
                            {hasSimulations && (
                                <span className="text-xs text-zinc-500 opacity-60 line-through">
                                    {currentLeverage.toFixed(2)}x
                                </span>
                            )}
                        </div>
                        <p className="text-zinc-600 text-xs mt-1">Target &lt; 1.50</p>
                    </div>
                    <div className={clsx(
                        "p-2 rounded-lg",
                        isHighRisk ? "bg-red-500/10 text-red-500" : "bg-zinc-800/50 text-zinc-400"
                    )}>
                        <LucideActivity size={20} />
                    </div>
                </div>
            </div>
        </div>
    );
}
