import csv
import os
import glob
from datetime import datetime
from typing import List, Dict, Any

class ActivityParser:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir

    def parse_all(self) -> Dict[str, Any]:
        """
        Parses all Activity Statement CSV files in the data directory.
        Returns aggregated trades and interest data.
        """
        # Find all CSV files that look like Activity Statements (start with U)
        files = glob.glob(os.path.join(self.data_dir, "U*.csv"))
        
        all_trades = []
        all_interest = []
        processed_files = []

        for file_path in files:
            try:
                # Check if it's an Activity Statement by reading first few lines
                if not self._is_activity_statement(file_path):
                    continue
                
                trades, interest = self._parse_file(file_path)
                all_trades.extend(trades)
                all_interest.extend(interest)
                processed_files.append(os.path.basename(file_path))
            except Exception as e:
                print(f"Error parsing {file_path}: {e}")

        # Deduplicate trades/interest based on unique keys (Symbol+Date+Price?)
        # For now, simple aggregation (assuming non-overlapping files or handling overlap later)
        # Actually, user files seem to overlap in dates (20250930_20260123 vs 20260101_20260128).
        # We MUST deduplicate.
        
        unique_trades = self._deduplicate(all_trades, key_func=lambda x: f"{x['symbol']}_{x['date']}_{x['time']}_{x['quantity']}_{x['price']}")
        unique_interest = self._deduplicate(all_interest, key_func=lambda x: f"{x['date']}_{x['amount']}_{x['currency']}_{x['description']}")

        # Sort by date descending
        unique_trades.sort(key=lambda x: x['date_obj'], reverse=True)
        unique_interest.sort(key=lambda x: x['date_obj'], reverse=True)

        return {
            "trades": unique_trades,
            "interest": unique_interest,
            "files": processed_files
        }

    def _is_activity_statement(self, file_path: str) -> bool:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            head = [next(f) for _ in range(5)]
            content = "".join(head)
            return "Activity Statement" in content or "Statement,Data,Title,Activity Statement" in content

    def _parse_file(self, file_path: str):
        trades = []
        interests = []
        
        # Headers map: Section -> {ColName: Index}
        headers = {}
        
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row: continue
                section = row[0]
                type_ = row[1]
                
                # Parse Headers
                if type_ == "Header":
                    # Map column names to indices for this section
                    # Format: Section, Header, Col1, Col2...
                    col_map = {name: i for i, name in enumerate(row)}
                    headers[section] = col_map
                    continue

                # Parse Trades
                if section == "Trades" and type_ == "Data" and row[2] == "Order":
                    # Ensure we have headers
                    if "Trades" not in headers: continue
                    h = headers["Trades"]
                    
                    # Extract fields safely
                    try:
                        symbol = row[h.get("Symbol", 5)]
                        dt_str = row[h.get("Date/Time", 6)] # "2026-01-28, 10:06:38"
                        qty = float(row[h.get("Quantity", 7)].replace(',', ''))
                        price = float(row[h.get("T. Price", 8)].replace(',', ''))
                        proceeds = float(row[h.get("Proceeds", 10)].replace(',', ''))
                        comm = float(row[h.get("Comm/Fee", 11)].replace(',', ''))
                        basis = float(row[h.get("Basis", 12)].replace(',', ''))
                        realized_pnl = float(row[h.get("Realized P/L", 13)].replace(',', ''))
                        code = row[h.get("Code", 15)]
                        category = row[h.get("Asset Category", 3)]
                        currency = row[h.get("Currency", 4)]

                        # Parse Date
                        # Format "YYYY-MM-DD, HH:MM:SS"
                        if "," in dt_str:
                            date_obj = datetime.strptime(dt_str, "%Y-%m-%d, %H:%M:%S")
                        else:
                            date_obj = datetime.strptime(dt_str, "%Y-%m-%d") # Sometimes just date?

                        trades.append({
                            "symbol": symbol,
                            "date": date_obj.strftime("%Y-%m-%d"),
                            "time": date_obj.strftime("%H:%M:%S"),
                            "date_obj": date_obj,
                            "quantity": qty,
                            "price": price,
                            "proceeds": proceeds,
                            "commission": comm,
                            "basis": basis,
                            "realized_pnl": realized_pnl,
                            "currency": currency,
                            "category": category,
                            "code": code
                        })
                    except (ValueError, KeyError, IndexError) as e:
                        # print(f"Skipping trade row: {e}")
                        continue

                # Parse Interest
                if section == "Interest" and type_ == "Data":
                    # Skip Total rows
                    if "Total" in row[2]: continue # Currency column (index 2) usually has 'Total' for summary rows
                    
                    if "Interest" not in headers: continue
                    h = headers["Interest"]
                    
                    try:
                        currency = row[h.get("Currency", 2)]
                        # If Currency field is empty or contains "Total", skip
                        if not currency or "Total" in currency: continue

                        date_str = row[h.get("Date", 3)]
                        desc = row[h.get("Description", 4)]
                        amount = float(row[h.get("Amount", 5)].replace(',', ''))

                        date_obj = datetime.strptime(date_str, "%Y-%m-%d")

                        interests.append({
                            "date": date_str,
                            "date_obj": date_obj,
                            "currency": currency,
                            "description": desc,
                            "amount": amount
                        })
                    except (ValueError, KeyError, IndexError) as e:
                        continue

        return trades, interests

    def _deduplicate(self, items: List[Dict], key_func) -> List[Dict]:
        seen = set()
        unique = []
        for item in items:
            key = key_func(item)
            if key not in seen:
                seen.add(key)
                unique.append(item)
        return unique
