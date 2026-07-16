# news_utils.py

import re
import requests

from datetime import (
    datetime,
    timezone,
    timedelta,
)

from modules.news_config import (
    HEADERS,
    KST,
)


# ── 날짜 유틸 ─────────────────────────────────────────────────────────────────
def extract_date_from_url(url):
    for pattern in [
        r"/(\d{4})/(\d{2})/(\d{2})/",
        r"key=(\d{4})(\d{2})(\d{2})\.",
        r"code=(\d{4})(\d{2})(\d{2})",
    ]:
        m = re.search(pattern, url)
        if m:
            try:
                return datetime(
                    int(m.group(1)),
                    int(m.group(2)),
                    int(m.group(3)),
                    0,
                    0,
                    tzinfo=KST,
                )
            except Exception:
                pass

    return None


def get_best_pub_dt(entry):

    pub = entry.get("published_parsed")

    if pub:
        return datetime(
            *pub[:6],
            tzinfo=timezone.utc,
        ).astimezone(KST)

    return extract_date_from_url(
        getattr(entry, "link", "")
    )


def is_recent(pub_dt, now_kst):
    """
    어제~오늘 기사.
    날짜를 알 수 없는 경우는 포함한다.
    """
    if pub_dt is None:
        return True

    yesterday = (
        now_kst - timedelta(days=1)
    ).date()

    return pub_dt.date() >= yesterday


def make_session(referer=None):

    s = requests.Session()

    s.headers.update(HEADERS)

    if referer:
        s.headers["Referer"] = referer

    return s


def market_text(value):

    value = float(value)

    if value > 0:
        return f"{value:.2f}% 상승"

    if value < 0:
        return f"{abs(value):.2f}% 하락"

    return "0.00% 보합"


def interleave_by_source(items):

    groups = {}

    for item in items:
        groups.setdefault(
            item["src"],
            [],
        ).append(item)

    result = []

    while groups:

        for src in list(groups.keys()):

            result.append(
                groups[src].pop(0)
            )

            if not groups[src]:
                del groups[src]

    return result
