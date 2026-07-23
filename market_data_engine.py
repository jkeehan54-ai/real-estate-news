"""
BRN Market Data Engine

KB
REB
MOLIT
BOK
Auction

각 데이터 수집 모듈을 하나로 통합한다.
"""

from __future__ import annotations

from modules.kb_market import (
    get_market_brief,
    get_market_data,
)
from modules.reb_market import REBMarket


class MarketDataEngine:

    def __init__(self):

        self.reb = REBMarket()

    def load_reb_json(self, filename):

        self.reb.load_json(filename)

    def build(self):

        values = {}

        # -------------------------------------------------
        # REB
        # -------------------------------------------------

        try:

            reb = self.reb.latest()

        except Exception:

            reb = {}

        if "전국" in reb:
            values["REB_NATION_INDEX"] = reb["전국"]

        if "서울" in reb:
            values["REB_SEOUL_INDEX"] = reb["서울"]

        if "부산" in reb:
            values["REB_BUSAN_INDEX"] = reb["부산"]

        # -------------------------------------------------
        # KB
        # -------------------------------------------------

        try:

            kb = get_market_data()

            values["KB_NATION_CHANGE"] = kb["nation_change"]
            values["KB_SEOUL_CHANGE"] = kb["seoul_change"]
            values["KB_BUSAN_CHANGE"] = kb["busan_change"]

            values["KB_SELLER"] = kb["seller"]
            values["KB_BUYER"] = kb["buyer"]

            values["KB_WEEKS"] = kb["weeks"]
            values["KB_TREND"] = kb["trend"]

        except Exception:

            pass

        # HTML 뉴스 브리핑용
        values["KB_MARKET"] = get_market_brief()

        return values
