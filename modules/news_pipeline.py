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

        if not is_market_valid(title):
            nonre += 1
            if any(k in title for k in ["종부세", "취득세", "양도세", "재산세", "보유세", "세금", "세제"]):
                print(f"  [진단/세제필터걸림] {title}")
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
            "link": link,
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