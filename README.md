# RONIN 📈

RONIN is a high-performance, local-first investment dashboard specifically designed for Interactive Brokers (IBKR) users. It provides a real-time "cockpit" view of your holdings, advanced analytics, and a dedicated options trading journal.

## ✨ Features
- **IBKR Integration:** Simply upload your Activity Statement (CSV), and the app does the rest.
- **Shadow Ledger:** Reconstructs your "true" cost basis and quantities from trade history, bypasses common report discrepancies and handles multi-currency P&L correctly.
- **Options Journal & Calculator:** Dedicated module to track option trades (Wheel strategy, etc.), calculate p.a. returns, and monitor downside protection.
- **Interactive Exposure:** Drill down from global regions to specific countries. Filter out derivatives for a clean equity view.
- **Live Market Data:** Real-time prices, FX rates, and 52-week ranges via Yahoo Finance integration.
- **Trade Simulator:** Add "ghost" positions to see how a new buy affects your Leverage and Portfolio Weight.
- **Multi-Currency Support:** View your portfolio in USD or CZK with reliable currency conversion.
- **Privacy First:** 100% local. Your financial data never leaves your machine.

## 📂 Project Structure
- `backend/`: FastAPI application and business logic.
- `frontend/`: Next.js 14 client application.
- `scripts/`: Shared utility scripts for data diagnostics and management.

## 🚀 Quick Start

## 🚀 Quick Start (Windows)

The easiest way to start is to use the universal startup script. It will check for prerequisites, install dependencies, and launch both servers automatically.

1. **Right-click `start.ps1`** and select **Run with PowerShell**.
2. Wait for the setup to finish.
3. The dashboard will be available at [http://localhost:3000](http://localhost:3000).

---

### Manual Setup (Optional)

#### 1. Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

#### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 🛠️ Tech Stack
- **Frontend:** Next.js 14, TypeScript, Tailwind CSS, SWR, Lucide Icons, Recharts, Framer Motion.
- **Backend:** FastAPI, Pandas (Data processing), yfinance (Market data).

## 📝 Documentation
- [SPECIFICATION.md](./SPECIFICATION.md): Detailed calculation logic (FX, P&L, Reconstruction).
- [ARCHITECTURE.md](./ARCHITECTURE.md): Deep dive into the codebase and service layers.
