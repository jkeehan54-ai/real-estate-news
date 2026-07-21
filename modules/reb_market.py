"""
REB Market Engine

한국부동산원(R-ONE) 시장지수

현재는 JSON 구조를 기준으로 작성되었으며
향후 OpenAPI와 동일한 형태로 사용할 수 있다.
"""

from __future__ import annotations

import json


class REBMarket:

    def __init__(self):

        self.data = None

    def load_json(self, filename):

        with open(filename, encoding="utf-8") as f:
            self.data = json.load(f)

        return self.data

    def latest(self):

        if self.data is None:
            raise RuntimeError("JSON이 로드되지 않았습니다.")

        rows = self.data["sheet"]["1"]["data"]

        result = {}

        for row in rows.values():

            if not isinstance(row, dict):
                continue

            region = row.get("1")

            if region is None:
                continue

            value = row.get("14")

            if value in ("", None):
                continue

            try:
                value = float(value)
            except Exception:
                continue

            result[region] = value

        return result
