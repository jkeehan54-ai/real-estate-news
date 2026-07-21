# brn_engine.py


"""
BRN Engine

BRN 전체 실행 엔진
"""

from __future__ import annotations

from modules.indicator_engine import IndicatorEngine
from modules.report_engine import ReportEngine
from modules.forecast_engine import ForecastEngine


class BRNEngine:

    def __init__(self):

        self.indicator_engine = IndicatorEngine()
        self.report_engine = ReportEngine()
        self.forecast_engine = ForecastEngine()

    def build(
        self,
        values: dict,
        region: str = "전국",
    ) -> dict:

        indicators = self.indicator_engine.create_many(
            values,
            region=region,
        )

        report = self.report_engine.build(
            indicators=indicators,
            region=region,
        )

        forecast = self.forecast_engine.build(
            region=region,
        )

        return {
            "dashboard": report["dashboard"],
            "signals": report["signals"],
            "summary": report["summary"],
            "forecast": forecast,
        }
