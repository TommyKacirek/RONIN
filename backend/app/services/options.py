
import json
import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

class OptionsService:
    def __init__(self, db_path="backend/data/options.json"):
        # Relativize path
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        if os.path.isabs(db_path):
            self.db_path = db_path
        else:
            self.db_path = os.path.join(base_dir or os.getcwd(), db_path)
            
        self.trades = self._load()

    def _load(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            with open(self.db_path, 'w') as f:
                json.dump(self.trades, f, indent=2)
        except Exception as e:
            print(f"Error saving options: {e}")

    def get_all_trades(self) -> List[Dict[str, Any]]:
        return sorted(self.trades, key=lambda x: x.get('date_opened', ''), reverse=True)

    def add_trade(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        new_trade = {
            "id": str(uuid.uuid4()),
            "date_opened": datetime.now().strftime("%Y-%m-%d"),
            "status": "OPEN",
            **trade_data
        }
        self.trades.append(new_trade)
        self._save()
        return new_trade

    def update_trade(self, trade_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for trade in self.trades:
            if trade['id'] == trade_id:
                trade.update(updates)
                self._save()
                return trade
        return None

    def delete_trade(self, trade_id: str) -> bool:
        initial_len = len(self.trades)
        self.trades = [t for t in self.trades if t['id'] != trade_id]
        if len(self.trades) < initial_len:
            self._save()
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Calculates dashboard stats:
        - Total Exposure (Sum of Strike * 100 for OPEN PUTs)
        - Cash Flow (Sum of Premiums for Closed/Expired this year)
        - Active Trades Count
        """
        current_year = datetime.now().year
        total_exposure = 0.0
        yearly_premium = 0.0
        active_count = 0
        
        # Currency breakdown for premiums
        premium_by_currency = {"USD": 0.0, "EUR": 0.0, "CZK": 0.0}

        for t in self.trades:
            status = t.get('status', 'OPEN')
            itype = t.get('type', 'SELL PUT')
            strike = float(t.get('strike', 0))
            premium = float(t.get('premium', 0)) 
            currency = t.get('currency', 'USD')
            dt_str = t.get('date_opened', '')
            
            # Exposure: Only Open Puts
            if status == "OPEN" and "PUT" in itype:
                total_exposure += strike * 100
                active_count += 1
            elif status == "OPEN":
                active_count += 1

            # Cash Flow: All premiums count when collected? Or when closed?
            # User said "Cash Flow: Sum of premiums for this month/year".
            # Usually you collect premium immediately on Sell.
            # So looking at date_opened for the year.
            if dt_str.startswith(str(current_year)):
                 yearly_premium += premium # Simplified, ignores currency conversion for total
                 if currency in premium_by_currency:
                     premium_by_currency[currency] += premium
        
        return {
            "total_exposure_usd": total_exposure, # Assuming mostly USD/EUR options, this is rough mix
            "active_trades": active_count,
            "yearly_premium_by_currency": premium_by_currency
        }
