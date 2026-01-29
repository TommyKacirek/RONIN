import json
import os
from typing import Dict, Any, Optional

class StoreService:
    def __init__(self, db_path="backend/data/metadata.json"):
        # Relativize path
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        if os.path.isabs(db_path):
            self.db_path = db_path
        else:
            self.db_path = os.path.join(base_dir or os.getcwd(), db_path)
            
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def load(self) -> Dict[str, Any]:
        self.data = self._load()
        return self.data

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            tmp_path = f"{self.db_path}.tmp"
            with open(tmp_path, 'w') as f:
                json.dump(self.data, f, indent=2)
            os.replace(tmp_path, self.db_path)
        except Exception as e:
            print(f"Error saving metadata: {e}")

    def get_metadata(self, symbol: str) -> Dict[str, Any]:
        return self.data.get(symbol, {})

    def update_metadata(self, symbol: str, updates: Dict[str, Any]):
        """
        Updates metadata for a symbol. Merges with existing.
        """
        if symbol not in self.data:
            self.data[symbol] = {}
        
        # Merge
        for k, v in updates.items():
            if v is not None:
                self.data[symbol][k] = v
        
        self._save()
        return self.data[symbol]

    # Watchlist Methods
    def get_watchlist(self) -> list[str]:
        return self.data.get("watchlist", [])

    def add_to_watchlist(self, symbol: str) -> list[str]:
        watchlist = self.get_watchlist()
        if symbol not in watchlist:
            watchlist.append(symbol)
            self.data["watchlist"] = watchlist
            self._save()
        return watchlist

    def remove_from_watchlist(self, symbol: str) -> list[str]:
        watchlist = self.get_watchlist()
        if symbol in watchlist:
            watchlist.remove(symbol)
            self.data["watchlist"] = watchlist
            self._save()
        return watchlist
