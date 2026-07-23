# news_pipeline.py

from datetime import datetime

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
    is_market_valid,
    normalize,
)


# ── 메인 수집 ─────────────────────────────────────────────────────────────────
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
        all_entries.extend(
            fetch_rss(
                name,
                url,
                eo,
                now_kst,
            )
        )

    print("\n[B] 스크래핑 (부산일보/국제신문/네이버부동산)")

    all_entries.extend(scrape_busan(now_kst))
    all_entries.extend(scrape_kookje(now_kst))
    all_entries.extend(scrape_naver_land(now_kst))

    print("\n[C] Google News RSS")

    all_entries.extend(fetch_google(now_kst))

    print(f"\n수집 합계(필터전): {len(all_entries)}건")

    all_entries.sort(
        key=lambda x: x[0] or datetime.max.replace(tzinfo=KST),
        reverse=True,
    )

    total = 0
    dup = 0
    nonre = 0

    for pub_dt, title, link, src in all_entries:

        total += 1

        # ① 중복 제거
        if is_duplicate(title, seen):
            dup += 1
            continue

        # ② 카테고리 분류
        cat = classify(title)

        # 예상하지 못한 카테고리 방어
        if cat not in results:
            continue

        # ③ 시장동향 2차 필터
        if cat == "시장동향" and not is_market_valid(title):
            nonre += 1
            continue

        # ④ 매체별 제한
        if src in SOURCE_LIMITS:
            if src_cnt.get(src, 0) >= SOURCE_LIMITS[src]:
                continue

        # ⑤ 카테고리별 제한
        limit = CAT_LIMITS.get(cat)

        if limit is not None:
            if len(results[cat]) >= limit:
                continue

        pub_str = (
            pub_dt.strftime("%m/%d %H:%M")
            if pub_dt
            else ""
        )

        results[cat].append(
            {
                "title": normalize(title),
                "link": link,
                "src": src,
                "pub_str": pub_str,
            }
        )

        seen.append(title)

        src_cnt[src] = src_cnt.get(src, 0) + 1

    kept = total - dup - nonre

    print(
        f"\n[결과] 전체 {total}건 | "
        f"중복제거 {dup}건 | "
        f"비부동산제외 {nonre}건 | "
        f"최종 {kept}건"
    )

    for cat in cats:
        print(f"  [{cat}] {len(results[cat])}건")

    print("\n[매체별]")

    for k, v in sorted(
        src_cnt.items(),
        key=lambda x: -x[1],
    ):
        print(f"  {k}: {v}건")

    return results
