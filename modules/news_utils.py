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
        r'/(\d{4})/(\d{2})/(\d{2})/',
        r'key=(\d{4})(\d{2})(\d{2})\.',
        r'code=(\d{4})(\d{2})(\d{2})',
    ]:
        m = re.search(pattern, url)
        if m:
            try:
                return datetime(
                    int(m.group(1)), int(m.group(2)), int(m.group(3)),
                    0, 0, tzinfo=KST
                )
            except Exception:
                pass
    return None

def get_best_pub_dt(entry):
    pub = entry.get("published_parsed")
    if pub:
        return datetime(*pub[:6], tzinfo=timezone.utc).astimezone(KST)
    return extract_date_from_url(getattr(entry, 'link', ''))

def is_recent(pub_dt, now_kst):
    """어제~오늘 기사. 날짜 불명 → 포함."""
    if pub_dt is None:
        return True
    yesterday = (now_kst - timedelta(days=1)).date()
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

    elif value < 0:
        return f"{abs(value):.2f}% 하락"

    return "0.00% 보합"

def interleave_by_source(items):

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


def is_duplicate(new_title: str, seen: list) -> bool:
    """
    3단계 중복 판별 (비용 없음, 빠름):
    1단계: 문자열 유사도 0.72 이상  → 같은 기사 (제목 일부만 달라도 잡힘)
    2단계: 키워드 자카드 0.55 이상  → 같은 주제 다른 표현
    3단계: 핵심 엔티티 2개 이상 겹침 → 같은 단지·지역·금액
    """
    nn = normalize(new_title)
    kn = keywords(new_title)
    en = extract_entities(new_title)
    for s in seen:
        ns = normalize(s)
        # 1단계: 문자열 유사도
        if SequenceMatcher(None, nn, ns).ratio() >= 0.72:
            return True
        # 2단계: 키워드 자카드
        ks = keywords(s)
        u  = len(kn | ks)
        if u and len(kn & ks) / u >= 0.55:
            return True
        # 3단계: 엔티티 겹침
        es = extract_entities(s)
        if en and es and len(en & es) >= 2:
            return True
    return False
