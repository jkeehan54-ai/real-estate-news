import feedparser
from datetime import datetime

# 1. 13개 매체 및 바로가기 주소
SOURCES = {
    "조선일보": ("https://www.chosun.com/arc/outboundfeeds/rss/category/economy/real_estate/", "https://www.chosun.com/economy/real_estate/"),
    "중앙일보": ("https://rss.joins.com/joins_realestate_list.xml", "https://www.joongang.co.kr/realestate"),
    "동아일보": ("https://rss.donga.com/economy.xml", "https://www.donga.com/news/Economy/Realestate"),
    "한겨레": ("https://www.hani.co.kr/rss/economy/", "https://www.hani.co.kr/arti/economy/property/"),
    "매일경제": ("https://www.mk.co.kr/rss/realestate.xml", "https://www.mk.co.kr/news/realestate/"),
    "한국경제": ("https://www.hankyung.com/feed/realestate", "https://www.hankyung.com/realestate"),
    "부산일보": ("http://www.busan.com/rss/pc/economy.xml", "https://www.busan.com/economy/"),
    "국제신문": ("http://www.kookje.co.kr/news2011/rss/rss_0200.xml", "https://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0200"),
    "네이버부동산": ("https://land.naver.com/news/headline.naver", "https://land.naver.com/news/"),
    "한국부동산원": ("https://www.reb.or.kr/reb/main.do", "https://www.reb.or.kr/reb/main.do"),
    "KB부동산": ("https://kbland.kr/today?xy=37.5194908,126.9249743,19", "https://kbland.kr/today?xy=37.5194908,126.9249743,19"),
    "머니투데이": ("https://news.mt.co.kr/rss/view.mt?type=estate", "https://news.mt.co.kr/estate/"),
    "연합뉴스": ("https://www.yna.co.kr/rss/economy/real-estate.xml", "https://www.yna.co.kr/economy/real-estate/")
}

def get_category(title):
    t = title.lower()
    if any(k in t for k in ["분양", "청약"]): return "청약"
    if any(k in t for k in ["재건축", "재개발"]): return "재건축"
    if any(k in t for k in ["세금", "종부세", "취득세"]): return "세제"
    if any(k in t for k in ["정부", "규제", "대출", "금리", "정책"]): return "정책"
    return "전체"

# 2. 뉴스 수집 및 중복 제거
articles = []
seen = set()
for name, (rss, link) in SOURCES.items():
    feed = feedparser.parse(rss)
    for entry in feed.entries[:3]:
        if entry.title not in seen:
            articles.append({
                "title": entry.title, "source": name, 
                "category": get_category(entry.title), "summary": "최신 부동산 이슈입니다."
            })
            seen.add(entry.title)

# 3. 브리핑 및 템플릿 구성
briefing = "전국 아파트 매매가격 0.05% 상승, 38주 연속 상승세 유지 [참조: image_446c75.jpg]"
top_articles = articles[:5]

# HTML 생성
html = f"""
<h1>🏠 부동산 뉴스 브리핑 ({datetime.now().strftime('%Y-%m-%d')})</h1>
<p>🔄 실시간 뉴스 새로고침</p>
<h2>오늘의 핵심 브리핑</h2><p>{briefing}</p>

<h2>TOP 이슈</h2>
{''.join([f'<p>{a["title"]} - {a["source"]}</p>' for a in top_articles])}

<h2>전체 뉴스</h2>
{''.join([f'<p>[{a["category"]}] {a["title"]} ({a["source"]})<br><small>{a["summary"]}</small></p>' for a in articles])}
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
