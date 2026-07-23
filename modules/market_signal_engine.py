# market_signal_engine.py


"""
BRN Market Signal Engine

시장 신호를 생성한다.
"""

from __future__ import annotations


class MarketSignalEngine:
    """
    Dashboard에서 사용하는 시장 신호 생성
    """

    def build(self, dashboard: dict) -> dict:

        return {
            "market": self.market_signal(dashboard["health"]),
            "leading": self.leading_signal(dashboard["leading"]),
            "risk": self.risk_signal(dashboard["risk"]),
            "demand": self.score_signal(dashboard["demand"]),
            "supply": self.score_signal(dashboard["supply"]),
            "finance": self.score_signal(dashboard["finance"]),
            "policy": self.score_signal(dashboard["policy"]),
        }

    @staticmethod
    def score_signal(score: float) -> str:

        if score >= 85:
            return "🟢 매우 강함"

        if score >= 70:
            return "🟢 강함"

        if score >= 60:
            return "🟡 보통"

        if score >= 40:
            return "🟠 약함"

        return "🔴 매우 약함"

    @staticmethod
    def market_signal(score: float) -> str:

        if score >= 90:
            return "🚀 매우 강세"

        if score >= 80:
            return "📈 강세"

        if score >= 70:
            return "🌱 회복"

        if score >= 60:
            return "➖ 보합"

        if score >= 50:
            return "📉 둔화"

        return "🔻 침체"

    @staticmethod
    def leading_signal(score: float) -> str:

        if score >= 85:
            return "⬆ 상승 가능성 높음"

        if score >= 70:
            return "↗ 회복 진행"

        if score >= 60:
            return "→ 중립"

        if score >= 40:
            return "↘ 약세"

        return "⬇ 하락 가능성"

    @staticmethod
    def risk_signal(score: float) -> str:

        if score >= 90:
            return "🟢 매우 안전"

        if score >= 80:
            return "🟢 안전"

        if score >= 70:
            return "🟡 보통"

        if score >= 60:
            return "🟠 주의"

        return "🔴 위험"
