# modules/reb_market.py
# (1/3)

"""
REB Market Engine

한국부동산원(R-ONE) OpenAPI 자동 수집

기능
----------------------------------------------------
- OpenAPI 호출
- 최신 월 자동 검색
- 매매지수
- 전세지수
- 평균가격
- 중위가격
- reb_market.json 저장
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import requests


class REBMarket:

    BASE_URL = "https://www.reb.or.kr/r-one/openapi"

    TABLES = {

        "price_index": {
            "STATBL_ID": "A_2024_00178",
            "DTACYCLE_CD": "MM",
        },

        "jeonse_index": {
            "STATBL_ID": "A_2024_00182",
            "DTACYCLE_CD": "MM",
        },

        "average_price": {
            "STATBL_ID": "A_2024_00188",
            "DTACYCLE_CD": "MM",
        },

        "median_price": {
            "STATBL_ID": "A_2024_00189",
            "DTACYCLE_CD": "MM",
        },

    }

    REGION_MAP = {

        "전국": "nation",
        "서울": "seoul",
        "부산": "busan",

    }

    def __init__(
        self,
        api_key: str | None = None,
        timeout: int = 30,
    ):

        self.api_key = (
            api_key
            or os.getenv("REB_API_KEY")
            or ""
        )

        if not self.api_key:
            raise RuntimeError(
                "REB_API_KEY 환경변수가 없습니다."
            )

        self.timeout = timeout

        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent":
                "BRN/2.0"
            }
        )

        self.data = {}

    # -----------------------------------------------------

    def _current_period(self):

        year = datetime.now().year

        return (
            f"{year}01",
            f"{year}12",
        )

    # -----------------------------------------------------

    def _request(
        self,
        statbl_id,
        cycle,
    ):

        start, end = self._current_period()

        params = {

            "KEY": self.api_key,

            "Type": "json",

            "pIndex": 1,

            "pSize": 5000,

            "STATBL_ID": statbl_id,

            "DTACYCLE_CD": cycle,

            "START_WRTTIME": start,

            "END_WRTTIME": end,

        }

        url = (
            self.BASE_URL
            + "/SttsApiTblData.do"
        )

        r = self.session.get(
            url,
            params=params,
            timeout=self.timeout,
        )

        r.raise_for_status()

        return r.json()

    # -----------------------------------------------------

    @staticmethod
    def _rows(response):

        if "SttsApiTblData" not in response:
            return []

        body = response["SttsApiTblData"]

        if len(body) < 2:
            return []

        return body[1].get(
            "row",
            [],
        )

    # -----------------------------------------------------

    @staticmethod
    def _latest_month(rows):

        latest = ""

        for row in rows:

            d = row.get(
                "WRTTIME_IDTFR_ID",
                "",
            )

            if d > latest:
                latest = d

        return latest

    # -----------------------------------------------------

    @staticmethod
    def _filter_latest(
        rows,
        latest,
    ):

        result = []

        for row in rows:

            if (
                row.get(
                    "WRTTIME_IDTFR_ID"
                )
                == latest
            ):

                result.append(row)

        return result

# modules/reb_market.py
# (2/3)

    # -----------------------------------------------------

    def _extract_region(
        self,
        rows,
    ):

        latest = self._latest_month(
            rows,
        )

        rows = self._filter_latest(
            rows,
            latest,
        )

        result = {

            "month": latest,

            "updated": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

        }

        for row in rows:

            name = row.get(
                "CLS_NM",
                "",
            )

            if name in self.REGION_MAP:

                key = self.REGION_MAP[name]

                try:

                    value = float(
                        row.get(
                            "DTA_VAL",
                            0,
                        )
                    )

                except Exception:

                    value = 0.0

                result[key] = value

        return result

    # -----------------------------------------------------

    def fetch_table(
        self,
        table_name,
    ):

        info = self.TABLES[
            table_name
        ]

        response = self._request(
            info["STATBL_ID"],
            info["DTACYCLE_CD"],
        )

        rows = self._rows(
            response,
        )

        return self._extract_region(
            rows,
        )

    # -----------------------------------------------------

    def fetch_price_index(self):

        return self.fetch_table(
            "price_index"
        )

    # -----------------------------------------------------

    def fetch_jeonse_index(self):

        return self.fetch_table(
            "jeonse_index"
        )

    # -----------------------------------------------------

    def fetch_average_price(self):

        return self.fetch_table(
            "average_price"
        )

    # -----------------------------------------------------

    def fetch_median_price(self):

        return self.fetch_table(
            "median_price"
        )

    # -----------------------------------------------------

    def build(self):

        self.data = {

            "price_index":
                self.fetch_price_index(),

            "jeonse_index":
                self.fetch_jeonse_index(),

            "average_price":
                self.fetch_average_price(),

            "median_price":
                self.fetch_median_price(),

        }

        return self.data

    # -----------------------------------------------------

    def save_json(
        self,
        filename="reb_market.json",
    ):

        if not self.data:

            self.build()

        path = Path(
            filename
        )

        with open(
            path,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                self.data,
                f,
                ensure_ascii=False,
                indent=4,
            )

        return path

    # -----------------------------------------------------

    def load_json(
        self,
        filename="reb_market.json",
    ):

        path = Path(
            filename
        )

        if not path.exists():

            raise FileNotFoundError(
                filename
            )

        with open(
            path,
            encoding="utf-8",
        ) as f:

            self.data = json.load(
                f
            )

        return self.data


# modules/reb_market.py
# (3/3)

    # -----------------------------------------------------

    def latest(self):

        if not self.data:

            self.build()

        return self.data

    # -----------------------------------------------------

    def get_price_index(self):

        if not self.data:

            self.build()

        return self.data.get(
            "price_index",
            {},
        )

    # -----------------------------------------------------

    def get_jeonse_index(self):

        if not self.data:

            self.build()

        return self.data.get(
            "jeonse_index",
            {},
        )

    # -----------------------------------------------------

    def get_average_price(self):

        if not self.data:

            self.build()

        return self.data.get(
            "average_price",
            {},
        )

    # -----------------------------------------------------

    def get_median_price(self):

        if not self.data:

            self.build()

        return self.data.get(
            "median_price",
            {},
        )

    # -----------------------------------------------------

    def print_summary(self):

        if not self.data:

            self.build()

        price = self.data["price_index"]

        print()

        print("========================================")
        print("REB Market Summary")
        print("========================================")
        print("기준월 :", price.get("month", ""))
        print()

        print(
            f"전국 매매지수 : "
            f"{price.get('nation', 0):.2f}"
        )

        print(
            f"서울 매매지수 : "
            f"{price.get('seoul', 0):.2f}"
        )

        print(
            f"부산 매매지수 : "
            f"{price.get('busan', 0):.2f}"
        )

        print("========================================")

    # -----------------------------------------------------

    def update(
        self,
        filename="reb_market.json",
    ):

        self.build()

        self.save_json(
            filename,
        )

        return self.data


if __name__ == "__main__":

    engine = REBMarket()

    engine.update()

    engine.print_summary()

