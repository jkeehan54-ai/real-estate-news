# market_health_engine.py


"""
BRN Market Health Engine

시장 건강도(Health Score)를 계산한다.
"""

from __future__ import annotations


class MarketHealthEngine:
    """
    Market Health Score 계산
    """

    DEFAULT_WEIGHTS = {
        "price": 0.15,
        "demand": 0.25,
        "supply": 0.20,
        "finance": 0.15,
        "policy": 0.10,
        "risk": 0.15,
    }

    def __init__(self, weights: dict | None = None):

        self.weights = weights or self.DEFAULT_WEIGHTS

    def calculate(self, indicators: list[dict]) -> dict:
        """
        Health Score 계산

        Parameters
        ----------
        indicators : list[dict]

        Returns
        -------
        dict
        """

        category_scores = {}

        for category in self.weights.keys():

            values = [
                item["weighted_score"]
                for item in indicators
                if item["category"].lower() == category
            ]

            if values:
                category_scores[category] = round(
                    sum(values) / len(values),
                    2,
                )
            else:
                category_scores[category] = 0.0

        health = 0.0

        for category, weight in self.weights.items():

            health += category_scores[category] * weight

        health = round(health, 2)

        return {
            "health": health,
            "price": category_scores["price"],
            "demand": category_scores["demand"],
            "supply": category_scores["supply"],
            "finance": category_scores["finance"],
            "policy": category_scores["policy"],
            "risk": category_scores["risk"],
            "grade": self.grade(health),
        }

    @staticmethod
    def grade(score: float) -> str:

        if score >= 90:
            return "Excellent"

        if score >= 80:
            return "Healthy"

        if score >= 70:
            return "Stable"

        if score >= 60:
            return "Caution"

        return "Risk"

