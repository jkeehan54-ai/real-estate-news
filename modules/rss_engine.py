# rss_engine.py

import feedparser
import requests

from modules.news_config import HEADERS

from modules.news_utils import (
    get_best_pub_dt,
    is_recent,
)

from modules.news_filter import (
    is_estate_related,
)


# ── A. RSS 수집 ───────────────────────────────────────────────────────────────
def fetch_rss(name, url, estate_only, now_kst):
    items = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
        for entry in feed.entries:
            pub_dt = get_best_pub_dt(entry)
            if not is_recent(pub_dt, now_kst):
                continue
            title = (entry.title or "").strip()
            if not title:
                continue
            # ★ 전용(True)/일반(False) 피드 모두 동일하게 필터 적용
            if not is_estate_related(title):
                continue
            src = name
            if hasattr(entry, 'source') and hasattr(entry.source, 'title'):
                src = entry.source.title
            items.append((pub_dt, title, entry.link, src))
        print(f"  OK [RSS/{name}] {len(items)}건")
    except Exception as e:
        print(f"  ER [RSS/{name}] {type(e).__name__}: {str(e)[:50]}")
    return items
