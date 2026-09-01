"""
Sentiment Agent: analyses news headlines. Always labels demo/simulated
news clearly and never presents it as real news.
"""


def run_sentiment_agent(news: dict) -> dict:
    if not news or not news.get("available"):
        return {
            "agent": "Sentiment Agent",
            "status": "unavailable",
            "signal": "UNKNOWN",
            "confidence": 0,
            "sentiment_distribution": {"positive": 0, "neutral": 0, "negative": 0},
            "summary": "Sentiment data unavailable.",
            "key_factors": [],
        }

    items = news["items"]
    total = len(items)
    counts = {"positive": 0, "neutral": 0, "negative": 0}
    for item in items:
        counts[item["sentiment"]] += 1

    distribution = {k: round((v / total) * 100) for k, v in counts.items()}

    if distribution["positive"] >= 55:
        signal = "POSITIVE"
    elif distribution["negative"] >= 55:
        signal = "NEGATIVE"
    else:
        signal = "NEUTRAL"

    # Confidence reflects how lopsided the distribution is and sample size.
    dominant = max(distribution.values())
    size_factor = min(total / 8, 1.0)  # fewer headlines -> lower confidence
    confidence = int((40 + dominant * 0.5) * size_factor + (1 - size_factor) * 30)
    confidence = min(confidence, 90)

    summary_map = {
        "POSITIVE": "Recent news sentiment is predominantly positive.",
        "NEGATIVE": "Recent news sentiment is predominantly negative.",
        "NEUTRAL": "Recent news sentiment is mixed with no dominant tone.",
    }

    key_factors = [item["headline"] for item in items[:4]]

    return {
        "agent": "Sentiment Agent",
        "status": "available",
        "signal": signal,
        "confidence": confidence,
        "sentiment_distribution": distribution,
        "summary": summary_map[signal],
        "key_factors": key_factors,
        "is_demo": news.get("source") == "demo",
        "data_note": "Based on simulated/demo news headlines, not live news." if news.get("source") == "demo" else None,
    }
