"""
REB Market Engine

한국부동산원(R-ONE) 시장지수

JSON 파일을 읽어 지역별 최신 매매가격지수를 반환한다.
"""

from __future__ import annotations

import json
from pathlib import Path


class REBMarket:
    """한국부동산원 시장지수"""

    def __init__(self):

        self.data = None

    def load_json(self, filename: str | Path):

        filename = Path(filename)

        if not filename.exists():
            raise FileNotFoundError(filename)

        with open(filename, encoding="utf-8") as f:
            self.data = json.load(f)

        return self.data

    def latest(self) -> dict[str, float]:

        if self.data is None:
            raise RuntimeError(
                "JSON이 로드되지 않았습니다."
            )

        rows = (
            self.data
            .get("sheet", {})
            .get("1", {})
            .get("data", {})
        )

        result: dict[str, float] = {}

        for row in rows.values():

            if not isinstance(row, dict):
                continue

            region = row.get("1")

            if not region:
                continue

            value = row.get("14")

            if value in ("", None):
                continue

            try:
                value = float(
                    str(value).replace(",", "")
                )
            except (ValueError, TypeError):
                continue

            result[region] = value

        return result
