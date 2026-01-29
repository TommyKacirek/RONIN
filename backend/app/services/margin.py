import requests
from bs4 import BeautifulSoup
import json
import os
import time
from typing import Dict, Optional, Tuple

class MarginRatesFetcher:
    URL = "https://www.interactivebrokers.com/en/trading/margin-rates.php"
    CACHE_FILE = "backend/data/margin_rates.json"
    CACHE_TTL = 86400  # 24 hours

    def __init__(self):
        # Ensure data dir exists
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.cache_path = os.path.join(base_dir, "data", "margin_rates.json")

    def get_rates(self) -> Dict[str, float]:
        """Returns map of Currency -> Annual Interest Rate (%)"""
        return {} # Placeholder as we use hardcoded tiers in Service now

    def _load_cache(self) -> Optional[Dict[str, float]]:
        if not os.path.exists(self.cache_path):
            return None
        try:
            with open(self.cache_path, 'r') as f:
                data = json.load(f)
                if time.time() - data.get('timestamp', 0) < self.CACHE_TTL:
                    return data.get('rates')
        except:
            pass
        return None

class MarginService:
    # Tiers structure: (Upper Limit, Rate %)
    # "inf" means remaining balance.
    # Rates based on User provided screenshot (Jan 2026) -> BM (~3.64%) + Spread
    FALLBACK_TIERS = {
        "USD": [
            (100_000, 5.14),    # 0 - 100,000 (BM + 1.5%)
            (1_000_000, 4.64),  # 100,000 - 1,000,000 (BM + 1%)
            (50_000_000, 4.39), # 1M - 50M (BM + 0.75%)
            (float('inf'), 4.14) # > 50M (BM + 0.5%)
        ],
        "EUR": [
            (100_000, 4.88),    # Est. BM + 1.5
            (1_000_000, 4.38),  # Est. BM + 1
            (float('inf'), 4.13)
        ],
        "CZK": [
            (2_500_000, 6.75),  # Est. (approx 100k USD equivalent)
            (float('inf'), 6.25)
        ]
    }

    def __init__(self):
        self.fetcher = MarginRatesFetcher()

    def calculate_daily_cost(self, currency: str, balance: float) -> Tuple[float, float, float]:
        """
        Calculates interest for a given balance using tiered rates.
        Returns: (annual_cost, daily_cost, effective_rate)
        """
        if balance >= -0.01:
            return 0.0, 0.0, 0.0

        debt = abs(balance)
        tiers = self.FALLBACK_TIERS.get(currency, [(float('inf'), 6.0)])
        
        total_annual_cost = 0.0
        remaining_debt = debt
        previous_limit = 0.0
        
        for limit, rate in tiers:
            if remaining_debt <= 0:
                break
                
            tier_capacity = limit - previous_limit
            amount_in_tier = min(remaining_debt, tier_capacity)
            
            cost = amount_in_tier * (rate / 100.0)
            total_annual_cost += cost
            
            remaining_debt -= amount_in_tier
            previous_limit = limit

        day_count = 360.0 if currency in ['USD', 'EUR'] else 365.0
        daily_cost = total_annual_cost / day_count
        effective_rate = (total_annual_cost / debt) * 100.0 if debt > 0 else 0.0
        
        return total_annual_cost, daily_cost, effective_rate
