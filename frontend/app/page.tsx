"use client";

import { useState } from "react";
import { usePortfolio } from "@/hooks/usePortfolio";
import { HoldingsTable } from "@/components/dashboard/HoldingsTable";
import { KPICard } from "@/components/dashboard/KPICard";
import { SimulationPanel } from "@/components/dashboard/SimulationPanel";
import { Onboarding } from "@/components/dashboard/Onboarding";
import { LeverageCard } from "@/components/dashboard/LeverageCard";
import { ExposureChart } from "@/components/dashboard/ExposureChart";
import { ExchangeRates } from "@/components/dashboard/ExchangeRates";
import PortfolioMetricsCard from "@/components/dashboard/PortfolioMetricsCard";
import { LucideLayoutDashboard, LucideWallet, LucideTrendingUp, LucideRefreshCw, LucideUpload } from "lucide-react";
import { Toaster } from "sonner";
import { FileUpload } from "@/components/dashboard/FileUpload";
import { LucidePlus, LucideX, LucidePieChart } from "lucide-react";
import Link from "next/link";

export default function DashboardPage() {
  const {
    data, error, isLoading, mutate,
    simulations, addSimulation, removeSimulation,
    mergedPositions, currentLeverage, projectedLeverage,
    projectedPctInvested, projectedCashUsd, projectedNetLiqUsd,
    projectedMarketValCzk, usdCzkRate, positionsCount
  } = usePortfolio();

  const [currency, setCurrency] = useState<'USD' | 'CZK'>('USD');
  const [showExcluded, setShowExcluded] = useState(false);
  const [isUploadOpen, setIsUploadOpen] = useState(false);

  if (isLoading) return <div className="min-h-screen bg-black flex items-center justify-center text-zinc-500 animate-pulse">Loading RONIN...</div>;
  if (error) return <div className="min-h-screen bg-black flex items-center justify-center text-rose-500">Error connecting to backend</div>;
  if (!data) return null;

  if (data.status === 'empty') {
    return <Onboarding onComplete={() => mutate()} />;
  }

  const prefix = currency === 'USD' ? '$' : 'Kč ';
  const hasSims = simulations.length > 0;
  const netLiqUsd = hasSims ? projectedNetLiqUsd : data.kpi.net_liquidity_usd;
  const netLiqCzk = hasSims ? (projectedNetLiqUsd * usdCzkRate) : data.kpi.net_liquidity_czk;

  const netLiqDisplay = currency === 'USD' ? netLiqUsd : netLiqCzk;
  const cash = hasSims ? projectedCashUsd : (data.kpi.cash_balance_usd || 0);
  const displayPositions = showExcluded ? mergedPositions : mergedPositions.filter(p => !p.is_excluded);

  // Portfolio Metrics calculations
  const stockValueCzk = data.kpi.total_market_czk || 0;
  const stockValueUsd = stockValueCzk / usdCzkRate;
  const totalPnlCzk = (data.kpi as any).total_pnl_czk || 0;
  const costBasisCzk = stockValueCzk - totalPnlCzk;
  const costBasisUsd = costBasisCzk / usdCzkRate;

  return (
    <div className="min-h-screen bg-black text-white font-sans selection:bg-zinc-800">
      <Toaster position="top-right" theme="dark" />

      <div className="max-w-[98%] mx-auto p-4 md:p-8 space-y-8">
        {/* Header */}
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-indigo-500/10 rounded-xl text-indigo-400">
              <LucideLayoutDashboard size={24} />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">RONIN</h1>
              <p className="text-zinc-500 text-sm">Fintech Dashboard</p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <label className="flex items-center space-x-2 text-sm text-zinc-400 cursor-pointer hover:text-white">
              <input
                type="checkbox"
                checked={showExcluded}
                onChange={(e) => setShowExcluded(e.target.checked)}
                className="rounded border-zinc-700 bg-zinc-900 focus:ring-indigo-500"
              />
              <span>Show Excluded</span>
            </label>
            <button
              onClick={() => setIsUploadOpen(true)}
              className="flex items-center px-4 py-2 bg-blue-600/10 border border-blue-500/20 rounded-lg text-sm font-medium text-blue-400 hover:bg-blue-600/20 transition-colors"
            >
              <LucideUpload size={14} className="mr-2" />
              Upload CSV
            </button>
            <Link
              href="/performance"
              className="flex items-center px-4 py-2 bg-purple-500/10 border border-purple-500/20 rounded-lg text-sm font-medium text-purple-400 hover:bg-purple-500/20 transition-colors"
            >
              <LucidePieChart size={14} className="mr-2" />
              Performance
            </Link>
            <div className="h-6 w-px bg-zinc-800" />
            <button
              onClick={() => setCurrency(c => c === 'USD' ? 'CZK' : 'USD')}
              className="flex items-center px-4 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-sm font-medium hover:bg-zinc-800 transition-colors"
            >
              <LucideRefreshCw size={14} className="mr-2 text-zinc-500" />
              {currency} View
            </button>
          </div>
        </header>

        {/* KPI Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <PortfolioMetricsCard
            netLiquidityCzk={netLiqCzk}
            netLiquidityUsd={netLiqUsd}
            stockValueCzk={stockValueCzk}
            stockValueUsd={stockValueUsd}
            costBasisCzk={costBasisCzk}
            costBasisUsd={costBasisUsd}
            totalPnlCzk={totalPnlCzk}
          />

          <LeverageCard
            currentLeverage={currentLeverage}
            projectedLeverage={projectedLeverage}
            hasSimulations={hasSims}
          />

          <KPICard
            title={`Cash (USD)${hasSims ? " (Proj.)" : ""}`}
            value={`$${cash.toLocaleString(undefined, { maximumFractionDigits: 2 })}`}
            subValue={hasSims
              ? (cash < 0
                ? `Borrowing $${Math.abs(cash).toLocaleString()} on Margin`
                : `-$${(data.kpi.cash_balance_usd - projectedCashUsd).toLocaleString()} from Sim`)
              : "Uninvested Balance"}
            icon={LucideWallet}
            details={data.kpi.cash_balances?.map(cb => (
              <div key={cb.currency} className="flex flex-col w-full mb-1">
                <div className="flex justify-between items-center">
                  <span className={cb.amount >= 0 ? "text-emerald-400" : "text-rose-400"}>
                    {cb.currency} {cb.amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>
                  <span className="text-zinc-600 ml-2">
                    (≈ {Math.round(cb.value_czk).toLocaleString()} Kč)
                  </span>
                </div>
                {/* Margin Interest Warning */}
                {cb.daily_interest_czk && cb.daily_interest_czk > 0 ? (
                  <div className="text-[10px] text-rose-500/80 text-right mt-0.5">
                    Daily: -{Math.round(cb.daily_interest_czk)} Kč ({cb.daily_interest_native?.toFixed(2)} {cb.currency}) <span className="opacity-70">@ {cb.effective_rate?.toFixed(2)}%</span>
                  </div>
                ) : null}
              </div>
            ))}
          />
          <KPICard
            title="Positions"
            value={positionsCount.toString()}
            subValue={simulations.length > 0 ? `+ ${simulations.length} Simulated` : "Active Holdings"}
            icon={LucideTrendingUp}
          />
        </div>


        {/* Simulator */}
        <SimulationPanel
          simulations={simulations}
          onAdd={addSimulation}
          onRemove={removeSimulation}
          netLiqUsd={netLiqUsd}
          fxRates={data.fx_rates}
        />

        {/* Charts & Rates Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 min-h-[400px]">
            <ExposureChart
              positions={displayPositions}
              cashValue={currency === 'CZK' ? (projectedCashUsd * usdCzkRate) : projectedCashUsd}
            />
          </div>
          <div className="lg:col-span-1">
            <ExchangeRates rates={data.fx_rates} />
          </div>
        </div>

        {/* Main Table */}
        <main>
          <HoldingsTable data={displayPositions} currency={currency} />
        </main>

        {/* Upload Modal */}
        {isUploadOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
            <div className="bg-zinc-900 border border-zinc-800 rounded-3xl w-full max-w-md overflow-hidden relative shadow-2xl">
              <button
                onClick={() => setIsUploadOpen(false)}
                className="absolute top-4 right-4 text-zinc-500 hover:text-white transition-colors"
              >
                <LucideX size={24} />
              </button>
              <div className="p-8 space-y-6 text-center">
                <div className="inline-flex p-3 bg-blue-500/10 rounded-xl text-blue-400">
                  <LucidePlus size={24} />
                </div>
                <div className="space-y-2">
                  <h2 className="text-2xl font-bold">Přidat data</h2>
                  <p className="text-zinc-500 text-sm">Nahraj další IBKR CSV soubory pro aktualizaci portfolia.</p>
                </div>
                <FileUpload
                  compact
                  onComplete={() => {
                    setIsUploadOpen(false);
                    mutate();
                  }}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
