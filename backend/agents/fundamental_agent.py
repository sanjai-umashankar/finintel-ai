"""
Fundamental Agent: analyses financial metrics + retrieves supporting
context from uploaded/demo documents via RAG. Never fabricates a source.
"""
from backend.rag.retrieval import retrieve_for_symbol


def run_fundamental_agent(market_data: dict, symbol: str) -> dict:
    if not market_data or market_data.get("source") == "unavailable":
        return {
            "agent": "Fundamental Agent",
            "status": "unavailable",
            "signal": "UNKNOWN",
            "confidence": 0,
            "summary": "Fundamental data unavailable.",
            "key_factors": [],
            "sources": [],
        }

    key_factors = []
    positive_points = 0
    negative_points = 0

    rev_growth = market_data.get("revenue_growth_yoy")
    profit_growth = market_data.get("profit_growth_yoy")
    pe = market_data.get("pe_ratio")
    debt_to_equity = market_data.get("debt_to_equity")

    if rev_growth is not None:
        if rev_growth >= 8:
            positive_points += 1
            key_factors.append(f"Revenue grew {rev_growth}% year-on-year")
        elif rev_growth <= 2:
            negative_points += 1
            key_factors.append(f"Revenue growth is weak at {rev_growth}% year-on-year")
        else:
            key_factors.append(f"Revenue growth is moderate at {rev_growth}% year-on-year")

    if profit_growth is not None:
        if profit_growth >= 8:
            positive_points += 1
            key_factors.append(f"Profit grew {profit_growth}% year-on-year")
        elif profit_growth <= 2:
            negative_points += 1
            key_factors.append(f"Profit growth is weak at {profit_growth}% year-on-year")

    if debt_to_equity is not None:
        if debt_to_equity <= 0.5:
            positive_points += 1
            key_factors.append(f"Debt-to-equity of {debt_to_equity} indicates conservative leverage")
        elif debt_to_equity >= 1.5:
            negative_points += 1
            key_factors.append(f"Debt-to-equity of {debt_to_equity} indicates high leverage")

    if pe is not None:
        key_factors.append(f"Trading at a P/E ratio of {pe}")

    # --- RAG retrieval ---
    retrieval = retrieve_for_symbol(symbol)
    sources = []
    doc_confidence_penalty = 0

    if retrieval["available"]:
        for chunk in retrieval["chunks"]:
            sources.append({
                "document_name": chunk["filename"],
                "excerpt": chunk["text"][:220] + ("..." if len(chunk["text"]) > 220 else ""),
                "relevance_score": chunk.get("score"),
                "is_demo": retrieval["is_demo"],
            })
        if retrieval["is_demo"]:
            key_factors.append("Analysis supplemented by demo sample financial document (no user document uploaded)")
    else:
        doc_confidence_penalty = 15
        key_factors.append("Fundamental document unavailable")

    total_signals = positive_points + negative_points
    if total_signals == 0:
        signal = "NEUTRAL"
        base_confidence = 45
    else:
        pos_ratio = positive_points / total_signals
        if pos_ratio >= 0.65:
            signal = "POSITIVE"
        elif pos_ratio <= 0.35:
            signal = "NEGATIVE"
        else:
            signal = "NEUTRAL"
        base_confidence = int(50 + abs(pos_ratio - 0.5) * 2 * 40)

    confidence = max(0, base_confidence - doc_confidence_penalty)

    summary = {
        "POSITIVE": "Fundamental indicators show healthy business performance.",
        "NEGATIVE": "Fundamental indicators show signs of weakening business performance.",
        "NEUTRAL": "Fundamental indicators are mixed, with no strong directional signal.",
    }[signal]

    return {
        "agent": "Fundamental Agent",
        "status": "available",
        "signal": signal,
        "confidence": confidence,
        "summary": summary,
        "key_factors": key_factors,
        "sources": sources,
        "document_available": retrieval["available"],
        "document_is_demo": retrieval.get("is_demo", False),
    }
