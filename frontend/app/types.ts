export interface OptionTrade {
    id?: string;
    ticker: string;
    type: string; // "SELL PUT" | "BUY CALL" etc
    strike: number;
    expiration: string;
    premium: number;
    fees: number;
    currency: string;
    status: string; // "OPEN" | "CLOSED" | "EXPIRED" | "ASSIGNED"
    date_opened: string;
    notes?: string;
    // Calculated frontend fields
    annualized_return?: number;
    ror?: number;
}

export interface MetaData {
    target_price?: number;
    risk?: number;
    note?: string;
}

export interface CashBalance {
    currency: string;
    amount: number;
    value_czk: number;
    value_usd: number;
    daily_interest_native?: number;
    daily_interest_czk?: number;
    effective_rate?: number;
}

export interface KPI {
    net_liquidity_usd: number;
    net_liquidity_czk: number;
    cash_balance_usd: number;
    cash_balances?: CashBalance[];
    pct_invested?: number;
    total_market_czk?: number;
    gross_position_usd?: number;  // Absolute value sum (for IBKR-style leverage)
    gross_position_czk?: number;
    leverage?: number;  // Pre-calculated Gross Position / Net Liq
}

export interface Position {
    symbol: string;
    currency: string;
    quantity: number;
    current_price?: number;
    name?: string;

    // Market Values
    market_value_native: number;
    market_value_usd: number;
    market_value_czk: number;
    pct_portfolio?: number;

    // Cost & PnL
    cost_basis_czk: number;
    unrealized_pnl_czk: number;
    unrealized_pnl_native?: number;
    pnl_percent?: number;
    average_buy_price?: number;

    // Metadata (Editable)
    target_price?: number;
    risk_score?: number;
    buy_zone?: number;
    sell_zone?: number;
    notes?: string;

    // Calculated
    distance_to_target?: number;
    pct_to_buy?: number;
    pct_to_sell?: number;
    instruction?: string;
    year_high?: number;
    year_low?: number;

    // Flags
    is_excluded: boolean;
    is_simulated?: boolean;
    recon_match?: boolean;
    price_source?: string;

    meta?: MetaData; // Deprecated but kept for compatibility if needed

    // Geographical
    region?: string;
    country?: string;
}

export interface PortfolioData {
    kpi: KPI;
    positions: Position[];
    fx_rates?: Record<string, number>;
}

export interface Trade {
    symbol: string;
    date: string;
    time: string;
    date_obj: string; // ISO string from backend
    quantity: number;
    price: number;
    proceeds: number;
    commission: number;
    basis: number; // Cost basis for ROI calc
    realized_pnl: number;
    currency: string;
    category: string;
    code: string;
}

export interface Interest {
    date: string;
    date_obj: string;
    currency: string;
    description: string;
    amount: number;
}

export interface PerformanceData {
    trades: Trade[];
    interest: Interest[];
    files: string[];
}
