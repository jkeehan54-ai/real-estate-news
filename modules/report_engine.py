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
from modules.history_engine import HistoryEngine


class ReportEngine:

    def __init__(self):

        self.dashboard_engine = DashboardEngine()
        self.signal_engine = MarketSignalEngine()
        self.history_engine = HistoryEngine()

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

        self.history_engine.save_report(report)

        return report

    def summary(
        self,
        dashboard: dict,
        signals: dict,
    ) -> str:

        return (
            f"[{dashboard['region']}]\n"
            f"BRN Index : {dashboard['brn_index']:.1f} "
            f"({dashboard['brn_grade']})\n"
            f"시장상태 : {signals['market']}\n"
            f"Health : {dashboard['health']:.1f}\n"
            f"Leading : {dashboard['leading']:.1f}\n"
            f"Risk : {dashboard['risk']:.1f}\n"
            f"전망 : {signals['leading']}\n"
            f"위험 : {signals['risk']}"
        )
