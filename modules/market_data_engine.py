# modules/market_data_engine.py
# ============================================================
# BRN Market Data Engine
# Sprint 1-3
# (1/3)
# ============================================================

"""
BRN Market Data Engine

KB
REB(OpenAPI)
BOK
공공데이터

모든 시장 데이터를 하나의 values(dict)로 통합한다.
"""

from __future__ import annotations

from modules.reb_market import REBMarket
from modules.kb_market import get_market_data


class MarketDataEngine:

    def __init__(self):

        self.values = {}

        self.reb = REBMarket()

    # ---------------------------------------------------------
    # REB
    # ---------------------------------------------------------

    def load_reb(self):

        """
        REB OpenAPI 호출

        최신 데이터를 다운로드하여
        reb_market.json 생성
        """

        data = self.reb.update()

        return data

    # ---------------------------------------------------------

    def build_reb(self):

        reb = self.load_reb()

        price = reb.get(
            "price_index",
            {},
        )

        jeonse = reb.get(
            "jeonse_index",
            {},
        )

        average = reb.get(
            "average_price",
            {},
        )

        median = reb.get(
            "median_price",
            {},
        )

        self.values.update(
            {

                # --------------------
                # REB
                # --------------------

                "REB_MONTH":
                    price.get(
                        "month",
                        "",
                    ),

                "REB_PRICE_NATION":
                    price.get(
                        "nation",
                        0.0,
                    ),

                "REB_PRICE_SEOUL":
                    price.get(
                        "seoul",
                        0.0,
                    ),

                "REB_PRICE_BUSAN":
                    price.get(
                        "busan",
                        0.0,
                    ),

                "REB_JEONSE_NATION":
                    jeonse.get(
                        "nation",
                        0.0,
                    ),

                "REB_JEONSE_SEOUL":
                    jeonse.get(
                        "seoul",
                        0.0,
                    ),

                "REB_JEONSE_BUSAN":
                    jeonse.get(
                        "busan",
                        0.0,
                    ),

                "REB_AVG_NATION":
                    average.get(
                        "nation",
                        0.0,
                    ),

                "REB_AVG_SEOUL":
                    average.get(
                        "seoul",
                        0.0,
                    ),

                "REB_AVG_BUSAN":
                    average.get(
                        "busan",
                        0.0,
                    ),

                "REB_MEDIAN_NATION":
                    median.get(
                        "nation",
                        0.0,
                    ),

                "REB_MEDIAN_SEOUL":
                    median.get(
                        "seoul",
                        0.0,
                    ),

                "REB_MEDIAN_BUSAN":
                    median.get(
                        "busan",
                        0.0,
                    ),

            }
        )

    # ---------------------------------------------------------
    # KB
    # ---------------------------------------------------------

    def build_kb(self):

        """
        KB Market Data

        modules.kb_market.get_market_data()
        에서 실제 KB 시장 데이터를 가져온다.

        반환 구조:

            {
                "date": "...",
                "nation_change": ...,
                "weeks": ...,
                "trend": "...",
                "seller": ...,
                "buyer": ...,
                "seoul_change": ...,
                "busan_change": ...,
            }

        BRNEngine에서 사용하는
        KB_* 형식으로 변환하여
        self.values에 저장한다.
        """

        data = get_market_data()

        # -----------------------------------------------------
        # 실제 KB 데이터
        # -----------------------------------------------------

        self.values.update(
            {

                "KB_DATE":
                    data.get(
                        "date",
                        "",
                    ),

                "KB_NATION_CHANGE":
                    data.get(
                        "nation_change",
                        0.0,
                    ),

                "KB_SEOUL_CHANGE":
                    data.get(
                        "seoul_change",
                        0.0,
                    ),

                "KB_BUSAN_CHANGE":
                    data.get(
                        "busan_change",
                        0.0,
                    ),

                "KB_BUYER":
                    data.get(
                        "buyer",
                        0.0,
                    ),

                "KB_SELLER":
                    data.get(
                        "seller",
                        0.0,
                    ),

                "KB_WEEKS":
                    data.get(
                        "weeks",
                        0,
                    ),

                "KB_TREND":
                    data.get(
                        "trend",
                        "",
                    ),

                "KB_MARKET":
                    data,

            }
        )

    # ---------------------------------------------------------
    # BOK
    # ---------------------------------------------------------

    def build_bok(self):

        """
        한국은행 ECOS

        추후 BOKEngine 연동
        """

        self.values.setdefault(
            "BOK_BASE_RATE",
            0.0,
        )

    # ---------------------------------------------------------
    # PUBLIC
    # ---------------------------------------------------------

    def build_public(self):

        """
        공공데이터포털

        추후 국토부/통계청 데이터 연동
        """

        self.values.setdefault(
            "PUBLIC_PERMIT",
            0.0,
        )

        self.values.setdefault(
            "PUBLIC_START",
            0.0,
        )

        self.values.setdefault(
            "PUBLIC_UNSOLD",
            0.0,
        )


