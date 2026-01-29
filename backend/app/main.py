from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import shutil
import json
import asyncio
import pandas as pd
from datetime import datetime
from fastapi.responses import StreamingResponse

from .services.parser import IBKRParser
from .services.merger import DataMerger
from .services.engine import PortfolioEngine
from .services.store import StoreService
from .services.market import MarketDataService
from .services.options import OptionsService
from .services.activity_parser import ActivityParser
from .models import MetadataUpdate, WatchlistAdd, OptionTrade, OptionUpdate

app = FastAPI()

# 1. CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services (Global Instances)
parser = IBKRParser()
merger = DataMerger()
engine = PortfolioEngine() 
store = StoreService()
market = MarketDataService()
options_service = OptionsService()
# Determine absolute path to backend/data
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(base_dir, "data")
activity_parser = ActivityParser(data_dir)

@app.get("/api/performance")
async def get_performance():
    """Get aggregated performance data from Activity Statements."""
    try:
        data = activity_parser.parse_all()
        return data
    except Exception as e:
        print(f"Error parsing activity: {e}")
        return {"trades": [], "interest": [], "error": str(e)}

@app.get("/api/portfolio")
async def get_portfolio():
    # 1. Setup Data Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(base_dir, "backend", "data")
    if not os.path.exists(data_dir): os.makedirs(data_dir)

    # 2. Parse CSVs
    found_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith('.csv')]
    if not found_files:
        return {"kpi": {"net_liquidity_usd": 0, "net_liquidity_czk": 0, "cash_balance_usd": 0}, "positions": [], "status": "empty"}

    # Generate File Hash (for caching)
    # Concatenate filename + mtime + size
    file_stats = []
    for f in sorted(found_files):
        stats = os.stat(f)
        file_stats.append(f"{f}_{stats.st_mtime}_{stats.st_size}")
    files_hash = str(hash("".join(file_stats)))

    parsed_data = []
    for fpath in found_files:
        try:
            parsed_data.append(parser.parse_csv(fpath))
        except Exception as e:
            print(f"Error parsing {fpath}: {e}")
    
    if not parsed_data:
         return {"kpi": {"net_liquidity_usd": 0, "net_liquidity_czk": 0, "cash_balance_usd": 0}, "positions": [], "status": "empty"}

    # 3. Process
    merged = merger.merge(parsed_data)
    metadata = store.load()
    result = await engine.process(merged, metadata, files_hash=files_hash)
    return result

