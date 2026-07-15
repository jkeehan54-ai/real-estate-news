# indicator_engine.py


"""
BRN Indicator Engine

Indicator 생성 및 관리
"""

from __future__ import annotations

from pathlib import Path

import yaml

from modules.normalization_engine import NormalizationEngine


class IndicatorEngine:
    """Indicator 생성 엔진"""

    def __init__(
        self,
        catalog_path: str = "config/indicator_catalog.yaml",
    ):

        self.catalog = self._load_catalog(catalog_path)

    def _load_catalog(self, path: str) -> dict:

        with open(Path(path), encoding="utf-8") as f:
            return yaml.safe_load(f)

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

        raise KeyError(f"Indicator not found : {indicator_id}")

    def create(
        self,
        indicator_id: str,
        value: float,
        region: str = "전국",
    ) -> dict:

        info = self._find(indicator_id)

        score = NormalizationEngine.normalize(
            indicator_id,
            value,
        )

        return {
            "id": info["id"],
            "name": info["name"],
            "category": info["category"],
            "source": info["source"],
            "region": region,
            "value": value,
            "score": score,
            "weight": info["weight"],
            "weighted_score": round(
                score * info["weight"],
                2,
            ),
        }

    def create_many(self, values: dict):

        indicators = []

        for indicator_id, value in values.items():

            indicators.append(

                self.create(
                    indicator_id,
                    value,
                )

            )

        return indicators

    def category(self, category: str):

        category = category.lower()

        if category not in self.catalog:

            return []

        return self.catalog[category]

    def ids(self):

        result = []

        for items in self.catalog.values():

            for item in items:

                result.append(item["id"])

        return sorted(result)
