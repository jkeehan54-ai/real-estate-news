from modules.reb_market import REBMarket

reb = REBMarket()

reb.load_json("(월) 매매가격지수_주택종합.json")

print(reb.latest())
