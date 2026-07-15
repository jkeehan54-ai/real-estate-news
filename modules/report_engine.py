# report_engine.py


"""
BRN Report Engine

Dashboard 결과를 이용하여
일일 시장 리포트를 생성한다.
"""

from __future__ import annotations

from datetime import datetime

from modules.dashboard_engine import DashboardEngine
from modules.market_signal_engine import MarketSignalEngine


class ReportEngine:

    def __init__(self):

        self.dashboard_engine = DashboardEngine()
        self.signal_engine = MarketSignalEngine()

    def build(
        self,
        indicators: list[dict],
        region: str = "전국",
    ) -> dict:

        dashboard = self.dashboard_engine.build(
            indicators=indicators,
            region=region,
        )

        signals = self.signal_engine.build(
            dashboard,
        )

        report = {
            "created_at": datetime.now().strftime(
                "%Y-%m-%d %H:%M"
            ),
            "dashboard": dashboard,
            "signals": signals,
            "summary": self.summary(
                dashboard,
                signals,
            ),
        }

        return report

    def summary(
        self,
        dashboard: dict,
        signals: dict,
    ) -> str:

        return (
            f"{dashboard['region']} 시장은 "
            f"{signals['market']} 상태입니다. "
            f"선행지표는 "
            f"{signals['leading']}이며 "
            f"위험도는 "
            f"{signals['risk']}입니다."
        )
