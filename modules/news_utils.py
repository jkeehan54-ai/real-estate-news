# modules/news_utils.py

import re
import requests
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))


def extract_date_from_url(url: str):
    """URL에서 날짜를 추출한다."""

    patterns = [
        r"/(\d{4})/(\d{2})/(\d{2})/",
        r"key=(\d{4})(\d{2})(\d{2})\.",
        r"code=(\d{4})(\d{2})(\d{2})",
    ]

    for pattern in patterns:
        m = re.search(pattern, url or "")
        if not m:
            continue

        try:
            return datetime(
                int(m.group(1)),
                int(m.group(2)),
                int(m.group(3)),
                tzinfo=KST,
            )
        except Exception:
            pass

    return None


def get_best_pub_dt(entry):
    """RSS published_parsed 또는 URL 날짜를 사용한다."""

    pub = entry.get("published_parsed")

    if pub:
        return datetime(
            *pub[:6],
            tzinfo=timezone.utc
        ).astimezone(KST)

    return extract_date_from_url(
        getattr(entry, "link", "")
    )


def is_recent(pub_dt, now_kst):
    """
    오늘 또는 어제 기사만 사용.
    날짜가 없으면 포함.
    """

    if pub_dt is None:
        return True

    yesterday = (now_kst - timedelta(days=1)).date()

    return pub_dt.date() >= yesterday


def make_session(headers, referer=None):
    """
    공통 requests.Session 생성
    """

    session = requests.Session()

    session.headers.update(headers)

    if referer:
        session.headers["Referer"] = referer

    return session


def market_text(value):
    """
    KB 변동률 문자열 변환
    """

    value = float(value)

    if value > 0:
        return f"{value:.2f}% 상승"

    if value < 0:
        return f"{abs(value):.2f}% 하락"

    return "0.00% 보합"


def interleave_by_source(items):
    """
    동일 매체가 연속되지 않도록
    매체별로 번갈아 배치한다.
    """

    groups = {}

    for item in items:
        groups.setdefault(item["src"], []).append(item)

    result = []

    while groups:

        for src in list(groups.keys()):

            result.append(groups[src].pop(0))

            if not groups[src]:
                del groups[src]

    return result
