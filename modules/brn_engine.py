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
    """
    BRN 통합 엔진

    처리 순서

        MarketDataEngine
                │
                ▼
        IndicatorEngine
                │
                ▼
         ReportEngine
                │
                ▼
        ForecastEngine
    """

    def __init__(self):

        self.indicator_engine = IndicatorEngine()
        self.report_engine = ReportEngine()
        self.forecast_engine = ForecastEngine()

    def build(
        self,
        values: dict,
        region: str = "전국",
    ) -> dict:

        # -------------------------------------------------
        # Indicator 생성
        # -------------------------------------------------

        indicators = self.indicator_engine.create_many(
            values=values,
            region=region,
        )

        # -------------------------------------------------
        # Dashboard / Signal / Summary 생성
        # -------------------------------------------------

        report = self.report_engine.build(
            indicators=indicators,
            region=region,
        )

        # -------------------------------------------------
        # Forecast 생성
        # (향후 BRN 지표를 활용할 수 있도록 indicators 전달)
        # -------------------------------------------------

        forecast = self.forecast_engine.build(
            indicators=indicators,
            region=region,
        )

        # -------------------------------------------------
        # 최종 결과
        # -------------------------------------------------

        return {
            "region": region,
            "indicators": indicators,
            "dashboard": report.get("dashboard", {}),
            "signals": report.get("signals", []),
            "summary": report.get("summary", ""),
            "forecast": forecast,
        }
