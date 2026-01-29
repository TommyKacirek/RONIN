# RONIN - Architecture Deep Dive

This document explains the technical structure of the application.

## 📡 Backend Structure (`/backend`)
The backend is a FastAPI application designed around a **Service-Based Architecture**.

### Service Layer (`app/services/`)
- **`market.py`**: The "Heart" of data fetching. Async service for live prices and FX rates with persistent JSON caching in `market_cache.json`.
- **`engine.py`**: The "Brain". Orchestrates data from parser, merger, and reconstructor. Handles country detection and regional grouping.
- **`options.py`**: **[NEW]** Manages the persistent Options Journal (`options.json`). Handles CRUD for option trades and calculates summary stats (Premium collected, Exposure).
- **`reconstructor.py`**: Implements the "Shadow Ledger" logic. Replays trades to find true cost basis in CZK.
- **`parser.py` / `merger.py`**: Handles raw IBKR CSV ingestion.
- **`store.py`**: Manages local JSON storage for equity metadata (notes, buy/sell targets).

### Data Models
- **`app/models.py`**: Centralized Pydantic models for API validation (OptionTrade, MetadataUpdate, etc.).

---

## 🎨 Frontend Structure (`/frontend`)
The frontend is a modern Next.js 14 application focusing on visual excellence and clean data flow.

### Custom Hooks (`hooks/`)
- **`usePortfolio.ts`**: The single source of truth for the dashboard. It manages data fetching (SWR), simulation state, and all derived calculations.

### Functional Areas
- **Dashboard (`app/page.tsx`)**: Global portfolio overview, exposure charts, and main holdings table.
- **Options Module (`app/options/`)**:
  - `OptionsCalculator`: Real-time return calculator for new potential trades.
  - `OptionsJournal`: History of all recorded option trades.
  - `OptionsDashboard`: KPI summary for current option strategy.
- **Watchlist (`app/watchlist/`)**: Price monitoring and technical charts.

---

## 🔄 Data Flow
1. **Interactive Indicators:** Dashboard calls `/api/portfolio`.
2. **Options Journal:** Options page calls `/api/options`.
3. **Synchronization:** Users can sync existing options from IBKR CSVs into the persistent `options.json` via `/api/options/import`.
4. **Price Feed:** `MarketDataService` fetches live quotes from Yahoo Finance for both equities and FX pairs (e.g., `USDCZK=X`).
