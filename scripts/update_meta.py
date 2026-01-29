
import json
import os

db_path = "backend/data/metadata.json"
if not os.path.exists(db_path):
    data = {"watchlist": []}
else:
    with open(db_path, "r") as f:
        data = json.load(f)

updates = {
    "EEFT": {"target_price": 165, "risk_score": 4, "buy_zone": 59, "sell_zone": 100},
    "P911": {"target_price": 53, "risk_score": 7, "buy_zone": 43, "sell_zone": 66},
    "EVO": {"target_price": 930, "risk_score": 7, "buy_zone": 550, "sell_zone": 880},
    "PYPL": {"target_price": 100, "risk_score": 4, "buy_zone": 48, "sell_zone": 90},
    "KSPI": {"target_price": 133, "risk_score": 6, "buy_zone": 61, "sell_zone": 99},
    "WIZZ": {"target_price": 1890, "risk_score": 6, "buy_zone": 1001, "sell_zone": 1400},
    "NU": {"target_price": 24, "risk_score": 4, "buy_zone": 12, "sell_zone": 20},
    "JD": {"target_price": 46, "risk_score": 6, "buy_zone": 26, "sell_zone": 44},
    "TUI1": {"target_price": 15, "risk_score": 4, "buy_zone": 6.2, "sell_zone": 10},
    "NICE": {"target_price": 195, "risk_score": 6, "buy_zone": 100, "sell_zone": 155},
    "ZAL": {"target_price": 34, "risk_score": 6, "buy_zone": 19, "sell_zone": 28},
    "S": {"target_price": 28, "risk_score": 5, "buy_zone": 9, "sell_zone": 16},
    "WIX": {"target_price": 170, "risk_score": 6, "buy_zone": 70, "sell_zone": 120},
    "BABA": {"target_price": 215, "risk_score": 4, "buy_zone": 120, "sell_zone": 190},
    "TTD": {"target_price": 54, "risk_score": 7, "buy_zone": 25, "sell_zone": 45},
    "DIDIY": {"target_price": 7, "risk_score": 6, "buy_zone": 3.6, "sell_zone": 6},
    "BOSS": {"target_price": 48, "risk_score": 7, "buy_zone": 30, "sell_zone": 46}
}

for ticker, meta in updates.items():
    if ticker not in data:
        data[ticker] = {}
    data[ticker].update(meta)

with open(db_path, "w") as f:
    json.dump(data, f, indent=2)

print("Metadata updated successfully.")
