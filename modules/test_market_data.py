from modules.market_data_engine import MarketDataEngine

engine = MarketDataEngine()

engine.load_reb_json("(월) 매매가격지수_주택종합.json")

print(engine.build())
