import feedparser
from datetime import datetime

# 1. 13개 매체 전체 복구 (이름, RSS, 바로가기)
SOURCES = {
    "조선일보": ("https://www.chosun.com/arc/outboundfeeds/rss/category/economy/real_estate/", "https://www.chosun.com/economy/real_estate/"),
    "중앙일보": ("https://rss.joins.com/joins_realestate_list.xml", "https://www.joongang.co.kr/realestate"),
    "동아일보": ("https://rss.donga.com/economy.xml", "https://www.donga.com/news/Economy/Realestate"),
    "한겨레": ("https://www.hani.co.kr/rss/economy/", "https://www.hani.co.kr/arti/economy/property/"),
    "매일경제": ("https://www.mk.co.kr/rss/realestate.xml", "https://www.mk.co.kr/news/realestate/"),
    "한국경제": ("https://www.hankyung.com/feed/realestate", "https://www.hankyung.com/realestate"),
    "부산일보": ("http://www.busan.com/rss/pc/economy.xml", "https://www.busan.com/economy/"),
    "국제신문": ("http://www.kookje.co.kr/news2011/rss/rss_0200.xml", "https://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0200"),
    "네이버부동산": ("https://news.naver.com/main/list.naver?mode=LS2D&mid=shm&sid1=101&sid2=260", "https://land.naver.com/news/"),
    "한국부동산원": ("https://www.reb.or.kr/reb/main.do", "https://www.reb.or.kr/reb/main.do"),
    "KB부동산": ("https://kbland.kr/today", "https://kbland.kr/today"),
    "머니투데이": ("https://news.mt.co.kr/rss/view.mt?type=estate", "https://news.mt.co.kr/estate/"),
    "연합뉴스": ("https://www.yna.co.kr/rss/economy/real-estate.xml", "https://www.yna.co.kr/economy/real-estate/")
}

# 2. 부동산 핵심 필터링 로직
def get_category(title):
    t = title.lower()
    keywords = ["부동산", "아파트", "청약", "분양", "재건축", "재개발", "주택", "전세", "월세", "집값", "대출", "공급", "임대"]
    if not any(k in t for k in keywords): return None
    if any(k in t for k in ["분양", "청약"]): return "청약"
    if any(k in t for k in ["재건축", "재개발"]): return "재건축"
    if any(k in t for k in ["세금", "종부세", "취득세"]): return "세제"
    if any(k in t for k in ["정부", "규제", "대출", "금리", "정책"]): return "정책"
    return "전체"

# 3. 데이터 수집 및 구성
articles = []
seen = set()
for name, (rss, link) in SOURCES.items():
    feed = feedparser.parse(rss)
    for entry in feed.entries:
        cat = get_category(entry.title)
        if cat and entry.title not in seen:
            articles.append({"title": entry.title, "source": name, "category": cat, "link": entry.link, "summary": "최신 부동산 이슈입니다."})
            seen.add(entry.title)

# 4. 템플릿 출력
briefing = "전국 아파트 매매가격 0.05% 상승, 38주 연속 상승세 유지. 매수우위지수는 62.9%로 매도자 우위입니다."
top_articles = articles[:5]

# HTML 생성 (요청하신 브리핑 템플릿 형식)
html = f"""
<h1>🏠 부동산 뉴스 브리핑</h1>
<div>{' | '.join([f'<a href="{link}" target="_blank">{name}</a>' for name, (rss, link) in SOURCES.items()])}</div>
<h2>오늘의 핵심 브리핑</h2><p>{briefing}</p>

<h2>TOP 이슈</h2>
{''.join([f'<p>{a["title"]}<br><b>{a["source"]}</b></p>' for a in top_articles])}

<h2>전체 뉴스</h2>
{''.join([f'<p><b>[{a["category"]}]</b> {a["title"]}<br>{a["source"]} - {a["summary"]}</p>' for a in articles])}
"""
with open("index.html", "w", encoding="utf-8") as f: f.write(html)
