"""
News data service. In this build we always use clearly-labelled demo
headlines (no live news API key required to run the app). Swap in a real
news API here later -- the Sentiment Agent only depends on the shape of
what this function returns: a list of {"headline": str, "sentiment": str}.
"""
from .demo_data import NEWS


def get_news(symbol: str) -> dict:
    symbol = symbol.upper()
    items = NEWS.get(symbol)
    if not items:
        return {"available": False, "items": [], "source": "unavailable"}
    return {"available": True, "items": items, "source": "demo"}
