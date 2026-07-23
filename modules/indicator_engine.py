# indicator_engine.py


from textwrap import dedent

content = dedent(r'''\
"""
BRN Indicator Engine

Indicator 생성 및 관리
(Starter template for BRN 1.0)

NOTE:
- Existing API is preserved.
- Expand CATALOG by adding new indicator entries.
"""

from __future__ import annotations

from modules.normalization_engine import NormalizationEngine


class IndicatorEngine:
    """Indicator 생성 엔진"""

    CATALOG = {
        "price": [
            {"id": "PRICE_INDEX", "name": "전국 매매가격지수", "source": "KB", "weight": 1.0},
            {"id": "SEOUL_PRICE_INDEX", "name": "서울 매매가격지수", "source": "KB", "weight": 1.0},
            {"id": "BUSAN_PRICE_INDEX", "name": "부산 매매가격지수", "source": "KB", "weight": 1.0},
            {"id": "REB_PRICE_INDEX", "name": "한국부동산원 매매가격지수", "source": "REB", "weight": 1.0},
        ],
        "demand": [
            {"id": "DEMAND_VOLUME", "name": "거래량", "source": "국토교통부", "weight": 1.0},
            {"id": "DEMAND_JEONSE", "name": "전세가율", "source": "KB", "weight": 1.0},
            {"id": "DEMAND_BUYER", "name": "매수우위지수", "source": "KB", "weight": 1.0},
            {"id": "DEMAND_SELLER", "name": "매도우위지수", "source": "KB", "weight": 1.0},
            {"id": "DEMAND_AUCTION", "name": "경매낙찰률", "source": "법원경매", "weight": 1.0},
        ],
        "supply": [
            {"id": "SUPPLY_PERMIT", "name": "인허가", "source": "국토교통부", "weight": 1.0},
            {"id": "SUPPLY_START", "name": "착공", "source": "국토교통부", "weight": 1.0},
            {"id": "SUPPLY_UNSOLD", "name": "미분양", "source": "국토교통부", "weight": 1.0},
        ],
        "finance": [
            {"id": "FINANCE_RATE", "name": "기준금리", "source": "한국은행", "weight": 1.0},
        ],
        "policy": [
            {"id": "POLICY_SCORE", "name": "정책지수", "source": "BRN", "weight": 1.0},
        ],
        "risk": [
            {"id": "RISK_PF", "name": "PF위험도", "source": "BRN", "weight": 1.0},
        ],
    }

    def __init__(self):
        self.catalog = self.CATALOG

    def _find(self, indicator_id: str) -> dict:
        indicator_id = indicator_id.upper()
        for category, indicators in self.catalog.items():
            for indicator in indicators:
                if indicator["id"].upper() == indicator_id:
                    return {
                        "id": indicator["id"],
                        "name": indicator["name"],
                        "category": category,
                        "source": indicator["source"],
                        "weight": indicator.get("weight", 1.0),
                    }
        raise KeyError(f"Indicator not found: {indicator_id}")

    def create(self, indicator_id: str, value: float, region: str = "전국") -> dict:
        info = self._find(indicator_id)
        score = NormalizationEngine.normalize(indicator_id, value)
        return {
            "id": info["id"],
            "name": info["name"],
            "category": info["category"],
            "source": info["source"],
            "region": region,
            "value": value,
            "score": score,
            "weight": info["weight"],
            "weighted_score": round(score * info["weight"], 2),
        }

    def create_many(self, values: dict, region: str = "전국"):
        return [self.create(k, v, region) for k, v in values.items()]

    def category(self, category: str):
        return self.catalog.get(category.lower(), [])

    def ids(self):
        result = []
        for items in self.catalog.values():
            result.extend(item["id"] for item in items)
        return sorted(result)
''')

path="/mnt/data/indicator_engine.py"
with open(path,"w",encoding="utf-8") as f:
    f.write(content)

print(path)
