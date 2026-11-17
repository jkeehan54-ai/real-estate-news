# news_pipeline.py
from datetime import datetime, timedelta

from modules.news_config import (
    KST,
    RSS_FEEDS,
    SOURCE_LIMITS,
    CAT_LIMITS,
)

from modules.rss_engine import fetch_rss

from modules.crawler_engine import (
    scrape_busan,
    scrape_kookje,
    scrape_naver_land,
)

from modules.google_engine import fetch_google

from modules.news_filter import (
    classify,
    is_duplicate,
    is_estate_related,
    is_market_valid,
    normalize,
)


_LINK_CACHE = {}
_LINK_BUDGET = [60]
_LINK_FAIL = [0]


def _resolve_link(link):
    """
    구글뉴스 중간 주소(news.google.com/rss/articles/...)를 언론사 원문 주소로 바꾼다.
    브리핑에 실리는 기사에만 쓰고, 한 번 실행에 최대 60건까지 시도한다.
    연속 8번 실패하면 더 이상 요청하지 않는다.
    실패하거나 패키지가 없으면 원래 주소를 그대로 돌려준다.
    """
    if "news.google.com/rss/articles" not in link:
        return link
    if link in _LINK_CACHE:
        return _LINK_CACHE[link]
    if _LINK_BUDGET[0] <= 0:
        return link
    _LINK_BUDGET[0] -= 1

    resolved = link
    try:
        from googlenewsdecoder import gnewsdecoder

        result = gnewsdecoder(link, interval=1)
        if result.get("status") and result.get("decoded_url"):
            resolved = result["decoded_url"]
            _LINK_FAIL[0] = 0
        else:
            _LINK_FAIL[0] += 1
    except Exception:
        _LINK_FAIL[0] += 1

    if _LINK_FAIL[0] >= 8:
        _LINK_BUDGET[0] = 0

    _LINK_CACHE[link] = resolved
    return resolved


def get_clean_news():

    cats = [
        "청약",
        "재건축",
        "공급개발",
        "세제",
        "정책",
        "부산경남",
        "시장동향",
    ]

    results = {c: [] for c in cats}

    seen = []
    src_cnt = {}

    now_kst = datetime.now(KST)

    print(f"[실행시각] {now_kst.strftime('%Y-%m-%d %H:%M KST')}")

    all_entries = []

    print("\n[A] RSS 피드")
    for name, url, eo in RSS_FEEDS:
        all_entries.extend(fetch_rss(name, url, eo, now_kst))

    print("\n[B] 스크래핑 (부산일보/국제신문/네이버부동산)")
    all_entries.extend(scrape_busan(now_kst))
    all_entries.extend(scrape_kookje(now_kst))
    all_entries.extend(scrape_naver_land(now_kst))

    print("\n[C] Google News RSS")
    all_entries.extend(fetch_google(now_kst))

    print(f"\n수집 합계(필터전): {len(all_entries)}건")

    all_entries.sort(
        key=lambda x: (x[0] or datetime.max.replace(tzinfo=KST)),
        reverse=True,
    )

    total = 0
    dup = 0
    nonre = 0

    for pub_dt, title, link, src in all_entries:

        total += 1

        if pub_dt is None or (now_kst - pub_dt) > timedelta(hours=24):
            continue

        if not is_estate_related(title):
            nonre += 1
            continue

        if is_duplicate(title, seen):
            dup += 1
            continue

        cat = classify(title)

        if cat not in results:
            continue

        if cat == "시장동향" and not is_market_valid(title):
            nonre += 1
            continue

        if src in SOURCE_LIMITS:
            if src_cnt.get(src, 0) >= SOURCE_LIMITS[src]:
                continue

        limit = CAT_LIMITS.get(cat)
        if limit is not None:
            if len(results[cat]) >= limit:
                continue

        pub_str = pub_dt.strftime("%m/%d %H:%M") if pub_dt else ""

        results[cat].append({
            "title": normalize(title),
            "link": _resolve_link(link),
            "src": src,
            "pub_str": pub_str,
        })

        seen.append(title)
        src_cnt[src] = src_cnt.get(src, 0) + 1

    saved = sum(len(v) for v in results.values())

    print(
        f"\n[결과] 수집 {total}건 | 중복제거 {dup}건 | "
        f"시장필터 {nonre}건 | HTML 저장 {saved}건"
    )

    for cat in cats:
        print(f"  [{cat}] {len(results[cat])}건")

    print("\n[매체별]")
    for k, v in sorted(src_cnt.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}건")

    return results
