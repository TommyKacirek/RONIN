import pandas as pd
import asyncio
import math
from datetime import datetime
from typing import Dict, Any, List, Optional
from .forex import ForexService
from .reconstructor import PortfolioReconstructor
from .market import MarketDataService
from .margin import MarginService

class PortfolioEngine:
    def __init__(self):
        self.market_data = MarketDataService()
        self.forex = ForexService()
        self.reconstructor = PortfolioReconstructor()
        self.margin = MarginService()
        
        # Caching
        self.cache_files_hash = ""
        self.cached_result = None
        self.cached_reconstructed = None

    # Region Mappings
    REGIONS = {
        "North America": ["US", "CA"],
        "Europe": ["DE", "GB", "FR", "IT", "ES", "NL", "CH", "SE", "NO", "DK", "FI", "IE", "AT", "BE", "PT", "CZ", "PL"],
        "Asia": ["CN", "JP", "KR", "TW", "HK", "IN", "SG", "ID", "MY", "TH", "VN"],
        "South America": ["BR", "AR", "CL", "CO", "PE", "MX"],
        "Pacific": ["AU", "NZ"],
        "Emerging": ["ZA", "SA", "TR", "AE"]
    }
    
    # Suffix to Country
    SUFFIX_MAP = {
        ".DE": "DE", ".F": "DE", ".MU": "DE", ".BE": "DE", ".HA": "DE", ".DU": "DE",
        ".L": "GB", ".AS": "NL", ".PA": "FR", ".MI": "IT", ".MC": "ES",
        ".ST": "SE", ".OL": "NO", ".CO": "DK", ".HE": "FI",
        ".HK": "HK", ".T": "JP", ".KS": "KR", ".SS": "CN", ".SZ": "CN",
        ".AX": "AU", ".TO": "CA", ".SW": "CH",
        ".PR": "CZ"
    }

    COUNTRY_NAME_MAP = {
        "United States": "US", "USA": "US",
        "China": "CN", "Hong Kong": "HK",
        "Germany": "DE", "United Kingdom": "GB", "Great Britain": "GB", "UK": "GB",
        "France": "FR", "Italy": "IT", "Spain": "ES", "Netherlands": "NL",
        "Sweden": "SE", "Norway": "NO", "Denmark": "DK", "Finland": "FI",
        "Switzerland": "CH", "Canada": "CA", "Australia": "AU", "Japan": "JP",
        "South Korea": "KR", "Taiwan": "TW", "India": "IN", "Singapore": "SG",
        "Brazil": "BR", "Mexico": "MX", "South Africa": "ZA",
        "Cayman Islands": "CN" # Tax haven, usually Chinese tech (BABA, JD, BIDU)
    }

    # Manual Overrides for specific tickers (when ISIN/Live data fails or is misleading)
    TICKER_OVERRIDE = {
        "BABA": "CN", "9988.HK": "CN",
        "JD": "CN", "BIDU": "CN",
        "PDD": "CN", "TCEHY": "CN",
        "TSM": "TW", 
        "NIO": "CN", "XPEV": "CN", "LI": "CN",
        "BYDDY": "CN"
    }

    ENABLE_CACHE = True

    def _detect_country(self, symbol: str, isin: str = "", live_country_name: str = None, metadata_override: str = None) -> str:
        # 1. Metadata Override (Highest Priority - User Defined)
        if metadata_override and len(metadata_override) == 2:
            return metadata_override.upper()

        # 2. Manual System Override (Known ADRs/Exceptions)
        clean_symbol = symbol.split('.')[0]
        if symbol in self.TICKER_OVERRIDE:
             return self.TICKER_OVERRIDE[symbol]
        if clean_symbol in self.TICKER_OVERRIDE:
             return self.TICKER_OVERRIDE[clean_symbol]

        # 3. Live Data Name (Economic Reality - HQ)
        if live_country_name:
            iso = self.COUNTRY_NAME_MAP.get(live_country_name)
            if iso: return iso

        # 4. ISIN (Legal Domicile Fallback)
        if isin and len(isin) >= 2:
            return isin[:2].upper()
            
        # 5. Ticker Suffix Fallback (Exchange Location)
        for suffix, country in self.SUFFIX_MAP.items():
            if symbol.endswith(suffix):
                return country
        
        # 6. Legacy Market Mapping
        if hasattr(self, 'market_data') and hasattr(self.market_data, 'MAPPING'):
            mapped = self.market_data.MAPPING.get(symbol)
            if mapped:
                for suffix, country in self.SUFFIX_MAP.items():
                    if mapped.endswith(suffix):
                        return country
                        
        return "Unknown"

    def _detect_region(self, country: str) -> str:
        for region, countries in self.REGIONS.items():
            if country in countries:
                return region
        return "Other"

    def _get_files_hash(self, merged_data: Dict[str, pd.DataFrame]) -> str:
        """
        Generates a simple hash based on the content length of DataFrames.
        In a real scenario, we might check file mtimes before parsing, 
        but here we receive already parsed data.
        Optimization: The Controller should ideally check mtimes BEFORE parsing.
        However, since we are inside Engine, let's optimize the Reconstruction step.
        To do this effectively without re-parsing, we need to know if the inputs changed.
        The `parser` provides fresh DFs every time currently. 
        
        Let's rely on a simpler mechanic: The caller (main.py) should ideally handle file changes.
        But sticking to the plan: We caching the result of RECONSTRUCTION.
        We can hash the input DataFrames or check if they are identical.
        Hashing DFs can be slow. 
        
        Alternative: main.py passes `file_signature` (hash of mtimes).
        Let's assume for now we don't have that signature yet, so we'll implement
        a lightweight check or we modify main.py to pass it.
        
        Actually, let's modify `process` to accept `files_hash` optional argument.
        """
        # For now, simplistic length check + head check as proxy for hash
        s = ""
        if 'Trades' in merged_data:
            df = merged_data['Trades']
            s += f"T:{len(df)}"
        return s

    async def process(self, merged_data: Dict[str, pd.DataFrame], metadata: Dict[str, Any], files_hash: str = "") -> Dict[str, Any]:
        """
        Main entry point for portfolio calculation.
        """
    async def process(self, merged_data: Dict[str, pd.DataFrame], metadata: Dict[str, Any], files_hash: str = "") -> Dict[str, Any]:
        """
        Main entry point for portfolio calculation.
        """
        # 1. Setup Data
        df_trades = merged_data.get('Trades', pd.DataFrame())
        df_fin_info = merged_data.get('Financial Instrument Information', pd.DataFrame())
        df_open_pos = merged_data.get('Open Positions', pd.DataFrame())
        
        # 2. Reconstruct Portfolio (Cached)
        # If files_hash is provided and matches, we skip reconstruction
        if files_hash and files_hash == self.cache_files_hash and self.cached_reconstructed is not None:
             reconstructed = self.cached_reconstructed
        else:
             reconstructed = self.reconstructor.reconstruct(df_trades, df_fin_info)
             # Update Cache
             if files_hash:
                 self.cache_files_hash = files_hash
                 self.cached_reconstructed = reconstructed
        
        # 3. Determine Report Date for FX
        report_date = self._get_report_date(merged_data.get('Statement', pd.DataFrame()))
        
        # 4. Fetch Live Market Data
        all_symbols = df_open_pos['Symbol'].dropna().unique().tolist() if not df_open_pos.empty else []
        live_data = await self.market_data.get_live_prices(all_symbols)

        
        # 5. Pre-fetch FX Rates (Hybrid: Live Yahoo + Historical CNB)
        today = datetime.now().strftime("%Y-%m-%d")
        fx_keys_hist = []
        fx_tasks_hist = []
        
        # Identify currencies needed
        currencies_live = set(["USD", "EUR", "GBP", "HKD", "SEK", "PLN", "AUD", "CAD", "JPY", "CHF", "CNY", "SGD"]) # Defaults
        
        # Scan positions
        if not df_open_pos.empty:
            for _, row in df_open_pos.iterrows():
                symbol = row.get('Symbol')
                cur = str(row.get('Currency', 'USD')).strip()
                if not cur: continue
                
                # Check if we have live price for this symbol
                if symbol in live_data:
                    currencies_live.add(cur)
                else:
                    # Need historical rate for report_date
                    if cur != 'CZK':
                         fx_keys_hist.append((cur, report_date, 'CZK'))
                    if cur != 'USD':
                         fx_keys_hist.append((cur, report_date, 'USD'))

        # Scan forex (Always Live for Cash)
        df_forex = merged_data.get('Forex Balances', pd.DataFrame())
        if not df_forex.empty:
             for _, row in df_forex.iterrows():
                 if 'Forex' in str(row.get('Asset Category', '')):
                     cur = str(row.get('Description', '')).strip()
                     if cur: currencies_live.add(cur)

        # A) Fetch Live Rates (Yahoo)
        live_fx_map = await self.market_data.get_live_fx_rates(list(currencies_live), "CZK")
        
        # Fallback for missing Live Rates (Yahoo often fails for CZK pairs like HKDCZK=X)
        missing_live = [c for c in currencies_live if c not in live_fx_map and c != 'CZK']
        if missing_live:
            # We fetch 'today' rate from ForexService (ForexService handles the direct fallback to Frankfurter)
            fallback_tasks = [self.forex.get_rate_async(c, today, 'CZK') for c in missing_live]
            fallback_results = await asyncio.gather(*fallback_tasks)
            for i, cur in enumerate(missing_live):
                if fallback_results[i] > 0:
                    live_fx_map[cur] = fallback_results[i]

        fx_map = {} 
        usd_rate = live_fx_map.get('USD') or 22.0
        
        # Populate Map for Today
        for cur, rate_czk in live_fx_map.items():
            fx_map[(cur, today, 'CZK')] = rate_czk
            if usd_rate > 0:
                fx_map[(cur, today, 'USD')] = rate_czk / usd_rate
        
        # B) Fetch Historical Rates (CNB)
        fx_keys_hist = list(set(fx_keys_hist))
        for k in fx_keys_hist:
            fx_tasks_hist.append(self.forex.get_rate_async(*k))
            
        if fx_tasks_hist:
            hist_results = await asyncio.gather(*fx_tasks_hist)
            for i, key in enumerate(fx_keys_hist):
                fx_map[key] = hist_results[i]
            
        # 6. Process Positions
        positions = self._process_positions(df_open_pos, reconstructed, live_data, metadata, report_date, fx_map)
        
        # 7. Calculate KPIs
        cash_balances = self._get_cash_balances(df_forex, fx_map)
        
        # 7b. Extract Accruals (from Net Asset Value)
        # We look for "Interest Accruals" and "Dividend Accruals" in Statement section or NAV section
        # Parser seems to separate "Net Asset Value" into its own section? 
        # Parser output keys: 'Statement', 'Account Information', 'Net Asset Value', ...
        df_nav = merged_data.get('Net Asset Value', pd.DataFrame())
        accruals_usd = self._get_accruals_total(df_nav)

        kpis = self._calculate_kpis(positions, cash_balances, report_date, fx_map, accruals_usd)

        kpis['cash_balances'] = cash_balances # Pass breakdown to frontend
        
        # 8. Fetch Current FX Rates (Display Only - Cached)
        display_currencies = ["USD", "EUR", "GBP", "HKD", "SEK", "PLN", "AUD", "CAD", "JPY", "CHF", "CNY", "SGD"]
        fx_rates = {}
        for curr in display_currencies:
            fx_rates[curr] = fx_map.get((curr, today, "CZK"), 1.0)

        # 8. Final Response Formatting
        response = {
            "kpi": kpis,
            "positions": sorted(positions, key=lambda x: x['market_value_czk'], reverse=True),
            "fx_rates": fx_rates,
            "status": "success" if positions else "empty"
        }
        
        # Recalc Weights (IBKR style: % of Net Liq)
        net_liq_czk = kpis.get("net_liquidity_czk", 0)
        if net_liq_czk > 0:
            for p in response["positions"]:
                p["pct_portfolio"] = (p["market_value_czk"] / net_liq_czk) * 100

        return self._sanitize(response)

    def _get_report_date(self, df_stmt: pd.DataFrame) -> str:
        """Extracts the end date of the report for consistent FX conversion."""
        if df_stmt.empty:
            return datetime.now().strftime("%Y-%m-%d")
        
        for _, row in df_stmt.iterrows():
            row_str = row.astype(str).str.cat(sep=' ')
            if 'Period' in row_str:
                for val in row.values:
                    val_str = str(val)
                    if '-' in val_str and ',' in val_str: # e.g. "January 01, 2024 - December 31, 2024"
                        try:
                            end_part = val_str.split('-')[-1].strip()
                            dt = datetime.strptime(end_part, "%B %d, %Y")
                            return dt.strftime("%Y-%m-%d")
                        except: pass
        return datetime.now().strftime("%Y-%m-%d")

    def _process_positions(self, df_open_pos: pd.DataFrame, reconstructed: Dict, 
                          live_data: Dict, metadata: Dict, report_date: str, fx_map: Dict) -> List[Dict]:
        positions = []
        today = datetime.now().strftime("%Y-%m-%d")

        if df_open_pos.empty:
            return []

        for _, row in df_open_pos.iterrows():
            symbol = row.get('Symbol')
            if not symbol: continue
            
            # ... (Rest of loop setup)
            cost_basis_czk = None
            cost_basis_native = None
            qty = self._parse_float(row.get('Quantity'))
            if qty == 0: continue
            
            currency = str(row.get('Currency', 'USD')).strip()
            recon_entry = reconstructed.get(symbol)
            
            live_entry = live_data.get(symbol)
            if live_entry:
                price = live_entry.get('price', 0.0)
                price_source = "Live"
                fx_date = today
                name = live_entry.get('name', symbol)
            else:
                price = self._parse_float(row.get('Close Price'))
                price_source = "Report"
                fx_date = report_date
                name = symbol

            if recon_entry:
                currency = recon_entry['currency']
                recon_qty = recon_entry['quantity']
                if abs(recon_qty) > 0.000001:
                    avg_cost_czk = recon_entry['cost_basis_czk'] / recon_qty
                    cost_basis_czk = qty * avg_cost_czk
                else: cost_basis_czk = 0.0
            else:
                raw_cost = self._parse_float(row.get('Cost Basis'))
                cost_basis_native = raw_cost
            
            # Market Val & FX (Use Map)
            # Default to 1.0 if not found (or 0.0 + error log?)
            # If same currency, logic returns 1.0? 
            # Our pre-fetcher didn't add tasks for same currency.
            # So we handle identity here.
            
            if currency == 'CZK': fx_czk = 1.0
            else: fx_czk = fx_map.get((currency, fx_date, 'CZK'), 0.0)
            
            if currency == 'USD': fx_usd = 1.0
            else: fx_usd = fx_map.get((currency, fx_date, 'USD'), 0.0)
            
            # If rate is 0 because of error, fallback to sync? No, that defeats point.
            # If 0, try fetching sync? Dangerous. Assume strict pre-fetch.
            # If pre-fetch failed, it's 0.

            # Detect if this is an option
            is_option = 'Option' in str(row.get('Asset Category', '')) or \
                        ((symbol.endswith('-P') or symbol.endswith('-C')) and len(symbol) > 15)
            
            # Get multiplier (for options: 100, for stocks: 1)
            mult = self._parse_float(row.get('Mult', 1))
            if mult == 0: mult = 1.0  # Fallback
            
            # Calculate market value
            # For options: invert sign because qty represents position direction
            # - Long option (qty > 0): You paid premium → negative value
            # - Short option (qty < 0): You received premium → negative value (liability)
            if is_option:
                market_val_native = -(qty * price * mult)
            else:
                market_val_native = qty * price * mult
                
            market_val_czk = market_val_native * fx_czk
            market_val_usd = market_val_native * fx_usd

            # Debug logging removed
            
            # Convert Cost Basis if it came from Native
            if cost_basis_czk is None:
                 # If we didn't get it from Reconstructor (Shadow Ledger)
                 cost_basis_czk = cost_basis_native * fx_czk 
            else:
                 # If we got CZK basis from recon, we back-calculate native for % calc consistency
                 # Or we should store native basis in recon too? For now, approximation:
                 # Actually, if we have recon, we don't always have native basis stored.
                 # Let's trust the 'Cost Basis' from CSV as 'cost_basis_native' fallback for % calc if recon fails?
                 # Better: derived native cost basis = cost_basis_czk / fx_rate_at_buy_time ... hard.
                 # SIMPLE FIX: If we have row['Cost Basis'], use it as native_basis.
                 pass

            if not cost_basis_native and qty != 0:
                 # Try to infer from CSV
                 cost_basis_native = self._parse_float(row.get('Cost Basis', 0))

            # P&L
            unrealized_pnl_czk = market_val_czk - cost_basis_czk
            
            # Use NATIVE values for % return to exclude FX impact
            # This matches "Price vs Avg Price" expectation
            native_pnl = market_val_native - cost_basis_native
            pnl_percent = (native_pnl / cost_basis_native * 100) if cost_basis_native and cost_basis_native != 0 else 0
            
            if 'P911' in symbol or 'BOSS' in symbol:
                pass 
                # print(f"DEBUG {symbol}: Qty={qty} Price={price} FX={fx_czk}")

            
            # Metadata & Instructions
            # Normalize symbol for lookup (strip suffixes like d, s used in some IBKR reports)
            norm_symbol = symbol.strip()
            # If it ends with lowercase d or s, strip it (for BOSSd, EVOs, P911d, etc.)
            if len(norm_symbol) > 1 and norm_symbol[-1] in ('d', 's'):
                potential = norm_symbol[:-1]
                # Check if the rest looks like a ticker (mostly uppercase/digits)
                if any(c.isupper() for c in potential):
                    norm_symbol = potential
            
            # Also handle common exchange suffixes if metadata is generic
            base_symbol = norm_symbol.split('.')[0]
            
            meta = metadata.get(symbol, {})
            if not meta: meta = metadata.get(norm_symbol, {})
            if not meta: meta = metadata.get(base_symbol, {})
            
            
            instr_data = self._get_instruction(price, meta)
            
            # Assets Exclusion (User wants to see all options)
            is_excluded = False
            # Country & Region
            raw_isin = row.get('ISIN')
            if isinstance(raw_isin, float) and math.isnan(raw_isin):
                raw_isin = ''
            isin = str(raw_isin) if raw_isin else (live_entry.get('isin', '') if live_entry else '')
            
            # Options Handling
            if 'Option' in str(row.get('Asset Category', '')) or ((symbol.endswith('-P') or symbol.endswith('-C')) and len(symbol) > 15):
                country = "N/A"
                region = "Derivatives" 
            else:
                live_country = live_entry.get('country') if live_entry else None
                meta_override = meta.get('country_override')
                country = self._detect_country(symbol, isin, live_country, meta_override)
                
                # Currency Fallbacks if Country Unknown
                if country == "Unknown":
                    if currency == "USD": country = "US"
                    elif currency == "GBP": country = "GB"
                    elif currency == "EUR": country = "DE" # Generic Eurozone
                    elif currency == "CZK": country = "CZ"
                    elif currency == "HKD": country = "HK"
                    elif currency == "SEK": country = "SE"
                    elif currency == "PLN": country = "PL"
                    elif currency == "AUD": country = "AU"
                    elif currency == "CAD": country = "CA"
                    elif currency == "JPY": country = "JP"
                    elif currency == "CHF": country = "CH"
                    elif currency == "CNY": country = "CN"
                    elif currency == "SGD": country = "SG"
                
                region = self._detect_region(country)
            
            # ... existing logic ...

            positions.append({
                "id": symbol, "symbol": symbol, "name": name, "quantity": qty,
                "current_price": price, "currency": currency,
                "market_value_native": market_val_native,
                "market_value_czk": market_val_czk, "market_value_usd": market_val_usd,
                "cost_basis_czk": cost_basis_czk, "unrealized_pnl_czk": unrealized_pnl_czk,
                "unrealized_pnl_native": native_pnl,
                "pnl_percent": pnl_percent, "is_excluded": is_excluded,
                "average_buy_price": self._parse_float(row.get('Cost Basis', 0)) / qty if qty else 0,
                "price_source": price_source, "recon_match": bool(recon_entry),
                **meta, **instr_data,
                "year_high": live_entry.get('high52') if live_entry else None,
                "year_low": live_entry.get('low52') if live_entry else None,
                "country": country, "region": region
            })

        return positions

    def _get_accruals_total(self, df_nav: pd.DataFrame) -> float:
        """Parse Interest and Dividend Accruals from Net Asset Value section."""
        total_accruals = 0.0
        if df_nav.empty:
            return 0.0
            
        try:
            # Clean columns? self.parser cleans them usually.
            # Columns usually: Asset Class, Prior Total, Current Long, Current Short, Current Total, Change
            # We want 'Current Total' where 'Asset Class' is 'Interest Accruals' or 'Dividend Accruals'
            
            # Helper to parse float safely
            def parse_val(val):
                if isinstance(val, (int, float)): return float(val)
                if isinstance(val, str): return float(val.replace(',', ''))
                return 0.0

            for _, row in df_nav.iterrows():
                asset_class = str(row.get('Asset Class', ''))
                if 'Interest Accruals' in asset_class or 'Dividend Accruals' in asset_class:
                     val = parse_val(row.get('Current Total', 0))
                     total_accruals += val
        except Exception as e:
            print(f"Error parsing accruals: {e}")
            
        return total_accruals

    def _calculate_kpis(self, positions: List[Dict], cash_balances: List[Dict], report_date: str, fx_map: Dict, accruals_usd: float = 0.0) -> Dict[str, Any]:
        active = [p for p in positions if not p['is_excluded']]
        
        # Net Market Value (traditional sum, short options reduce value)
        total_market_czk = sum(p['market_value_czk'] for p in active)
        total_market_usd = sum(p['market_value_usd'] for p in active)
        total_cost_czk = sum(p['cost_basis_czk'] for p in active)
        
        # Gross Position Value (absolute sum)
        gross_position_czk = sum(abs(p['market_value_czk']) for p in positions)
        gross_position_usd = sum(abs(p['market_value_usd']) for p in positions)
        
        # Calculate Total Cash
        today = datetime.now().strftime("%Y-%m-%d")
        total_cash_usd = 0.0
        total_cash_czk = 0.0
        
        for cb in cash_balances:
            total_cash_usd += cb['value_usd']
            total_cash_czk += cb['value_czk']
            
            # Margin Interest
            if cb['amount'] < 0:
                ann_cost, daily_cost, effective_rate = self.margin.calculate_daily_cost(cb['currency'], cb['amount'])
                cb['daily_interest_native'] = daily_cost
                cb['effective_rate'] = effective_rate
                
                if cb['currency'] == 'CZK': fx_czk = 1.0
                else: fx_czk = fx_map.get((cb['currency'], today, 'CZK'), 1.0)
                
                if cb['currency'] == 'USD': fx_usd = 1.0
                else: fx_usd = fx_map.get((cb['currency'], today, 'USD'), 1.0)

                cb['daily_interest_czk'] = daily_cost * fx_czk
                cb['daily_interest_usd'] = daily_cost * fx_usd
            else:
                cb['daily_interest_czk'] = 0
                cb['daily_interest_usd'] = 0
                cb['effective_rate'] = 0.0

        # Net Liquidity Value
        # IBKR Formula: Cash + Stock + Options + Accruals
        
        # Convert Accruals to CZK (approx using avg rate implied by portfolio? or just USD/CZK live)
        # We assume accruals_usd is in USD (Base Currency)
        fx_usd_czk = fx_map.get(('USD', today, 'CZK'), 22.0) 
        if fx_usd_czk == 0: fx_usd_czk = 22.0
            
        accruals_czk = accruals_usd * fx_usd_czk
        
        nav_usd = total_market_usd + total_cash_usd + accruals_usd
        nav_czk = total_market_czk + total_cash_czk + accruals_czk
        
        # Leverage = Gross Exposure / Net Liq (IBKR style)
        leverage = gross_position_usd / nav_usd if nav_usd != 0 else 0
        pct_invested = (total_market_czk / nav_czk * 100) if nav_czk != 0 else 0

        return {
            "net_liquidity_usd": nav_usd,
            "net_liquidity_czk": nav_czk,
            "cash_balance_usd": total_cash_usd,
            "pct_invested": pct_invested,
            "total_pnl_czk": total_market_czk - total_cost_czk, 
            "total_market_czk": total_market_czk,
            "gross_position_usd": gross_position_usd,
            "gross_position_czk": gross_position_czk,
            "leverage": leverage,
            "report_date": report_date
        }


    def _get_cash_balances(self, df_forex: pd.DataFrame, fx_map: Dict) -> List[Dict]:
        """
        Extracts cash balances from 'Forex Balances' section.
        Returns: [ { currency: 'EUR', amount: 500, value_czk: 12500, value_usd: 550 } ]
        """
        balances = []
        today = datetime.now().strftime("%Y-%m-%d")
        
        if df_forex.empty:
            return []
            
        # Iterate rows where Asset Category is Forex
        # Based on debug: Asset Category, Currency (Base), Description (Actual Curr), Quantity (Amount)
        
        for _, row in df_forex.iterrows():
            cat = str(row.get('Asset Category', ''))
            if 'Forex' not in cat: continue
            
            # IBKR 'Forex Balances' section:
            # Description = The Currency code (e.g. 'CZK', 'EUR', 'USD')
            # Quantity = The Balance amount
            
            currency = str(row.get('Description', '')).strip()
            amount = self._parse_float(row.get('Quantity', 0))
            
            if not currency or abs(amount) < 0.01: continue
            
            # Convert to normalized values
            if currency == 'CZK': fx_czk = 1.0
            else: fx_czk = fx_map.get((currency, today, 'CZK'), 1.0)
            
            if currency == 'USD': fx_usd = 1.0
            else: fx_usd = fx_map.get((currency, today, 'USD'), 1.0)
            
            balances.append({
                "currency": currency,
                "amount": amount,
                "value_czk": amount * fx_czk,
                "value_usd": amount * fx_usd
            })
            
        return sorted(balances, key=lambda x: x['currency'])

    def _get_instruction(self, price: float, meta: Dict) -> Dict:
        buy_zone = meta.get('buy_zone')
        sell_zone = meta.get('sell_zone')
        instr = "Hold"
        pct_buy, pct_sell = 0.0, 0.0

        if price > 0:
            if buy_zone:
                bz = float(buy_zone)
                pct_buy = (price - bz) / price * 100
                if price <= bz: instr = "Buy"
            if sell_zone:
                sz = float(sell_zone)
                pct_sell = (sz - price) / price * 100
                if price >= sz: instr = "Sell"
        
        return {"instruction": instr, "pct_to_buy": pct_buy, "pct_to_sell": pct_sell}

    def _parse_float(self, val: Any) -> float:
        try: return float(str(val).replace(',', ''))
        except: return 0.0

    def _sanitize(self, obj: Any) -> Any:
        if isinstance(obj, float):
            return None if math.isnan(obj) or math.isinf(obj) else obj
        if isinstance(obj, dict): return {k: self._sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list): return [self._sanitize(v) for v in obj]
        return obj
