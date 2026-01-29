from pydantic import BaseModel
from typing import Optional, List

# 1. Dashboard & Portfolio Models
class MetadataUpdate(BaseModel):
    symbol: str
    target_price: Optional[float] = None
    risk: Optional[int] = None
    note: Optional[str] = None
    buy_zone: Optional[float] = None
    sell_zone: Optional[float] = None
    measurements: Optional[List] = None

class WatchlistAdd(BaseModel):
    symbol: str

# 2. Options Module Models
class OptionTrade(BaseModel):
    ticker: str
    type: str = "SELL PUT" # SELL PUT, BUY CALL etc
    strike: float
    expiration: str # YYYY-MM-DD
    premium: float
    fees: float = 0.0
    currency: str = "USD"
    status: str = "OPEN" # OPEN, CLOSED, EXPIRED, ASSIGNED
    date_opened: str # YYYY-MM-DD
    notes: Optional[str] = None

class OptionUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
