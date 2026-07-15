# dashboard_engine.py


"""
BRN Dashboard Engine

Indicator Engine
Market Health Engine
Leading Engine
Risk Engine

결과를 하나의 Dashboard 객체로 생성한다.
"""

from __future__ import annotations

from datetime import datetime

from modules.market_health_engine import MarketHealthEngine
from modules.leading_engine import LeadingEngine
from modules.risk_engine import RiskEngine


class DashboardEngine:
    """
    BRN Dashboard 생성
    """

    def __init__(self):

        self.health_engine = MarketHealthEngine()
        self.leading_engine = LeadingEngine()
        self.risk_engine = RiskEngine()

    def build(
        self,
        indicators: list[dict],
        region: str = "전국",
    ) -> dict:

        health = self.health_engine.calculate(indicators)

        leading = self.leading_engine.calculate(indicators)

        risk = self.risk_engine.calculate(indicators)

        dashboard = {
            "region": region,
            "updated_at": datetime.now().strftime(
                "%Y-%m-%d %H:%M"
            ),

            "health": health["health"],
            "health_grade": health["grade"],

            "leading": leading["leading"],
            "leading_signal": leading["signal"],

            "risk": risk["risk"],
            "risk_grade": risk["grade"],

            "price": health["price"],
            "demand": health["demand"],
            "supply": health["supply"],
            "finance": health["finance"],
            "policy": health["policy"],

            "health_detail": health,
            "leading_detail": leading,
            "risk_detail": risk,
        }

        return dashboard

    def summary(
        self,
        dashboard: dict,
    ) -> str:

        return (
            f"[{dashboard['region']}] "
            f"Health {dashboard['health']:.1f} "
            f"({dashboard['health_grade']}), "
            f"Leading {dashboard['leading']:.1f}, "
            f"Risk {dashboard['risk']:.1f}"
        )
