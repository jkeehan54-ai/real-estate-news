import time

import requests

from modules.news_utils import market_text


# ============================================================
# KB API 설정
# ============================================================

KB_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://kbland.kr",
    "Referer": "https://kbland.kr/",
    "webservice": "1",
}

KB_TIMEOUT = 20
KB_RETRY_COUNT = 3
KB_RETRY_DELAY = 2


# ============================================================
# KB API 공통 호출
# ============================================================

def _kb_get(url):
    """
    KB API 공통 GET 호출

    - 일시적인 연결 오류 발생 시 재시도
    - 모든 재시도 실패 시 예외를 그대로 발생시킨다.
    - 호출 결과를 여기서 0값으로 변환하지 않는다.
    """

    last_error = None

    for attempt in range(1, KB_RETRY_COUNT + 1):

        try:

            print(
                f"[KB API] 요청 "
                f"{attempt}/{KB_RETRY_COUNT}"
            )

            response = requests.get(
                url,
                headers=KB_HEADERS,
                timeout=KB_TIMEOUT,
            )

            response.raise_for_status()

            print(
                "[KB STATUS]",
                response.status_code,
            )

            return response.json()

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        ) as exc:

            last_error = exc

            print(
                "[KB API ERROR]",
                repr(exc),
            )

            if attempt < KB_RETRY_COUNT:

                print(
                    f"[KB RETRY] "
                    f"{KB_RETRY_DELAY}초 후 재시도"
                )

                time.sleep(
                    KB_RETRY_DELAY
                )

        except requests.exceptions.RequestException as exc:

            last_error = exc

            print(
                "[KB HTTP ERROR]",
                repr(exc),
            )

            break

        except Exception as exc:

            last_error = exc

            print(
                "[KB UNKNOWN ERROR]",
                repr(exc),
            )

            break

    raise last_error


# ============================================================
# 최신 KB 기준일
# ============================================================

def get_latest_kb_date():

    url = (
        "https://api.kbland.kr/"
        "land-extra/market-conditions/ref-date"
        "?거래유형=1&주기=1"
    )

    data = _kb_get(url)

    latest = data["dataBody"]["data"][0]

    print(
        "[KB 최신 기준일]",
        latest,
    )

    return latest


# ============================================================
# HTML 뉴스 브리핑용
# ============================================================

def get_market_brief():

    try:

        latest = get_latest_kb_date()

        url = (
            "https://api.kbland.kr/"
            "land-extra/market-conditions/sales"
            f"?기준년월일={latest}"
            "&법정동코드=0000000000"
        )

        data = _kb_get(url)

        print(
            "[KB DATA DATE]",
            data["dataBody"]["data"]["기준년월일"],
        )

        summary = (
            data["dataBody"]["data"]["시장요약"]
        )

        print("[KB SUMMARY]")
        print(summary)

        change = summary[
            "대표지역변동률"
        ]

        weeks = summary[
            "대표지역변동률연속주수"
        ]

        trend = summary[
            "대표지역변동률연속상태"
        ]

        seller = summary[
            "매도자많음응답"
        ]

        buyer = summary[
            "매수자많음응답"
        ]

        all_market = (
            data["dataBody"]["data"]["전체시황"]
        )

        seoul = next(
            (
                x["변동률"]
                for x in all_market
                if x["지역명"] == "서울"
            ),
            0,
        )

        busan = next(
            (
                x["변동률"]
                for x in all_market
                if x["지역명"] == "부산"
            ),
            0,
        )

        return (
            f"전국 아파트 매매가격은 "
            f"{change}% {trend}했습니다. "
            f"{weeks}주 연속 "
            f"{trend}세를 유지했습니다. "
            f"서울은 {market_text(seoul)}, "
            f"부산은 {market_text(busan)}입니다. "
            f"매도자많음 {seller}%, "
            f"매수자많음 {buyer}%입니다."
        )

    except Exception as exc:

        print(
            "[KB ERROR]",
            repr(exc),
        )

        return (
            "KB 시황 정보를 "
            "불러오지 못했습니다."
        )


# ============================================================
# BRN 계산용
# ============================================================

def get_market_data():

    try:

        latest = get_latest_kb_date()

        url = (
            "https://api.kbland.kr/"
            "land-extra/market-conditions/sales"
            f"?기준년월일={latest}"
            "&법정동코드=0000000000"
        )

        data = _kb_get(url)

        summary = (
            data["dataBody"]["data"]["시장요약"]
        )

        all_market = (
            data["dataBody"]["data"]["전체시황"]
        )

        seoul = next(
            (
                float(x["변동률"])
                for x in all_market
                if x["지역명"] == "서울"
            ),
            0.0,
        )

        busan = next(
            (
                float(x["변동률"])
                for x in all_market
                if x["지역명"] == "부산"
            ),
            0.0,
        )

        result = {
            "ok": True,

            "date": latest,

            "nation_change": float(
                summary[
                    "대표지역변동률"
                ]
            ),

            "weeks": int(
                summary[
                    "대표지역변동률연속주수"
                ]
            ),

            "trend": summary[
                "대표지역변동률연속상태"
            ],

            "seller": float(
                summary[
                    "매도자많음응답"
                ]
            ),

            "buyer": float(
                summary[
                    "매수자많음응답"
                ]
            ),

            "seoul_change": seoul,

            "busan_change": busan,
        }

        print(
            "[KB DATA OK]",
            latest,
        )

        return result

    except Exception as exc:

        print(
            "[KB DATA ERROR]",
            repr(exc),
        )

        # ----------------------------------------------------
        # 중요
        #
        # 기존 코드처럼 단순히 0값을 반환하지 않는다.
        # ok=False를 통해 실제 시장의 0.0%와
        # KB 데이터 취득 실패를 구분한다.
        # ----------------------------------------------------

        return {
            "ok": False,

            "date": "",

            "nation_change": 0.0,

            "weeks": 0,

            "trend": "",

            "seller": 0.0,

            "buyer": 0.0,

            "seoul_change": 0.0,

            "busan_change": 0.0,
        }
```
