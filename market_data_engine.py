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

from modules.kb_market import get_market_brief
from modules.reb_market import REBMarket


class MarketDataEngine:

    def __init__(self):

        self.reb = REBMarket()

    def load_reb_json(self, filename):

        self.reb.load_json(filename)

    def build(self):

        reb = self.reb.latest()

        values = {}

        # --------------------------
        # REB
        # --------------------------

        if "전국" in reb:
            values["PRICE_INDEX"] = reb["전국"]

        if "서울" in reb:
            values["SEOUL_PRICE_INDEX"] = reb["서울"]

        if "부산" in reb:
            values["BUSAN_PRICE_INDEX"] = reb["부산"]

        # --------------------------
        # KB
        # --------------------------

        values["KB_MARKET"] = get_market_brief()

        return values
