import requests

from modules.news_utils import market_text


def get_latest_kb_date():

    url = (
        "https://api.kbland.kr/land-extra/market-conditions/ref-date"
        "?거래유형=1&주기=1"
    )

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://kbland.kr",
        "Referer": "https://kbland.kr/",
        "webservice": "1",
    }

    r = requests.get(
        url,
        headers=headers,
        timeout=20,
    )

    r.raise_for_status()

    data = r.json()

    latest = data["dataBody"]["data"][0]

    print("[KB 최신 기준일]", latest)

    return latest


# ─────────────────────────────────────────────────────────────
# HTML 뉴스 브리핑용
# ─────────────────────────────────────────────────────────────
def get_market_brief():

    try:

        latest = get_latest_kb_date()

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://kbland.kr",
            "Referer": "https://kbland.kr/",
            "webservice": "1",
        }

        url = (
            "https://api.kbland.kr/land-extra/market-conditions/sales"
            f"?기준년월일={latest}"
            "&법정동코드=0000000000"
        )

        r = requests.get(
            url,
            headers=headers,
            timeout=20,
        )

        r.raise_for_status()

        print("[KB STATUS]", r.status_code)

        data = r.json()

        print(
            "[KB DATA DATE]",
            data["dataBody"]["data"]["기준년월일"],
        )

        summary = data["dataBody"]["data"]["시장요약"]

        print("[KB SUMMARY]")
        print(summary)

        change = summary["대표지역변동률"]
        weeks = summary["대표지역변동률연속주수"]
        trend = summary["대표지역변동률연속상태"]

        seller = summary["매도자많음응답"]
        buyer = summary["매수자많음응답"]

        all_market = data["dataBody"]["data"]["전체시황"]

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
            f"전국 아파트 매매가격은 {change}% {trend}했습니다. "
            f"{weeks}주 연속 {trend}세를 유지했습니다. "
            f"서울은 {market_text(seoul)}, "
            f"부산은 {market_text(busan)}입니다. "
            f"매도자많음 {seller}%, "
            f"매수자많음 {buyer}%입니다."
        )

    except Exception as e:

        print("[KB ERROR]", repr(e))

        return "KB 시황 정보를 불러오지 못했습니다."


# ─────────────────────────────────────────────────────────────
# BRN 계산용
# ─────────────────────────────────────────────────────────────
def get_market_data():

    try:

        latest = get_latest_kb_date()

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://kbland.kr",
            "Referer": "https://kbland.kr/",
            "webservice": "1",
        }

        url = (
            "https://api.kbland.kr/land-extra/market-conditions/sales"
            f"?기준년월일={latest}"
            "&법정동코드=0000000000"
        )

        r = requests.get(
            url,
            headers=headers,
            timeout=20,
        )

        r.raise_for_status()

        data = r.json()

        summary = data["dataBody"]["data"]["시장요약"]
        all_market = data["dataBody"]["data"]["전체시황"]

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

        return {
            "date": latest,
            "nation_change": float(summary["대표지역변동률"]),
            "weeks": int(summary["대표지역변동률연속주수"]),
            "trend": summary["대표지역변동률연속상태"],
            "seller": float(summary["매도자많음응답"]),
            "buyer": float(summary["매수자많음응답"]),
            "seoul_change": seoul,
            "busan_change": busan,
        }

    except Exception as e:

        print("[KB DATA ERROR]", repr(e))

        return {
            "date": "",
            "nation_change": 0.0,
            "weeks": 0,
            "trend": "",
            "seller": 0.0,
            "buyer": 0.0,
            "seoul_change": 0.0,
            "busan_change": 0.0,
        }
