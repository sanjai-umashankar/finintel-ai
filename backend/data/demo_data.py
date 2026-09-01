"""
Demo / fallback data.

FinIntel AI always works even with zero external API access: if yfinance
(or a news API, or OpenAI) is unavailable, we fall back to this clearly
labelled simulated data so the whole pipeline still runs end-to-end.

To add a new symbol: add an entry to MARKET_DATA, PRICE_HISTORY, NEWS,
and (optionally) DOCUMENTS.
"""
import random

# ---------------------------------------------------------------------------
# Market data (source: "demo")
# ---------------------------------------------------------------------------
MARKET_DATA = {
    "RELIANCE": {
        "symbol": "RELIANCE",
        "company_name": "Reliance Industries Ltd.",
        "price": 2945.60,
        "change": 32.10,
        "change_pct": 1.10,
        "volume": 8_432_100,
        "avg_volume": 6_120_000,
        "pe_ratio": 27.4,
        "eps": 107.5,
        "revenue_growth_yoy": 8.2,
        "profit_growth_yoy": 11.4,
        "debt_to_equity": 0.42,
        "source": "demo",
    },
    "TCS": {
        "symbol": "TCS",
        "company_name": "Tata Consultancy Services Ltd.",
        "price": 3812.25,
        "change": -18.40,
        "change_pct": -0.48,
        "volume": 2_105_000,
        "avg_volume": 2_400_000,
        "pe_ratio": 29.1,
        "eps": 131.2,
        "revenue_growth_yoy": 6.1,
        "profit_growth_yoy": 5.3,
        "debt_to_equity": 0.08,
        "source": "demo",
    },
    "HDFCBANK": {
        "symbol": "HDFCBANK",
        "company_name": "HDFC Bank Ltd.",
        "price": 1682.90,
        "change": 6.75,
        "change_pct": 0.40,
        "volume": 9_871_200,
        "avg_volume": 10_500_000,
        "pe_ratio": 19.8,
        "eps": 85.0,
        "revenue_growth_yoy": 12.0,
        "profit_growth_yoy": 9.8,
        "debt_to_equity": 1.1,
        "source": "demo",
    },
}


def _synth_price_series(base: float, n: int = 60, seed: int = 0, drift: float = 0.0004):
    """Deterministic pseudo-random walk so charts/indicators are stable per symbol."""
    rnd = random.Random(seed)
    prices = [base]
    for _ in range(n - 1):
        change_pct = rnd.gauss(drift, 0.012)
        prices.append(round(prices[-1] * (1 + change_pct), 2))
    return prices


PRICE_HISTORY = {
    "RELIANCE": _synth_price_series(2850, seed=1, drift=0.0009),
    "TCS": _synth_price_series(3860, seed=2, drift=-0.0003),
    "HDFCBANK": _synth_price_series(1640, seed=3, drift=0.0006),
}

# ---------------------------------------------------------------------------
# News / sentiment source data (source: "demo")
# ---------------------------------------------------------------------------
NEWS = {
    "RELIANCE": [
        {"headline": "Reliance Jio adds record subscribers in Q2", "sentiment": "positive"},
        {"headline": "Reliance Retail expands into three new states", "sentiment": "positive"},
        {"headline": "Oil-to-chemicals margins face global pricing pressure", "sentiment": "negative"},
        {"headline": "Reliance announces green energy investment roadmap", "sentiment": "positive"},
        {"headline": "Analysts maintain neutral stance ahead of earnings", "sentiment": "neutral"},
    ],
    "TCS": [
        {"headline": "TCS wins large multi-year cloud transformation deal", "sentiment": "positive"},
        {"headline": "IT hiring slows industry-wide amid demand softness", "sentiment": "negative"},
        {"headline": "TCS reports steady margins despite currency headwinds", "sentiment": "neutral"},
        {"headline": "TCS expands AI delivery centers in Europe", "sentiment": "positive"},
    ],
    "HDFCBANK": [
        {"headline": "HDFC Bank posts strong deposit growth", "sentiment": "positive"},
        {"headline": "Asset quality remains stable, NPAs contained", "sentiment": "positive"},
        {"headline": "Rising deposit costs pressure near-term margins", "sentiment": "negative"},
        {"headline": "RBI commentary on sector liquidity seen as neutral", "sentiment": "neutral"},
        {"headline": "Bank expands rural branch network", "sentiment": "positive"},
    ],
}

# ---------------------------------------------------------------------------
# Demo "financial documents" — used by the RAG pipeline when no PDF has been
# uploaded for a symbol. Each is pre-chunked. Real uploads go through
# rag/ingestion.py instead and are stored the same way.
# ---------------------------------------------------------------------------
DOCUMENTS = {
    "RELIANCE": {
        "filename": "RELIANCE_Q2_Earnings_Summary_DEMO.txt",
        "chunks": [
            "Reliance Industries reported consolidated revenue growth of 8.2% year-on-year, "
            "driven by strong performance in the digital services and retail segments.",
            "Net profit grew 11.4% year-on-year, supported by improved retail margins and "
            "continued subscriber growth at Jio Platforms.",
            "The company's debt-to-equity ratio stands at 0.42, reflecting a moderate leverage "
            "position relative to sector peers.",
            "Management highlighted continued capital expenditure in green energy and new "
            "manufacturing capacity over the next three years, which may pressure near-term "
            "free cash flow.",
        ],
    },
    "TCS": {
        "filename": "TCS_Annual_Report_Extract_DEMO.txt",
        "chunks": [
            "TCS delivered revenue growth of 6.1% year-on-year in constant currency terms, "
            "with broad-based growth across BFSI and retail verticals.",
            "Operating margins were largely stable at 24-25%, supported by cost optimization "
            "programs and currency tailwinds.",
            "The company maintains a near debt-free balance sheet with a debt-to-equity ratio "
            "of 0.08, and continues its policy of high dividend payout.",
            "Management noted cautious client spending in North American markets, with deal "
            "pipelines remaining healthy but conversion cycles lengthening.",
        ],
    },
    # HDFCBANK intentionally has no demo document, to exercise the
    # "Fundamental document unavailable" graceful-degradation path.
}
