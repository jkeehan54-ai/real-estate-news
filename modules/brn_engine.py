```python
# modules/brn_engine.py

"""
BRN Engine v2

MarketDataEngine에서 생성한 값을 이용하여
BRN 요약을 생성한다.

KB 데이터 취득 실패 시
실제 0.0% 시장 데이터와 구분한다.
"""

from __future__ import annotations


class BRNEngine:

    # ========================================================
    # BUILD
    # ========================================================

    def build(
        self,
        values: dict,
        region: str = "전국",
    ) -> dict:

        # ----------------------------------------------------
        # KB 원본 상태
        # ----------------------------------------------------

        market = values.get(
            "KB_MARKET",
            {},
        )

        kb_ok = market.get(
            "ok",
            False,
        )

        # ----------------------------------------------------
        # KB 데이터
        # ----------------------------------------------------

        nation = values.get(
            "KB_NATION_CHANGE",
            0,
        )

        seoul = values.get(
            "KB_SEOUL_CHANGE",
            0,
        )

        busan = values.get(
            "KB_BUSAN_CHANGE",
            0,
        )

        buyer = values.get(
            "KB_BUYER",
            0,
        )

        seller = values.get(
            "KB_SELLER",
            0,
        )

        weeks = values.get(
            "KB_WEEKS",
            0,
        )

        trend = values.get(
            "KB_TREND",
            "",
        )

        # ----------------------------------------------------
        # KB 실패
        # ----------------------------------------------------

        if not kb_ok:

            summary = (
                "KB 시장 데이터를 "
                "불러오지 못했습니다."
            )

            signals = {
                "market": "데이터없음",
                "demand": "데이터없음",
            }

            forecast = {
                "comment": (
                    "KB 시장 데이터가 없어 "
                    "시장 전망을 산출할 수 없습니다."
                ),
                "trend": "",
            }

        # ----------------------------------------------------
        # KB 정상
        # ----------------------------------------------------

        else:

            summary = self.make_summary(
                nation,
                seoul,
                busan,
                buyer,
                seller,
                weeks,
                trend,
            )

            signals = self.make_signals(
                nation,
                buyer,
                seller,
            )

            forecast = self.make_forecast(
                nation,
                trend,
            )

        # ----------------------------------------------------
        # RESULT
        # ----------------------------------------------------

        return {
            "region": region,

            "kb_ok": kb_ok,

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
                "kb_ok": kb_ok,
            },

            "signals": signals,

            "forecast": forecast,
        }

    # ========================================================
    # SUMMARY
    # ========================================================

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

        trend_word = (
            trend
            if trend
            else "변동"
        )

        return (
            f"전국 아파트 매매가격은 "
            f"{nation}% "
            f"{trend_word}했습니다. "
            f"{weeks}주 연속 "
            f"{trend_word}세입니다. "
            f"서울 {seoul}%, "
            f"부산 {busan}%, "
            f"매수우위 {buyer}%, "
            f"매도우위 {seller}%입니다."
        )

    # ========================================================
    # SIGNALS
    # ========================================================

    def make_signals(
        self,
        nation,
        buyer,
        seller,
    ):

        if nation >= 0.20:

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

    # ========================================================
    # FORECAST
    # ========================================================

    def make_forecast(
        self,
        nation,
        trend,
    ):

        if nation >= 0.20:

            comment = (
                "상승세 지속 가능성이 있습니다."
            )

        elif nation > 0:

            comment = (
                "완만한 상승 흐름이 예상됩니다."
            )

        else:

            comment = (
                "당분간 관망세가 예상됩니다."
            )

        return {
            "comment": comment,
            "trend": trend,
        }
```
