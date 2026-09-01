"""
Risk Agent: the personalization core of the system. Same stock, same
technical/fundamental/sentiment inputs -> potentially very different
risk read depending on who's asking.
"""
from typing import List, Dict


def run_risk_agent(
    risk_tolerance: str,
    investment_horizon: str,
    portfolio: List[Dict],
    symbol: str,
    technical: dict,
    fundamental: dict,
    sentiment: dict,
) -> dict:
    symbol = symbol.upper()
    total_value = sum((p["quantity"] * p["average_price"]) for p in portfolio) or 0
    position = next((p for p in portfolio if p["symbol"].upper() == symbol), None)
    position_value = (position["quantity"] * position["average_price"]) if position else 0
    concentration_pct = round((position_value / total_value) * 100, 1) if total_value > 0 else 0.0

    # Thresholds vary by declared risk tolerance -- an aggressive investor's
    # "comfortable" concentration is a conservative investor's red flag.
    thresholds = {
        "Conservative": {"warn": 15, "high": 25},
        "Moderate": {"warn": 25, "high": 40},
        "Aggressive": {"warn": 40, "high": 60},
    }.get(risk_tolerance, {"warn": 25, "high": 40})

    concerns = []
    concentration_flag = False

    if concentration_pct >= thresholds["high"]:
        risk_level = "HIGH"
        concentration_flag = True
        concerns.append(
            f"This position already represents {concentration_pct}% of the portfolio, "
            f"well above the comfortable range for a {risk_tolerance.lower()} investor."
        )
    elif concentration_pct >= thresholds["warn"]:
        risk_level = "MODERATE"
        concentration_flag = True
        concerns.append(
            f"This position represents {concentration_pct}% of the portfolio, "
            f"approaching a high concentration for a {risk_tolerance.lower()} investor."
        )
    else:
        risk_level = "LOW"
        if concentration_pct > 0:
            concerns.append(f"This position represents a modest {concentration_pct}% of the portfolio.")
        else:
            concerns.append("No existing position in this stock — concentration risk is not a factor yet.")

    # Volatility / horizon mismatch
    volatility = (technical or {}).get("indicators", {}).get("volatility_pct")
    if volatility is not None:
        if volatility >= 4 and investment_horizon == "Short Term" and risk_tolerance == "Conservative":
            concerns.append(
                f"Recent volatility ({volatility}%) is relatively high for a conservative, "
                f"short-term investment horizon."
            )
            if risk_level == "LOW":
                risk_level = "MODERATE"

    # Under-diversification: portfolio has very few holdings
    if 0 < len(portfolio) <= 2:
        concerns.append(f"Portfolio currently holds only {len(portfolio)} position(s), limiting diversification.")

    # Conflicting signals across agents raise uncertainty, independent of concentration
    signals = [s.get("signal") for s in (technical, fundamental, sentiment) if s and s.get("status") == "available"]
    bullish_like = {"BULLISH", "POSITIVE"}
    bearish_like = {"BEARISH", "NEGATIVE"}
    has_bull = any(s in bullish_like for s in signals)
    has_bear = any(s in bearish_like for s in signals)
    if has_bull and has_bear:
        concerns.append("Technical, fundamental and sentiment signals disagree with each other.")

    if risk_level == "HIGH":
        recommendation = "Avoid increasing exposure; consider trimming the position."
    elif risk_level == "MODERATE":
        recommendation = "Maintain current exposure and avoid adding further until concentration eases."
    else:
        recommendation = "Current exposure level does not raise portfolio risk concerns."

    return {
        "agent": "Risk Agent",
        "status": "available",
        "risk_level": risk_level,
        "portfolio_concentration_pct": concentration_pct,
        "portfolio_concentration": concentration_flag,
        "total_portfolio_value": round(total_value, 2),
        "position_value": round(position_value, 2),
        "summary": concerns[0] if concerns else "No significant portfolio risk factors identified.",
        "concerns": concerns,
        "recommendation": recommendation,
    }
