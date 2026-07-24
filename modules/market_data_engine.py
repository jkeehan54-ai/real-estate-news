# modules/market_data_engine.py
# (1/3)

"""
BRN Market Data Engine

KB
REB(OpenAPI)
BOK
공공데이터

모든 시장 데이터를 하나의 values(dict)로 통합한다.
"""

from __future__ import annotations

import os

from modules.reb_market import REBMarket


class MarketDataEngine:

    def __init__(self):

        self.values = {}

        self.reb = REBMarket()

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

# modules/market_data_engine.py
# (2/3)

    # ---------------------------------------------------------

    def build_kb(self):

        """
        KB 데이터

        현재 BRNEngine에서 사용하는 값은
        generate_news.py에서 생성된 값을 그대로 유지한다.
        """

        defaults = {

            "KB_NATION_CHANGE": 0.0,
            "KB_SEOUL_CHANGE": 0.0,
            "KB_BUSAN_CHANGE": 0.0,

            "KB_BUYER": 0.0,
            "KB_SELLER": 0.0,

            "KB_WEEKS": 0,

            "KB_TREND": "보합",

            "KB_MARKET": {},

        }

        for key, value in defaults.items():

            self.values.setdefault(
                key,
                value,
            )

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

    # ---------------------------------------------------------

    def build(self):

        self.values = {}

        self.build_reb()

        self.build_kb()

        self.build_bok()

        self.build_public()

        return self.values



# modules/market_data_engine.py
# (3/3)

    # ---------------------------------------------------------

    def summary(self):

        print()

        print("===================================")
        print("BRN Market Data")
        print("===================================")

        print(
            "REB 기준월 :",
            self.values.get(
                "REB_MONTH",
                "",
            ),
        )

        print(
            "전국 매매지수 :",
            self.values.get(
                "REB_PRICE_NATION",
                0,
            ),
        )

        print(
            "서울 매매지수 :",
            self.values.get(
                "REB_PRICE_SEOUL",
                0,
            ),
        )

        print(
            "부산 매매지수 :",
            self.values.get(
                "REB_PRICE_BUSAN",
                0,
            ),
        )

        print()

        print(
            "전국 전세지수 :",
            self.values.get(
                "REB_JEONSE_NATION",
                0,
            ),
        )

        print(
            "서울 전세지수 :",
            self.values.get(
                "REB_JEONSE_SEOUL",
                0,
            ),
        )

        print(
            "부산 전세지수 :",
            self.values.get(
                "REB_JEONSE_BUSAN",
                0,
            ),
        )

        print()

        print(
            "전국 평균가격 :",
            self.values.get(
                "REB_AVG_NATION",
                0,
            ),
        )

        print(
            "전국 중위가격 :",
            self.values.get(
                "REB_MEDIAN_NATION",
                0,
            ),
        )

        print("===================================")

        return self.values


if __name__ == "__main__":

    engine = MarketDataEngine()

    engine.build()

    engine.summary()

