"""
Market data service.

Tries yfinance for live data if it's installed and reachable; otherwise
(or on any error) falls back to the clearly-labelled demo data so the
app never crashes because a data source is unavailable.
"""
from typing import Optional
from .demo_data import MARKET_DATA, PRICE_HISTORY

try:
    import yfinance as yf  # optional dependency
    _HAS_YFINANCE = True
except ImportError:
    _HAS_YFINANCE = False

# Map our simple symbols to NSE tickers for yfinance, when available.
_YF_TICKER_MAP = {
    "RELIANCE": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "HDFCBANK": "HDFCBANK.NS",
}


def get_market_data(symbol: str) -> dict:
    """Return current market snapshot for `symbol`. Never raises."""
    symbol = symbol.upper()

    if _HAS_YFINANCE and symbol in _YF_TICKER_MAP:
        try:
            ticker = yf.Ticker(_YF_TICKER_MAP[symbol])
            info = ticker.fast_info
            price = float(info.last_price)
            prev_close = float(info.previous_close)
            change = round(price - prev_close, 2)
            change_pct = round((change / prev_close) * 100, 2) if prev_close else 0.0
            return {
                "symbol": symbol,
                "company_name": MARKET_DATA.get(symbol, {}).get("company_name", symbol),
                "price": round(price, 2),
                "change": change,
                "change_pct": change_pct,
                "volume": int(info.last_volume or 0),
                "avg_volume": MARKET_DATA.get(symbol, {}).get("avg_volume", 0),
                "pe_ratio": MARKET_DATA.get(symbol, {}).get("pe_ratio"),
                "eps": MARKET_DATA.get(symbol, {}).get("eps"),
                "revenue_growth_yoy": MARKET_DATA.get(symbol, {}).get("revenue_growth_yoy"),
                "profit_growth_yoy": MARKET_DATA.get(symbol, {}).get("profit_growth_yoy"),
                "debt_to_equity": MARKET_DATA.get(symbol, {}).get("debt_to_equity"),
                "source": "live",
            }
        except Exception:
            pass  # fall through to demo data

    if symbol in MARKET_DATA:
        return dict(MARKET_DATA[symbol])

    return {
        "symbol": symbol,
        "company_name": symbol,
        "price": None,
        "change": None,
        "change_pct": None,
        "volume": None,
        "avg_volume": None,
        "pe_ratio": None,
        "eps": None,
        "revenue_growth_yoy": None,
        "profit_growth_yoy": None,
        "debt_to_equity": None,
        "source": "unavailable",
        "error": "Market data unavailable.",
    }


def get_price_history(symbol: str) -> Optional[list]:
    symbol = symbol.upper()

    if _HAS_YFINANCE and symbol in _YF_TICKER_MAP:
        try:
            ticker = yf.Ticker(_YF_TICKER_MAP[symbol])
            hist = ticker.history(period="3mo")
            closes = [round(float(x), 2) for x in hist["Close"].tolist()]
            if closes:
                return closes
        except Exception:
            pass

    return PRICE_HISTORY.get(symbol)


def list_supported_symbols() -> list:
    return list(MARKET_DATA.keys())
