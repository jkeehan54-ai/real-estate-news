# forecast_engine.py


"""
BRN Forecast Engine

Timeline을 이용하여
단기 시장 전망을 계산한다.
"""

from __future__ import annotations

from modules.timeline_engine import TimelineEngine


class ForecastEngine:

    def __init__(self):

        self.timeline = TimelineEngine()

    def build(
        self,
        region: str = "전국",
    ) -> dict:

        timeline = self.timeline.load(region)

        if not timeline:

            return {
                "forecast": "Unknown",
                "trend": 0.0,
                "probability": 0,
                "months": {
                    "1m": "Unknown",
                    "3m": "Unknown",
                    "6m": "Unknown",
                },
            }

        trend = self.timeline.trend(region)

        latest = timeline[-1]

        score = latest["brn_index"]

        if trend >= 3:

            outlook = "Strong Bullish"
            probability = 90

        elif trend >= 1:

            outlook = "Bullish"
            probability = 75

        elif trend > -1:

            outlook = "Neutral"
            probability = 55

        elif trend > -3:

            outlook = "Bearish"
            probability = 35

        else:

            outlook = "Strong Bearish"
            probability = 15

        return {
            "forecast": outlook,
            "probability": probability,
            "trend": trend,
            "current_index": score,
            "months": {
                "1m": self._month1(trend),
                "3m": self._month3(trend),
                "6m": self._month6(trend),
            },
        }

    @staticmethod
    def _month1(trend: float) -> str:

        if trend >= 2:
            return "상승"

        if trend >= 0:
            return "보합"

        return "하락"

    @staticmethod
    def _month3(trend: float) -> str:

        if trend >= 2:
            return "완만한 상승"

        if trend >= 0:
            return "횡보"

        return "완만한 하락"

    @staticmethod
    def _month6(trend: float) -> str:

        if trend >= 2:
            return "상승세 지속"

        if trend >= 0:
            return "안정"

        return "약세 지속"
