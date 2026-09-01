"""
Synthesis Agent: the only agent that produces a final personalized
signal. It must always explain WHY, and must account for unavailable
or conflicting agent outputs rather than pretending everything agreed.
"""

_BULLISH_LIKE = {"BULLISH", "POSITIVE"}
_BEARISH_LIKE = {"BEARISH", "NEGATIVE"}


def _weighted_score(agents):
    """-1..1 score across available agents, weighted by each agent's own confidence."""
    total_weight = 0
    score = 0
    for agent in agents:
        if not agent or agent.get("status") != "available":
            continue
        signal = agent.get("signal")
        weight = max(agent.get("confidence", 0), 1)
        direction = 1 if signal in _BULLISH_LIKE else (-1 if signal in _BEARISH_LIKE else 0)
        score += direction * weight
        total_weight += weight
    if total_weight == 0:
        return 0.0
    return score / total_weight


def run_synthesis_agent(technical: dict, fundamental: dict, sentiment: dict, risk: dict, user_profile: dict) -> dict:
    agents = [technical, fundamental, sentiment]
    available_agents = [a for a in agents if a and a.get("status") == "available"]
    unavailable_agents = [a for a in agents if not a or a.get("status") != "available"]

    market_score = _weighted_score(agents)  # -1 (bearish) .. +1 (bullish)

    positive_factors, risk_factors = [], []
    for a in available_agents:
        line = f"{a['agent']}: {a['summary']}"
        if a.get("signal") in _BULLISH_LIKE:
            positive_factors.append(line)
        elif a.get("signal") in _BEARISH_LIKE:
            risk_factors.append(line)

    for concern in (risk or {}).get("concerns", []):
        risk_factors.append(f"Risk Agent: {concern}")

    # --- base market read ---
    if market_score >= 0.25:
        market_read = "positive"
    elif market_score <= -0.25:
        market_read = "negative"
    else:
        market_read = "mixed"

    risk_level = (risk or {}).get("risk_level", "LOW")
    concentration_flag = (risk or {}).get("portfolio_concentration", False)
    has_position = (risk or {}).get("position_value", 0) > 0

    # --- personalization: map (market_read, risk_level, has_position) -> final signal ---
    if market_read == "positive":
        if risk_level == "HIGH":
            final_signal = "HOLD"
            personalized_action = "Maintain the current position and avoid increasing concentration."
        elif risk_level == "MODERATE":
            final_signal = "HOLD"
            personalized_action = "Hold the current position; consider adding only after concentration eases."
        else:
            final_signal = "ACCUMULATE" if has_position else "BUY"
            personalized_action = (
                "Consider gradually increasing this position given favorable indicators and low portfolio risk."
                if has_position else
                "Indicators are favorable and this would not create outsized portfolio risk."
            )
    elif market_read == "negative":
        if has_position and risk_level in ("HIGH", "MODERATE"):
            final_signal = "REDUCE"
            personalized_action = "Consider reducing exposure given weakening indicators and elevated concentration."
        elif has_position:
            final_signal = "HOLD"
            personalized_action = "Monitor the position; indicators are weakening but portfolio risk is currently low."
        else:
            final_signal = "HOLD"
            personalized_action = "Avoid initiating a new position until indicators improve."
    else:  # mixed
        final_signal = "HOLD"
        personalized_action = "Signals are mixed — maintain current exposure and reassess as new data arrives."

    # --- confidence: combine available agent confidences, then penalize for gaps ---
    if available_agents:
        base_confidence = sum(a["confidence"] for a in available_agents) / len(available_agents)
    else:
        base_confidence = 0

    confidence = base_confidence
    confidence_notes = []

    if unavailable_agents:
        penalty = 12 * len(unavailable_agents)
        confidence = max(0, confidence - penalty)
        names = ", ".join(a["agent"] if a else "An agent" for a in unavailable_agents)
        confidence_notes.append(f"Confidence reduced because data was unavailable for: {names}.")

    signals_present = {a["signal"] for a in available_agents}
    if signals_present & _BULLISH_LIKE and signals_present & _BEARISH_LIKE:
        confidence = max(0, confidence - 10)
        confidence_notes.append("Confidence reduced because agents produced conflicting signals.")

    if fundamental and fundamental.get("status") == "available" and not fundamental.get("document_available"):
        confidence = max(0, confidence - 10)
        confidence_notes.append("Confidence reduced because no fundamental document was available for this stock.")

    confidence = round(min(confidence, 95))  # never claim false certainty

    # --- explanation ---
    profile_desc = f"{user_profile.get('risk_tolerance', 'Moderate')} risk, {user_profile.get('investment_horizon', 'Medium Term')} horizon"
    if market_read == "positive" and concentration_flag:
        reason = (
            f"Technical, fundamental and sentiment indicators are broadly {market_read}, "
            f"but the user's current portfolio has {'high' if risk_level == 'HIGH' else 'elevated'} "
            f"exposure to this stock relative to a {profile_desc.lower()} profile."
        )
    elif market_read == "negative":
        reason = (
            f"Market indicators are broadly {market_read} for this stock. "
            f"Given the user's {profile_desc.lower()} profile, the recommendation reflects reduced conviction."
        )
    else:
        reason = (
            f"Market indicators are {market_read} for this stock, and portfolio risk for this "
            f"{profile_desc.lower()} profile is currently {risk_level.lower()}."
        )

    return {
        "final_signal": final_signal,
        "confidence": confidence,
        "confidence_notes": confidence_notes,
        "reason": reason,
        "positive_factors": positive_factors,
        "risk_factors": risk_factors,
        "personalized_action": personalized_action,
        "agents_available": [a["agent"] for a in available_agents],
        "agents_unavailable": [a["agent"] if a else "Unknown Agent" for a in unavailable_agents],
        "market_read": market_read,
        "disclaimer": "AI-generated financial intelligence for educational purposes only. Not guaranteed financial advice.",
    }
