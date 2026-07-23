# leading_engine.py


"""
BRN Leading Indicator Engine

선행지표를 이용하여 시장의 방향성을 계산한다.
"""

from __future__ import annotations


class LeadingEngine:
    """
    Leading Score 계산
    """

    DEFAULT_WEIGHTS = {
        "DEMAND_VOLUME": 0.25,
        "DEMAND_JEONSE": 0.25,
        "DEMAND_AUCTION": 0.20,
        "SUPPLY_PERMIT": 0.15,
        "SUPPLY_UNSOLD": 0.15,
    }

    def __init__(self, weights: dict | None = None):

        self.weights = weights or self.DEFAULT_WEIGHTS

    def calculate(self, indicators: list[dict]) -> dict:

        indicator_map = {
            item["id"]: item
            for item in indicators
        }

        total = 0.0
        used = 0.0

        details = {}

        for indicator_id, weight in self.weights.items():

            if indicator_id not in indicator_map:
                continue

            score = indicator_map[indicator_id]["score"]

            details[indicator_id] = round(score, 2)

            total += score * weight

            used += weight

        if used == 0:
            leading = 0.0
        else:
            leading = round(total / used, 2)

        return {
            "leading": leading,
            "signal": self.signal(leading),
            "details": details,
        }

    @staticmethod
    def signal(score: float) -> str:

        if score >= 85:
            return "Strong Recovery"

        if score >= 70:
            return "Recovery"

        if score >= 55:
            return "Neutral"

        if score >= 40:
            return "Weak"

        return "Downtrend"
