import feedparser
from datetime import datetime

# 1. 13개 매체 정의
SOURCES = {
    "조선일보": ("https://www.chosun.com/arc/outboundfeeds/rss/category/economy/realestate/", "https://www.chosun.com/economy/realestate/"),
    "중앙일보": ("https://rss.joins.com/joins_realestate_list.xml", "https://www.joongang.co.kr/realestate"),
    "동아일보": ("https://rss.donga.com/economy.xml", "https://www.donga.com/news/Economy/Realestate"),
    "한겨레": ("https://www.hani.co.kr/rss/economy/", "https://www.hani.co.kr/arti/economy/property/"),
    "매일경제": ("https://www.mk.co.kr/rss/realestate.xml", "https://www.mk.co.kr/news/realestate/"),
    "한국경제": ("https://www.hankyung.com/feed/realestate", "https://www.hankyung.com/realestate"),
    "부산일보": ("http://www.busan.com/rss/pc/economy.xml", "https://www.busan.com/economy/"),
    "국제신문": ("http://www.kookje.co.kr/news2011/rss/rss_0200.xml", "https://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0200"),
    "네이버부동산": ("https://news.google.com/rss/search?q=네이버부동산+부동산&hl=ko&gl=KR&ceid=KR:ko", "https://land.naver.com/news/"),
    "한국부동산원": ("https://news.google.com/rss/search?q=한국부동산원+부동산&hl=ko&gl=KR&ceid=KR:ko", "https://www.reb.or.kr/reb/main.do"),
    "KB부동산": ("https://news.google.com/rss/search?q=KB부동산+부동산&hl=ko&gl=KR&ceid=KR:ko", "https://kbland.kr/"),
    "머니투데이": ("https://news.mt.co.kr/rss/view.mt?type=estate", "https://news.mt.co.kr/estate/"),
    "연합뉴스": ("https://www.yna.co.kr/rss/economy/real-estate.xml", "https://www.yna.co.kr/economy/real-estate/")
}

def get_category(title):
    t = title.lower()
    if any(k in t for k in ["분양", "청약"]): return "청약"
    if any(k in t for k in ["재건축", "재개발"]): return "재건축"
    if any(k in t for k in ["세금", "종부세", "취득세"]): return "세제"
    if any(k in t for k in ["정부", "규제", "대출", "금리", "공급"]): return "정책"
    return "시장동향"

# 뉴스 수집 및 카테고리별 분류
data = {cat: [] for cat in ["청약", "재건축", "세제", "정책", "시장동향"]}
seen = set()

for name, (rss, link) in SOURCES.items():
    feed = feedparser.parse(rss)
    for entry in feed.entries[:3]:
        cat = get_category(entry.title)
        if entry.title not in seen:
            data[cat].append((entry.title, entry.link, name))
            seen.add(entry.title)

# HTML 생성
html = f"<html><head><meta charset='utf-8'></head><body>"
html += f"<h1>🏠 부동산 종합 리포트 ({datetime.now().strftime('%Y-%m-%d')})</h1>"
html += "<div><strong>매체 바로가기:</strong> " + " | ".join([f"<a href='{link}'>{name}</a>" for name, (rss, link) in SOURCES.items()]) + "</div>"

# 카테고리별 출력 루프
for cat, articles in data.items():
    html += f"<h2>[{cat}]</h2><ul>"
    for title, link, source in articles:
        html += f"<li>[{source}] <a href='{link}'>{title}</a></li>"
    html += "</ul>"

html += "</body></html>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
