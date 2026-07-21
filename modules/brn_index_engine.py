# brn_index_engine.py


"""
BRN Index Engine

Health
Leading
Risk

세 개의 핵심 Engine 결과를 이용하여
BRN Index를 계산한다.
"""

from __future__ import annotations


class BRNIndexEngine:

    DEFAULT_WEIGHTS = {
        "health": 0.50,
        "leading": 0.30,
        "risk": 0.20,
    }

    def __init__(
        self,
        weights: dict | None = None,
    ):

        self.weights = weights or self.DEFAULT_WEIGHTS

    def calculate(
        self,
        dashboard: dict,
    ) -> dict:

        health = dashboard["health"]
        leading = dashboard["leading"]
        risk = dashboard["risk"]

        index = (
            health * self.weights["health"]
            + leading * self.weights["leading"]
            + risk * self.weights["risk"]
        )

        index = round(index, 2)

        return {
            "index": index,
            "grade": self.grade(index),
            "color": self.color(index),
            "trend": self.trend(index),
            "weights": self.weights,
            "components": {
                "health": health,
                "leading": leading,
                "risk": risk,
            },
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

    @staticmethod
    def color(score: float) -> str:

        if score >= 90:
            return "darkgreen"

        if score >= 80:
            return "green"

        if score >= 70:
            return "limegreen"

        if score >= 60:
            return "gold"

        if score >= 50:
            return "orange"

        return "red"

    @staticmethod
    def trend(score: float) -> str:

        if score >= 80:
            return "Bullish"

        if score >= 70:
            return "Recovery"

        if score >= 60:
            return "Neutral"

        if score >= 50:
            return "Weak"

        return "Bearish"