# modules/market_data_engine.py
# ============================================================
# BRN Market Data Engine
# Sprint 1-3
# (2/3)
# ============================================================

    # ---------------------------------------------------------
    # BUILD
    # ---------------------------------------------------------

    def build(self):

        """
        전체 시장 데이터 생성

        순서:

            REB
            ↓
            KB
            ↓
            BOK
            ↓
            PUBLIC
        """

        self.values = {}

        # -----------------------------------------------------
        # REB
        # -----------------------------------------------------

        try:

            self.build_reb()

        except Exception as exc:

            print(
                "[REB ERROR]",
                repr(exc),
            )

        # -----------------------------------------------------
        # KB
        # -----------------------------------------------------

        try:

            self.build_kb()

        except Exception as exc:

            print(
                "[KB ERROR]",
                repr(exc),
            )

            # KB 전체 실패 시에도
            # 나머지 Engine은 계속 실행한다.

            self.values.setdefault(
                "KB_DATE",
                "",
            )

            self.values.setdefault(
                "KB_NATION_CHANGE",
                0.0,
            )

            self.values.setdefault(
                "KB_SEOUL_CHANGE",
                0.0,
            )

            self.values.setdefault(
                "KB_BUSAN_CHANGE",
                0.0,
            )

            self.values.setdefault(
                "KB_BUYER",
                0.0,
            )

            self.values.setdefault(
                "KB_SELLER",
                0.0,
            )

            self.values.setdefault(
                "KB_WEEKS",
                0,
            )

            self.values.setdefault(
                "KB_TREND",
                "",
            )

            self.values.setdefault(
                "KB_MARKET",
                {},
            )

        # -----------------------------------------------------
        # BOK
        # -----------------------------------------------------

        try:

            self.build_bok()

        except Exception as exc:

            print(
                "[BOK ERROR]",
                repr(exc),
            )

        # -----------------------------------------------------
        # PUBLIC
        # -----------------------------------------------------

        try:

            self.build_public()

        except Exception as exc:

            print(
                "[PUBLIC DATA ERROR]",
                repr(exc),
            )

        return self.values

    # ---------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------

    def summary(self):

        print()

        print(
            "==================================="
        )

        print(
            "BRN Market Data"
        )

        print(
            "==================================="
        )

        # -----------------------------------------------------
        # KB
        # -----------------------------------------------------

        print(
            "KB 기준일 :",
            self.values.get(
                "KB_DATE",
                "",
            ),
        )

        print(
            "KB 전국 변동률 :",
            self.values.get(
                "KB_NATION_CHANGE",
                0,
            ),
        )

        print(
            "KB 서울 변동률 :",
            self.values.get(
                "KB_SEOUL_CHANGE",
                0,
            ),
        )

        print(
            "KB 부산 변동률 :",
            self.values.get(
                "KB_BUSAN_CHANGE",
                0,
            ),
        )

        print(
            "KB 매수우위 :",
            self.values.get(
                "KB_BUYER",
                0,
            ),
        )

        print(
            "KB 매도우위 :",
            self.values.get(
                "KB_SELLER",
                0,
            ),
        )

        print(
            "KB 연속주수 :",
            self.values.get(
                "KB_WEEKS",
                0,
            ),
        )

        print(
            "KB 추세 :",
            self.values.get(
                "KB_TREND",
                "",
            ),
        )

        print()

        # -----------------------------------------------------
        # REB
        # -----------------------------------------------------

        print(
            "REB 기준월 :",
            self.values.get(
                "REB_MONTH",
                "",
            ),
        )

        print(
            "REB 전국 매매지수 :",
            self.values.get(
                "REB_PRICE_NATION",
                0,
            ),
        )

        print(
            "REB 서울 매매지수 :",
            self.values.get(
                "REB_PRICE_SEOUL",
                0,
            ),
        )

        print(
            "REB 부산 매매지수 :",
            self.values.get(
                "REB_PRICE_BUSAN",
                0,
            ),
        )

        print()

        print(
            "REB 전국 전세지수 :",
            self.values.get(
                "REB_JEONSE_NATION",
                0,
            ),
        )

        print(
            "REB 서울 전세지수 :",
            self.values.get(
                "REB_JEONSE_SEOUL",
                0,
            ),
        )

        print(
            "REB 부산 전세지수 :",
            self.values.get(
                "REB_JEONSE_BUSAN",
                0,
            ),
        )

        print()

        print(
            "REB 전국 평균가격 :",
            self.values.get(
                "REB_AVG_NATION",
                0,
            ),
        )

        print(
            "REB 전국 중위가격 :",
            self.values.get(
                "REB_MEDIAN_NATION",
                0,
            ),
        )

        print(
            "==================================="
        )

        return self.values


# ============================================================
# DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":

    engine = MarketDataEngine()

    engine.build()

    engine.summary()







