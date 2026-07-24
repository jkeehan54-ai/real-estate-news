# modules/market_data_engine.py

from modules.kb_market import get_market_brief
from modules.reb_market import REBMarket


class MarketDataEngine:
    def __init__(self):
        self.reb = REBMarket()

    def build(self):
        indicators = {}

        reb = self.reb.get()

        if reb:
            indicators["PRICE_INDEX"] = reb.get("전국", 0.0)
            indicators["SEOUL_PRICE_INDEX"] = reb.get("서울", 0.0)
            indicators["BUSAN_PRICE_INDEX"] = reb.get("부산", 0.0)
        else:
            indicators["PRICE_INDEX"] = 0.0
            indicators["SEOUL_PRICE_INDEX"] = 0.0
            indicators["BUSAN_PRICE_INDEX"] = 0.0

        indicators["KB_MARKET"] = get_market_brief()

        return indicators
