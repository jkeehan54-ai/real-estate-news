# risk_engine.py


"""
BRN Risk Engine

시장 위험도를 계산한다.
"""

from __future__ import annotations


class RiskEngine:
    """
    Risk Score 계산

    점수가 높을수록 위험이 낮다.
    """

    DEFAULT_WEIGHTS = {
        "RISK_PF": 0.40,
        "SUPPLY_UNSOLD": 0.30,
        "FINANCE_RATE": 0.20,
        "DEMAND_AUCTION": 0.10,
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
            risk = 0.0
        else:
            risk = round(total / used, 2)

        return {
            "risk": risk,
            "grade": self.grade(risk),
            "details": details,
        }

    @staticmethod
    def grade(score: float) -> str:

        if score >= 90:
            return "Very Low"

        if score >= 80:
            return "Low"

        if score >= 70:
            return "Normal"

        if score >= 60:
            return "Caution"

        return "High"
