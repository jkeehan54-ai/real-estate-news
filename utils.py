"""
utils.py
--------------------------------------------------
공통 유틸리티 함수
"""

import re
import requests
from datetime import datetime, timezone, timedelta
from urllib.parse import urljoin

from config import HEADERS, KST


# --------------------------------------------------
# URL에서 날짜 추출
# --------------------------------------------------

def extract_date_from_url(url):

    for pattern in [

        r'/(\d{4})/(\d{2})/(\d{2})/',

        r'key=(\d{4})(\d{2})(\d{2})\.',

        r'code=(\d{4})(\d{2})(\d{2})',

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


# --------------------------------------------------
# RSS 게시일
# --------------------------------------------------

def get_best_pub_dt(entry):

    pub = entry.get("published_parsed")

    if pub:

        return datetime(

            *pub[:6],

            tzinfo=timezone.utc

        ).astimezone(KST)

    return extract_date_from_url(

        getattr(entry, "link", "")

    )


# --------------------------------------------------
# 최근 기사 여부
# --------------------------------------------------

def is_recent(pub_dt, now_kst):

    if pub_dt is None:

        return True

    yesterday = (

        now_kst - timedelta(days=1)

    ).date()

    return pub_dt.date() >= yesterday


# --------------------------------------------------
# 시장 변동률 문자열
# --------------------------------------------------

def market_text(value):

    value = float(value)

    if value > 0:

        return f"{value:.2f}% 상승"

    elif value < 0:

        return f"{abs(value):.2f}% 하락"

    return "0.00% 보합"


# --------------------------------------------------
# Requests Session
# --------------------------------------------------

def make_session(referer=None):

    s = requests.Session()

    s.headers.update(HEADERS)

    if referer:

        s.headers["Referer"] = referer

    return s
