from typing import Optional, List
from pydantic import BaseModel, Field


class UserProfileIn(BaseModel):
    name: str
    risk_tolerance: str = Field(default="Moderate")         # Conservative | Moderate | Aggressive
    investment_horizon: str = Field(default="Medium Term")  # Short Term | Medium Term | Long Term


class UserProfileOut(UserProfileIn):
    id: int

    class Config:
        from_attributes = True


class PortfolioItemIn(BaseModel):
    user_id: int
    symbol: str
    company_name: Optional[str] = ""
    quantity: float
    average_price: float


class PortfolioItemOut(PortfolioItemIn):
    id: int

    class Config:
        from_attributes = True


class WatchlistItemIn(BaseModel):
    user_id: int
    symbol: str


class WatchlistItemOut(WatchlistItemIn):
    id: int

    class Config:
        from_attributes = True


class AnalyzeRequest(BaseModel):
    user_id: int
