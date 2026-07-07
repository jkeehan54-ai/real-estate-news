# google_engine.py

import feedparser
import requests

from urllib.parse import quote_plus

from modules.news_config import (
    GOOGLE_QUERIES,
    HEADERS,
)

from modules.news_utils import (
    get_best_pub_dt,
    is_recent,
)

from modules.news_filter import (
    is_estate_related,
)

# ── C. Google News RSS ───────────────────────────────────────────────────────
def fetch_google(now_kst):
    items = []
    for q in GOOGLE_QUERIES:
        try:
            url  = f"https://news.google.com/rss/search?q={quote_plus(q)}&hl=ko&gl=KR&ceid=KR:ko"
            resp = requests.get(url, headers=HEADERS, timeout=10)
            feed = feedparser.parse(resp.content)
            cnt  = 0
            for entry in feed.entries:
                pub_dt = get_best_pub_dt(entry)
                if not is_recent(pub_dt, now_kst):
                    continue
                title = (entry.title or "").strip()
                if not title or not is_estate_related(title):
                    continue
                src  = "뉴스"
                if hasattr(entry, 'source') and hasattr(entry.source, 'title'):
                    src = entry.source.title
                link = entry.link
                # 링크로 매체명 보정
                if "busan.com"    in link: src = "부산일보"
                if "kookje.co.kr" in link: src = "국제신문"
                if "land.naver.com" in link or "fin.land.naver.com" in link:
                    src = "네이버부동산"
                items.append((pub_dt, title, link, src))
                cnt += 1
            print(f"  OK [Google/{q}] {cnt}건")
        except Exception as e:
            print(f"  ER [Google/{q}] {type(e).__name__}: {str(e)[:50]}")
    return items
