# crawler_engine.py

import requests

from bs4 import BeautifulSoup
from urllib.parse import urljoin

from modules.news_utils import (
    make_session,
    extract_date_from_url,
    is_recent,
)

from modules.news_filter import (
    is_estate_related,
)


# ── B-1. 부산일보 스크래핑 ───────────────────────────────────────────────────
def scrape_busan(now_kst):
    items = []
    seen = set()

    for url in [
        "https://www.busan.com/economy/",
        "https://www.busan.com/newsList/realestate",
    ]:
        try:
            s = make_session("https://www.busan.com/")
            resp = s.get(url, timeout=10)

            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")

            for el in soup.select("p.title, .title a, h4 a, h3 a"):

                a = el if el.name == "a" else el.find("a", href=True)

                if not a:
                    continue

                title = a.get_text(strip=True)
                href = a.get("href", "")

                if not title or len(title) < 10 or not href:
                    continue

                if not is_estate_related(title):
                    continue

                link = urljoin("https://www.busan.com", href)

                if link in seen:
                    continue

                seen.add(link)

                pub_dt = extract_date_from_url(link)

                if not is_recent(pub_dt, now_kst):
                    continue

                items.append(
                    (
                        pub_dt,
                        title,
                        link,
                        "부산일보",
                    )
                )

        except Exception as e:
            print(f"  ER [부산일보] {type(e).__name__}: {str(e)[:50]}")

    print(f"  OK [부산일보] {len(items)}건")

    return items


# ── B-2. 국제신문 스크래핑 ───────────────────────────────────────────────────
def scrape_kookje(now_kst):

    items = []
    seen = set()

    for url in [
        "https://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0220",
        "https://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0200",
    ]:

        try:

            s = make_session("https://www.kookje.co.kr/")

            resp = s.get(url, timeout=10)

            if resp.status_code != 200:
                continue

            resp.encoding = "euc-kr"

            soup = BeautifulSoup(resp.text, "html.parser")

            selectors = [
                "ol.tabcontent li a",
                "ol#hitlist1 li a",
                "ol#hitlist2 li a",
                "ol#hitlist3 li a",
                "ol#hitlist4 li a",
                "ol#hitlist5 li a",
                "dt a",
                "h2 a",
                "h3.tit a",
            ]

            for sel in selectors:

                for a in soup.select(sel):

                    title = a.get_text(strip=True)
                    href = a.get("href", "")

                    if not title or len(title) < 10:
                        continue

                    if "newsbody.asp" not in href:
                        continue

                    if not is_estate_related(title):
                        continue

                    link = urljoin(
                        "https://www.kookje.co.kr",
                        href,
                    )

                    if link in seen:
                        continue

                    seen.add(link)

                    pub_dt = extract_date_from_url(link)

                    if not is_recent(pub_dt, now_kst):
                        continue

                    items.append(
                        (
                            pub_dt,
                            title,
                            link,
                            "국제신문",
                        )
                    )

        except Exception as e:
            print(f"  ER [국제신문] {type(e).__name__}: {str(e)[:50]}")

    print(f"  OK [국제신문] {len(items)}건")

    return items


# ── B-3. 네이버 부동산 스크래핑 ──────────────────────────────────────────────
def scrape_naver_land(now_kst):

    items = []
    seen = set()

    for url, base in [
        ("https://land.naver.com/news/", "https://land.naver.com"),
        ("https://fin.land.naver.com/news", "https://fin.land.naver.com"),
    ]:

        try:

            s = make_session(base + "/")

            resp = s.get(url, timeout=10)

            if resp.status_code != 200:
                print(f"  ER [네이버부동산] HTTP {resp.status_code}")
                continue

            soup = BeautifulSoup(resp.text, "html.parser")

            cnt = 0

            selectors = [
                "ul.category_list li a",
                "ul#land_news_list li a",
                "li.main_news a",
                "li.main_article_beta a",
                "li.news_headline a",
                "li.news_breaking a",
                'a[class*="NewsList_link"]',
                'a[class*="CardNews_link"]',
                'div[class*="AllNews_article"] a',
            ]

            for sel in selectors:

                for a in soup.select(sel):

                    title = a.get_text(strip=True)
                    href = a.get("href", "")

                    if not title or len(title) < 10:
                        continue

                    if not href.startswith("http"):
                        continue

                    if not is_estate_related(title):
                        continue

                    if href in seen:
                        continue

                    seen.add(href)

                    pub_dt = extract_date_from_url(href)

                    # ★ 날짜 필터 추가
                    if not is_recent(pub_dt, now_kst):
                        continue

                    items.append(
                        (
                            pub_dt,
                            title,
                            href,
                            "네이버부동산",
                        )
                    )

                    cnt += 1

            print(f"  OK [네이버({base.split('/')[2]})] {cnt}건")

        except Exception as e:
            print(f"  ER [네이버부동산] {type(e).__name__}: {str(e)[:50]}")

    return items
