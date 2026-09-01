"""
Technical Agent: analyses price history only. Never invents indicators it
can't compute from the data it was given.
"""
from typing import List, Optional


def _sma(prices: List[float], period: int) -> Optional[float]:
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period


def _rsi(prices: List[float], period: int = 14) -> Optional[float]:
    if len(prices) < period + 1:
        return None
    gains, losses = [], []
    for i in range(-period, 0):
        delta = prices[i] - prices[i - 1]
        gains.append(max(delta, 0))
        losses.append(max(-delta, 0))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def _ema(prices: List[float], period: int) -> Optional[float]:
    if len(prices) < period:
        return None
    k = 2 / (period + 1)
    ema = sum(prices[:period]) / period
    for price in prices[period:]:
        ema = price * k + ema * (1 - k)
    return ema


def _macd(prices: List[float]) -> Optional[float]:
    ema12 = _ema(prices, 12)
    ema26 = _ema(prices, 26)
    if ema12 is None or ema26 is None:
        return None
    return round(ema12 - ema26, 2)


def _volatility(prices: List[float], period: int = 20) -> Optional[float]:
    if len(prices) < period:
        return None
    window = prices[-period:]
    mean = sum(window) / period
    variance = sum((p - mean) ** 2 for p in window) / period
    return round((variance ** 0.5) / mean * 100, 2)  # as % of mean price


def run_technical_agent(price_history: Optional[List[float]], volume: Optional[int], avg_volume: Optional[int]) -> dict:
    if not price_history or len(price_history) < 15:
        return {
            "agent": "Technical Agent",
            "status": "unavailable",
            "signal": "UNKNOWN",
            "confidence": 0,
            "summary": "Market data unavailable — technical analysis could not be performed.",
            "key_factors": [],
        }

    current_price = price_history[-1]
    sma20 = _sma(price_history, 20)
    sma50 = _sma(price_history, min(50, len(price_history) - 1))
    rsi = _rsi(price_history)
    macd = _macd(price_history)
    volatility = _volatility(price_history)
    momentum_pct = round(((price_history[-1] - price_history[-10]) / price_history[-10]) * 100, 2) if len(price_history) >= 10 else None

    key_factors = []
    bullish_points = 0
    bearish_points = 0

    if sma20 is not None:
        if current_price > sma20:
            bullish_points += 1
            key_factors.append("Price is above the 20-period moving average")
        else:
            bearish_points += 1
            key_factors.append("Price is below the 20-period moving average")

    if rsi is not None:
        if rsi >= 70:
            bearish_points += 1
            key_factors.append(f"RSI at {rsi} indicates overbought conditions")
        elif rsi <= 30:
            bullish_points += 1
            key_factors.append(f"RSI at {rsi} indicates oversold conditions")
        else:
            key_factors.append(f"RSI at {rsi} is in a neutral range")

    if macd is not None:
        if macd > 0:
            bullish_points += 1
            key_factors.append("MACD is positive, suggesting upward momentum")
        else:
            bearish_points += 1
            key_factors.append("MACD is negative, suggesting downward momentum")

    if momentum_pct is not None:
        if momentum_pct > 0:
            bullish_points += 1
            key_factors.append(f"Positive price momentum of {momentum_pct}% over the last 10 periods")
        else:
            bearish_points += 1
            key_factors.append(f"Negative price momentum of {momentum_pct}% over the last 10 periods")

    if volume and avg_volume:
        if volume > avg_volume * 1.1:
            key_factors.append("Trading volume is above average, supporting the current move")
        elif volume < avg_volume * 0.7:
            key_factors.append("Trading volume is below average, suggesting weaker conviction")

    total_signals = bullish_points + bearish_points
    if total_signals == 0:
        signal = "NEUTRAL"
        confidence = 40
    else:
        bull_ratio = bullish_points / total_signals
        if bull_ratio >= 0.65:
            signal = "BULLISH"
        elif bull_ratio <= 0.35:
            signal = "BEARISH"
        else:
            signal = "NEUTRAL"
        # confidence scales with how lopsided the signals are + how much data we had
        confidence = int(45 + bull_ratio_delta(bull_ratio) * 45)

    summary = {
        "BULLISH": "Positive price momentum with supportive technical indicators.",
        "BEARISH": "Weak price momentum with technical indicators pointing downward.",
        "NEUTRAL": "Mixed technical signals with no clear directional bias.",
    }[signal]

    return {
        "agent": "Technical Agent",
        "status": "available",
        "signal": signal,
        "confidence": confidence,
        "summary": summary,
        "key_factors": key_factors,
        "indicators": {
            "current_price": current_price,
            "sma_20": round(sma20, 2) if sma20 else None,
            "sma_50": round(sma50, 2) if sma50 else None,
            "rsi_14": rsi,
            "macd": macd,
            "momentum_pct_10p": momentum_pct,
            "volatility_pct": volatility,
        },
    }


def bull_ratio_delta(bull_ratio: float) -> float:
    """Distance from the neutral midpoint (0.5), scaled to 0..1."""
    return abs(bull_ratio - 0.5) * 2
