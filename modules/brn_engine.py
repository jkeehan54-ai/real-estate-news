# brn_engine.py


"""
BRN Engine v2

MarketDataEngine에서 생성한 값을 이용하여
BRN 요약을 생성한다.
"""

from __future__ import annotations


class BRNEngine:

    def build(
        self,
        values: dict,
        region: str = "전국",
    ) -> dict:

        nation = values.get("KB_NATION_CHANGE", 0)
        seoul = values.get("KB_SEOUL_CHANGE", 0)
        busan = values.get("KB_BUSAN_CHANGE", 0)

        buyer = values.get("KB_BUYER", 0)
        seller = values.get("KB_SELLER", 0)

        weeks = values.get("KB_WEEKS", 0)
        trend = values.get("KB_TREND", "")

        market = values.get("KB_MARKET", {})

        summary = self.make_summary(
            nation,
            seoul,
            busan,
            buyer,
            seller,
            weeks,
            trend,
        )

        return {

            "region": region,

            "summary": summary,

            "market": market,

            "dashboard": {

                "nation": nation,
                "seoul": seoul,
                "busan": busan,
                "buyer": buyer,
                "seller": seller,
                "weeks": weeks,
                "trend": trend,

            },

            "signals": self.make_signals(
                nation,
                buyer,
                seller,
            ),

            "forecast": self.make_forecast(
                nation,
                trend,
            ),

        }

    def make_summary(
        self,
        nation,
        seoul,
        busan,
        buyer,
        seller,
        weeks,
        trend,
    ):

        return (
            f"전국 아파트 매매가격은 {nation}% "
            f"{trend}했습니다. "
            f"{weeks}주 연속 {trend}세입니다. "
            f"서울 {seoul}%, "
            f"부산 {busan}%, "
            f"매수우위 {buyer}%, "
            f"매도우위 {seller}%입니다."
        )

    def make_signals(
        self,
        nation,
        buyer,
        seller,
    ):

        if nation > 0.15:
            market = "강세"

        elif nation > 0:
            market = "보합"

        else:
            market = "약세"

        if buyer > seller:
            demand = "매수우위"

        elif seller > buyer:
            demand = "매도우위"

        else:
            demand = "균형"

        return {

            "market": market,
            "demand": demand,

        }

    def make_forecast(
        self,
        nation,
        trend,
    ):

        if nation > 0.2:

            text = "상승세 지속 가능성이 있습니다."

        elif nation > 0:

            text = "완만한 상승 흐름이 예상됩니다."

        else:

            text = "당분간 관망세가 예상됩니다."

        return {

            "comment": text,
            "trend": trend,

        }
