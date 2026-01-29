import yfinance as yf
import asyncio
import time
import os
import json
import functools
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

class MarketDataService:
    def __init__(self, cache_file="backend/data/market_cache.json", cache_expiry_minutes=5):
        # 1. Setup Cache Path
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if os.path.isabs(cache_file):
            self.cache_file = cache_file
        else:
            self.cache_file = os.path.join(base_dir, cache_file)
            
        self.metadata_file = os.path.join(base_dir, "backend/data/metadata.json")
            
        self.cache_expiry_minutes = cache_expiry_minutes
        self.last_request_time: float = 0
        self.MIN_DELAY = 1.0  # Seconds between requests
        
        # 2. Load Cache
        self.cache = self._load_cache()
        self.metadata = self._load_metadata()

        # 3. Ticker Mapping (IBKR -> YFinance)
        self.MAPPING = {
            'ZAL': 'ZAL.DE',
            'WIZZ': 'WIZZ.L',
            'TUI1': 'TUI1.DE',
            'BOSS': 'BOSS.DE',
            'P911': 'P911.DE',
            'ADS': 'ADS.DE',
            'EVO': 'EVO.ST'
        }

    def _load_metadata(self) -> Dict:
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except: return {}
        return {}

    def _load_cache(self) -> Dict:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading cache: {e}")
                return {}
        return {}

    def _save_cache(self):
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save market cache: {e}")

    def _sanitize_symbol(self, symbol: str) -> str:
        if symbol in self.MAPPING:
            return self.MAPPING[symbol]
        
        # 1. Try Option Conversion (IBKR to Yahoo)
        # Format: TICKER DDMMMYY STRIKE C/P (e.g. SOFI 20FEB26 26 P)
        import re
        opt_match = re.match(r'^(\w+)\s+(\d{2})([A-Z]{3})(\d{2})\s+([\d\.]+)\s+([CP])$', symbol.strip())
        if opt_match:
            ticker, day, mon_str, year, strike, otype = opt_match.groups()
            months = {'JAN':'01','FEB':'02','MAR':'03','APR':'04','MAY':'05','JUN':'06',
                      'JUL':'07','AUG':'08','SEP':'09','OCT':'10','NOV':'11','DEC':'12'}
            month = months.get(mon_str.upper(), '01')
            
            # Strike formatting: 8 digits (5 integer, 3 decimal)
            try:
                strike_val = int(float(strike) * 1000)
                strike_str = str(strike_val).zfill(8)
                return f"{ticker}{year}{month}{day}{otype}{strike_str}"
            except: pass

        return symbol.replace(' ', '-')

    async def get_live_prices(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        results = {}
        to_fetch = []
        now = datetime.now()

        # Initialize failure tracking if not present
        if not hasattr(self, 'failed_symbols'):
            self.failed_symbols = {} # {symbol: expiry_timestamp}

        # 1. Check Cache & Filter failures
        for sym in symbols:
            # Skip recently failed symbols (1 hour cooldown)
            fail_expiry = self.failed_symbols.get(sym)
            if fail_expiry and time.time() < fail_expiry:
                continue

            entry = self.cache.get(sym)
            if entry and 'timestamp' in entry and 'data' in entry:
                try:
                    last_updated = datetime.fromisoformat(entry['timestamp'])
                    if (now - last_updated) < timedelta(minutes=self.cache_expiry_minutes):
                        results[sym] = entry['data']
                        continue
                except: pass
            to_fetch.append(sym)

        if not to_fetch:
            return results

        # 2. Fetch from yfinance
        loop = asyncio.get_event_loop()
        sanitized_map = {s: self._sanitize_symbol(s) for s in to_fetch}
        sanitized_list = list(sanitized_map.values())
        
        try:
            # Throttle
            elapsed = time.time() - self.last_request_time
            if elapsed < self.MIN_DELAY:
                await asyncio.sleep(self.MIN_DELAY - elapsed)

            # Tickers batch fetch (fast_info is available on the Tickers object)
            tickers_obj = await loop.run_in_executor(None, lambda: yf.Tickers(" ".join(sanitized_list)))
            
            # We will process each ticker with a task to fetch details if needed
            async def process_ticker(orig, san):
                try:
                    t = tickers_obj.tickers.get(san)
                    if not t: return None
                    
                    data = {}
                    is_option = len(san) > 15 and any(c in san for c in ['C', 'P'])
                    is_forex = san.endswith('=X')

                    # 1. Try fast_info (Price & Basic Info)
                    try:
                        fi = t.fast_info
                        data['price'] = fi.last_price
                        data['high52'] = fi.year_high
                        data['low52'] = fi.year_low
                        currency = getattr(fi, 'currency', None)
                    except:
                        currency = None

                    # 2. Fallbacks for Price
                    if not data.get('price'):
                        hist = await loop.run_in_executor(None, lambda: t.history(period="1d"))
                        if not hist.empty:
                            data['price'] = hist['Close'].iloc[-1]
                    
                    # 3. Metadata (Name, Country)
                    # Skip slow t.info for options and forex
                    if is_option:
                        data['name'] = orig # Keep original string for options
                        data['country'] = "N/A"
                    elif is_forex:
                        data['name'] = f"Currency Pair {orig}"
                        data['country'] = "N/A"
                    else:
                        # OPTIMIZATION: Use local metadata instead of slow t.info
                        # Try to get Name/Country from our metadata.json first
                        # Note: we use 'orig' symbol for lookup as key in metadata usually matches that
                        meta_entry = self.metadata.get(orig, {})
                        
                        data['name'] = meta_entry.get('name') or meta_entry.get('longName') 
                        data['country'] = meta_entry.get('country')
                        
                        # Fallback if missing
                        if not data['name']:
                             # Try t.fast_info currency as a hint? No, just use symbol
                             data['name'] = orig
                             
                        if not data['country']:
                             data['country'] = "Unknown"

                        if not currency: 
                            currency = getattr(fi, 'currency', 'USD') # Default to USD if unknown

                    # Normalization
                    if currency == 'GBp' and data.get('price'):
                        for key in ['price', 'high52', 'low52']:
                            if data.get(key): data[key] /= 100.0

                    if data.get('price') and not (isinstance(data['price'], float) and (math.isnan(data['price']) or math.isinf(data['price']))):
                        return orig, data
                    else:
                        # Mark as failed to avoid retrying every request
                        self.failed_symbols[orig] = time.time() + 3600
                        return None
                except Exception as e:
                    # print(f"Error processing {orig}: {e}")
                    self.failed_symbols[orig] = time.time() + 3600
                    return None

            # Run all ticker processing in parallel
            import math # for isinf/isnan check if not imported
            tasks = [process_ticker(orig, san) for orig, san in sanitized_map.items()]
            processed_results = await asyncio.gather(*tasks)

            for item in processed_results:
                if item:
                    orig, data = item
                    results[orig] = data
                    self.cache[orig] = {
                        'data': data,
                        'timestamp': now.isoformat()
                    }

            self._save_cache()
            self.last_request_time = time.time()
            
        except Exception as e:
            print(f"Batch fetch error: {e}")

        return results

    async def get_ohlcv(self, symbol: str, range_period: str) -> Dict[str, Any]:
        """
        Fetches OHLCV data for detailed charts.
        """
        now = time.time()
        cache_key = f"ohlcv_{symbol}_{range_period}"
        ttl = 60 if range_period in ['1d', '1w'] else 3600

        # Check Cache
        entry = self.cache.get(cache_key)
        if entry and now - entry.get('timestamp_unix', 0) < ttl:
            return entry['data']

        # Map range to yf params
        yf_params = {
            "1d": {"period": "1d", "interval": "5m"},
            "1w": {"period": "5d", "interval": "15m"},
            "1m": {"period": "1mo", "interval": "1d"},
            "3m": {"period": "3mo", "interval": "1d"},
            "6m": {"period": "6mo", "interval": "1d"},
            "1y": {"period": "1y", "interval": "1d"},
            "5y": {"period": "5y", "interval": "1wk"},
            "max": {"period": "max", "interval": "1wk"},
        }
        params = yf_params.get(range_period, {"period": "1y", "interval": "1d"})

        # Throttle
        elapsed = now - self.last_request_time
        if elapsed < self.MIN_DELAY:
            await asyncio.sleep(self.MIN_DELAY - elapsed)

        try:
            loop = asyncio.get_event_loop()
            sanitized = self._sanitize_symbol(symbol)
            ticker = await loop.run_in_executor(None, yf.Ticker, sanitized)
            
            fetch_func = functools.partial(ticker.history, **params)
            hist = await loop.run_in_executor(None, fetch_func)
            
            if hist.empty:
                return {"error": "No data found"}
            
            is_intraday = range_period in ['1d', '1w']
            candles = []
            volumes = []
            
            for date, row in hist.iterrows():
                time_val = int(date.timestamp()) if is_intraday else date.strftime('%Y-%m-%d')
                candles.append({
                    "time": time_val,
                    "open": row['Open'], "high": row['High'],
                    "low": row['Low'], "close": row['Close']
                })
                is_up = row['Close'] >= row['Open']
                color = 'rgba(34, 197, 94, 0.56)' if is_up else 'rgba(239, 68, 68, 0.56)'
                volumes.append({"time": time_val, "value": row['Volume'], "color": color})

            result = {"symbol": symbol, "candles": candles, "volume": volumes}
            
            self.cache[cache_key] = {
                "timestamp_unix": time.time(),
                "data": result
            }
            self._save_cache()
            self.last_request_time = time.time()
            return result
            
        except Exception as e:
            print(f"Error fetching OHLCV {symbol}: {e}")
            return {"error": str(e)}

    async def get_watchlist_data(self, symbol: str, range_period: str = "1m") -> Dict[str, Any]:
        """
        Fetches lightweight data for watchlist (Price + %Change + Sparkline).
        range_period: 1d, 1w, 1m, 3m, 1y
        """
        try:
            loop = asyncio.get_event_loop()
            sanitized = self._sanitize_symbol(symbol)
            
            # Map Range
            # 1d=5m, 1w=15m, 1m=1d, 3m=1d, 1y=1d
            period = "1mo"
            interval = "1d"
            
            if range_period == "1d":
                period = "1d"
                interval = "5m"
            elif range_period == "1w":
                period = "5d"
                interval = "15m"
            elif range_period == "3m":
                period = "3mo"
                interval = "1d"
            elif range_period == "1y":
                period = "1y"
                interval = "1d"
            # Default "1m" is "1mo"
            
            # Fetch history
            ticker = await loop.run_in_executor(None, yf.Ticker, sanitized)
            hist = await loop.run_in_executor(None, lambda: ticker.history(period=period, interval=interval))
            
            if hist.empty:
                return {"symbol": symbol, "error": "No data"}
                
            # Current Price & Stats
            current_price = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            
            change_percent = 0.0
            if prev_close > 0:
                change_percent = ((current_price - prev_close) / prev_close) * 100
                
            # Sparkline Data (Simplify to date/close)
            sparkline = []
            for date, row in hist.iterrows():
                # Format: "YYYY-MM-DD" is enough for sparkline usually, or ISO
                sparkline.append({
                    "date": date.strftime('%Y-%m-%d'),
                    "close": float(row['Close'])
                })
                
            return {
                "symbol": symbol,
                "price": float(current_price),
                "currency": "USD", # TODO: Get from fast_info if needed, keeping simple
                "change_percent": float(change_percent),
                "history": sparkline
            }
            
        except Exception as e:
            print(f"Error fetching watchlist data {symbol}: {e}")
            return {"symbol": symbol, "error": str(e)}

    # Compatibility shim for blocking calls
    def get_history(self, symbol: str, period: str = "1y") -> Dict[str, Any]:
        # This is a bit tricky in async. For now, we'll keep it as a wrapper if needed, 
        # but the app should move to async get_ohlcv.
        # I'll implement a simple sync version for safety.
        sanitized = self._sanitize_symbol(symbol)
        t = yf.Ticker(sanitized)
        hist = t.history(period=period)
        if hist.empty: return {"error": "No data found"}
        
        chart_data = [{"date": d.strftime('%Y-%m-%d'), "close": round(row['Close'], 2)} for d, row in hist.iterrows()]
        return {
            "symbol": symbol,
            "price": round(hist['Close'].iloc[-1], 2),
            "history": chart_data
        }

    async def get_live_fx_rates(self, currencies: List[str], target: str = "CZK") -> Dict[str, float]:
        """
        Fetches live FX rates from Yahoo Finance for given currencies vs target.
        Returns: {'USD': 23.50, 'EUR': 25.20, ...}
        """
        if not currencies: return {}
        
        # 1. Map to Yahoo Tickers
        # Format: CURRENCY + TARGET + "=X" (e.g. USDCZK=X)
        ticker_map = {} # {currency: yahoo_symbol}
        # Filter duplicates and target
        unique_curs = set([c.upper() for c in currencies if c.upper() != target])
        
        for cur in unique_curs:
            symbol = f"{cur}{target}=X"
            ticker_map[cur] = symbol
            
        yahoo_symbols = list(ticker_map.values())
        if not yahoo_symbols: return {target: 1.0}

        # 2. Fetch Prices 
        # Uses existing get_live_prices which handles 5min cache & throttling
        raw_data = await self.get_live_prices(yahoo_symbols)
        
        # 3. Format Result
        rates = {}
        rates[target] = 1.0
        
        for cur, symbol in ticker_map.items():
            entry = raw_data.get(symbol)
            if entry and entry.get('price'):
                rates[cur] = float(entry['price'])
        
        return rates
