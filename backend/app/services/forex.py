import requests
import json
import os
from datetime import datetime
import time

class ForexService:
    def __init__(self, cache_file="backend/data/forex_cache.json"):
        # Ensure absolute path or correct relative path
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        if os.path.isabs(cache_file):
            self.cache_file = cache_file
        else:
            self.cache_file = os.path.join(base_dir or os.getcwd(), cache_file)
            
        self.cache = self._load_cache()
        self.api_url = "https://api.frankfurter.app"

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_cache(self):
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save forex cache: {e}")

    def get_rate(self, currency: str, date_str: str, target_currency: str = "CZK") -> float:
        """
        Returns rate to convert 1 unit of 'currency' to 'target_currency' on 'date_str'.
        """
        currency = currency.upper().strip()
        target_currency = target_currency.upper().strip()
        date_str = date_str.strip()

        # Handle Pence
        factor = 1.0
        if currency in ["GBX", "GBPENCE"]: # Special codes
            currency = "GBP"
            factor = 0.01
        
        # Identity
        if currency == target_currency:
            return 1.0 * factor

        # Cache Key
        key = f"{currency}_{target_currency}_{date_str}"
        if key in self.cache:
            return self.cache[key] * factor
            
        # Strategy:
        # ALL conversions go through ČNB (Česká národní banka).
        # For cross-rates (e.g., EUR->USD), we triangulate through CZK:
        #   EUR->USD = (EUR->CZK) / (USD->CZK)
        # Frankfurter is only a fallback if CNB fails.
        
        rate = 0.0
        
        if target_currency == 'CZK':
            # Direct: X -> CZK
            rate = self._fetch_cnb_rate(currency, date_str)
            if rate == 0:
                print(f"Warning: CNB missing direct rate for {currency}, using Frankfurter fallback")
                rate = self._fetch_frankfurter(currency, date_str, "CZK")
        elif currency == 'CZK':
            # Inverse: CZK -> X
            inverse = self._fetch_cnb_rate(target_currency, date_str)
            if inverse == 0:
                # Try fallback for inverse too
                inv_rate = self._fetch_frankfurter(target_currency, date_str, "CZK")
                if inv_rate > 0: inverse = inv_rate
                
            if inverse > 0: rate = 1.0 / inverse
        else:
            # Cross-rate: X -> Y via CZK
            # Example: EUR -> USD = (EUR->CZK) / (USD->CZK)
            rate_src_czk = self._fetch_cnb_rate(currency, date_str)
            rate_tgt_czk = self._fetch_cnb_rate(target_currency, date_str)
            
            if rate_src_czk > 0 and rate_tgt_czk > 0:
                rate = rate_src_czk / rate_tgt_czk
            else:
                # Fallback to Frankfurter only if CNB fails
                print(f"Warning: CNB missing rate for {currency} or {target_currency}, using Frankfurter fallback")
                rate = self._fetch_frankfurter(currency, date_str, target_currency)
             
        if rate > 0:
            self.cache[key] = rate
            self._save_cache()
            return rate * factor
            
        return 0.0

    def _fetch_cnb_rate(self, currency: str, date_str: str) -> float:
        try:
            # Date format YYYY-MM-DD -> DD.MM.YYYY
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            cnb_date = dt.strftime("%d.%m.%Y")
            
            url = f"https://www.cnb.cz/cs/financni-trhy/devizovy-trh/kurzy-devizoveho-trhu/kurzy-devizoveho-trhu/denni_kurz.txt?date={cnb_date}"
            
            resp = requests.get(url, timeout=5)
            if resp.status_code != 200:
                print(f"CNB API Error {resp.status_code}")
                return 0.0
                
            # Parse text response
            # 31.01.2025 #22
            # země|měna|množství|kód|kurz
            # Austrálie|dolar|1|AUD|15,649
            
            lines = resp.text.strip().split('\n')
            for line in lines[2:]:
                parts = line.split('|')
                if len(parts) >= 5:
                    code = parts[3]
                    if code == currency:
                        qty = float(parts[2])
                        rate_str = parts[4].replace(',', '.')
                        rate = float(rate_str)
                        return rate / qty
            
            return 0.0
        except Exception as e:
            print(f"Error fetching CNB: {e}")
            return 0.0

    def _fetch_frankfurter(self, currency: str, date_str: str, target_currency: str) -> float:
        try:
            url = f"{self.api_url}/{date_str}"
            params = { "from": currency, "to": target_currency }
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if "rates" in data and target_currency in data["rates"]:
                    return data["rates"][target_currency]
            return 0.0
        except: return 0.0

    async def get_rate_async(self, currency: str, date_str: str, target_currency: str = "CZK") -> float:
        """
        Async version of get_rate.
        """
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_rate, currency, date_str, target_currency)

if __name__ == "__main__":
    fx = ForexService("backend/data/forex_cache.json")
    print("Test 1: SEK -> CZK on 2023-05-01")
    rate = fx.get_rate("SEK", "2023-05-01", "CZK")
    print(f"Rate: {rate}")
    
    print("\nTest 2: USD -> CZK on 2023-05-01")
    rate2 = fx.get_rate("USD", "2023-05-01", "CZK")
    print(f"Rate: {rate2}")