@app.post("/api/upload")
async def upload_csv(files: List[UploadFile] = File(...)):
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(base_dir, "backend", "data")
    if not os.path.exists(data_dir): os.makedirs(data_dir)
        
    saved_files = []
    for file in files:
        file_path = os.path.join(data_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append(file.filename)
    return {"status": "success", "files": saved_files}

@app.get("/api/quote")
async def get_quote(symbol: str):
    """Fetch single quote for simulation using consolidated service."""
    symbol = symbol.upper()
    data_map = await market.get_live_prices([symbol])
    data = data_map.get(symbol)
    
    if not data:
        return {"symbol": symbol, "price": 0.0, "currency": "USD", "found": False}
        
    # Basic currency inference (could be moved to MarketDataService)
    currency = "USD"
    if ".DE" in symbol or ".PA" in symbol: currency = "EUR"
    elif ".ST" in symbol: currency = "SEK"
    elif ".L" in symbol: currency = "GBP"
        
    return {
        "symbol": symbol,
        "price": data.get('price'),
        "name": data.get('name'),
        "currency": currency,
        "found": True
    }

@app.post("/api/metadata")
def update_metadata(update: MetadataUpdate):
    data = update.dict(exclude_unset=True)
    symbol = data.pop('symbol')
    store.update_metadata(symbol, data)
    return {"status": "success", "updated": symbol}

@app.get("/api/metadata/{symbol}")
def get_metadata(symbol: str):
    return store.get_metadata(symbol.upper())

@app.get("/api/watchlist")
def get_watchlist():
    return store.get_watchlist()

@app.post("/api/watchlist")
def add_to_watchlist(item: WatchlistAdd):
    return store.add_to_watchlist(item.symbol.upper())

@app.delete("/api/watchlist/{symbol}")
def remove_from_watchlist(symbol: str):
    return store.remove_from_watchlist(symbol.upper())

@app.get("/api/market-data/{symbol}/ohlcv")
async def get_ohlcv(symbol: str, range: str = "1y"):
    return await market.get_ohlcv(symbol.upper(), range)

@app.get("/api/watchlist/stream")
async def stream_watchlist(range: str = "1m"):
    watchlist = store.get_watchlist()
    async def event_generator():
        if not watchlist:
             yield f"event: DONE\ndata: \n\n"
             return
        
        # Parallel fetch
        tasks = [market.get_watchlist_data(symbol, range) for symbol in watchlist]
        results = await asyncio.gather(*tasks)
        
        for data in results:
            yield f"data: {json.dumps(data)}\n\n"
            
        yield f"event: DONE\ndata: \n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Options Endpoints
@app.get("/api/options")
def get_options():
    return options_service.get_all_trades()

@app.post("/api/options")
def create_option(trade: OptionTrade):
    return options_service.add_trade(trade.dict())

@app.put("/api/options/{trade_id}")
def update_option(trade_id: str, update: OptionUpdate):
    updates = update.dict(exclude_unset=True)
    result = options_service.update_trade(trade_id, updates)
    if result:
        return {"status": "success", "trade": result}
    return {"status": "error", "message": "Trade not found"}

@app.delete("/api/options/{trade_id}")
def delete_option(trade_id: str):
    if options_service.delete_trade(trade_id):
        return {"status": "success"}
    return {"status": "error", "message": "Trade not found"}

@app.get("/api/options/stats")
def get_options_stats():
    return options_service.get_stats()

@app.post("/api/options/import")
def import_options():
    # 1. Load Data
    import os
    # main.py is in app/. data/ is in backend/data/ (one level up from app/)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    
    csv_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith('.csv')]
    parsed_data = []
    for f in csv_files:
        try: parsed_data.append(parser.parse_csv(f))
        except: pass
    
    merged = merger.merge(parsed_data)
    pos = merged.get('Open Positions', pd.DataFrame())
    
    count = 0
    if not pos.empty:
        for _, row in pos.iterrows():
            cat = str(row.get('Asset Category', ''))
            symbol = row.get('Symbol', '')
            
            # Check if Option
            # IBKR often lists "Equity and Index Options" or similar
            is_option = 'Option' in cat or ((symbol.endswith(' P') or symbol.endswith(' C')) and len(symbol) > 10)
            
            if is_option:
                # Deduplicate: Check if option already exists?
                # For now, simplistic check or just add if not present
                # Parse Symbol: SPY 30JUN26 660 P
                try:
                    parts = symbol.split()
                    if len(parts) >= 4:
                        ticker = parts[0]
                        expiry_raw = parts[1] # 30JUN26
                        strike = float(parts[2])
                        otype = parts[3] # P or C
                        
                        # Parse Date
                        try:
                            dt = datetime.strptime(expiry_raw, "%d%b%y")
                            exp_date = dt.strftime("%Y-%m-%d")
                        except:
                            exp_date = datetime.now().strftime("%Y-%m-%d") # Fallback
                        
                        # Construct Trade
                        # Check exist
                        existing = [t for t in options_service.get_all_trades() if t['ticker'] == ticker and t['strike'] == strike and t['expiration'] == exp_date]
                        if existing: continue

                        # Cost Basis / Price
                        # If we sold, cost basis is usually negative (credit). 
                        # Premium is effectively the price we sold at.
                        # IBKR 'Cost Basis' is total cost. 'Cost Price' is per share.
                        # Let's use 'Cost Price' from report if available, else 'Close Price'.
                        # Actually 'marked price' is current price.
                        # We want 'Trade Price' (Premium). 
                        # This is tricky from Open Positions as it tracks *current* state.
                        # We can try to approximate Premium from Cost Basis / Qty
                        qty = float(str(row.get('Quantity', 0)).replace(',', ''))
                        cost_basis = float(str(row.get('Cost Basis', 0)).replace(',', ''))
                        
                        # If short (sold), qty is negative.
                        # Premium = (Cost Basis / Qty) * -1? 
                        # Example: Sold 1 put. Qty -1. Cost Basis -500 (Received 500).
                        # Avg Price = -500 / -1 = 500. = 5.00 * 100.
                        
                        premium = 0.0
                        if abs(qty) > 0:
                            # Cost basis is total.
                            # Per contract premium = (Cost Basis / Qty) / 100 (if standard 100x)
                            # But wait, Cost Basis in IBKR is usually total value.
                            # If I sold for $0.50, and have -1 qty.
                            # Cost Basis is approx -50.
                            # Price = (-50 / -1) / 100 = 0.50.
                            premium = (cost_basis / qty) / 100.0
                        
                        # Type
                        full_type = "SELL PUT"
                        if otype == 'P':
                            full_type = "SELL PUT" if qty < 0 else "BUY PUT"
                        elif otype == 'C':
                            full_type = "SELL CALL" if qty < 0 else "BUY CALL"

                        trade = {
                            "ticker": ticker,
                            "type": full_type,
                            "strike": strike,
                            "expiration": exp_date,
                            "premium": abs(premium),
                            "fees": 0,
                            "currency": row.get('Currency', 'USD'),
                            "status": "OPEN", 
                            "date_opened": datetime.now().strftime("%Y-%m-%d"), # Unknown from OpenPos
                            "notes": "Imported from Portfolio"
                        }
                        options_service.add_trade(trade)
                        count += 1
                except Exception as e:
                    print(f"Error parsing option {symbol}: {e}")
                    
    return {"status": "success", "imported": count}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

