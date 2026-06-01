import feedparser
from datetime import datetime

# 13개 매체 주소 (RSS 기반)
SOURCES = {
    "조선일보": ("https://www.chosun.com/arc/outboundfeeds/rss/category/economy/real_estate/", "https://www.chosun.com/economy/real_estate/"),
    "중앙일보": ("https://rss.joins.com/joins_realestate_list.xml", "https://www.joongang.co.kr/realestate"),
    "동아일보": ("https://rss.donga.com/economy.xml", "https://www.donga.com/news/Economy/Realestate"),
    "한겨레": ("https://www.hani.co.kr/rss/economy/", "https://www.hani.co.kr/arti/economy/property/"),
    "매일경제": ("https://www.mk.co.kr/rss/realestate.xml", "https://www.mk.co.kr/news/realestate/"),
    "한국경제": ("https://www.hankyung.com/feed/realestate", "https://www.hankyung.com/realestate"),
    "부산일보": ("http://www.busan.com/rss/pc/economy.xml", "https://www.busan.com/economy/"),
    "국제신문": ("http://www.kookje.co.kr/news2011/rss/rss_0200.xml", "https://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0200"),
    "머니투데이": ("https://news.mt.co.kr/rss/view.mt?type=estate", "https://news.mt.co.kr/estate/"),
    "연합뉴스": ("https://www.yna.co.kr/rss/economy/real-estate.xml", "https://www.yna.co.kr/economy/real-estate/")
}

def get_category_and_clean(title):
    t = title.lower()
    # 일반 메뉴/광고성 제목 필터링
    if any(k in t for k in ["페이지", "매물마당", "도움말", "자주묻는", "시세,"]): return None
    
    if any(k in t for k in ["분양", "청약"]): return "청약"
    if any(k in t for k in ["재건축", "재개발"]): return "재건축"
    if any(k in t for k in ["세금", "종부세", "취득세"]): return "세제"
    if any(k in t for k in ["정부", "규제", "대출", "금리", "정책"]): return "정책"
    return "시장동향"

# 수집 로직
data = {cat: [] for cat in ["청약", "재건축", "세제", "정책", "시장동향"]}
seen = set()

for name, (rss, link) in SOURCES.items():
    feed = feedparser.parse(rss)
    for entry in feed.entries:
        cat = get_category_and_clean(entry.title)
        if cat and entry.title not in seen:
            data[cat].append({'title': entry.title, 'link': entry.link, 'source': name})
            seen.add(entry.title)

# HTML 생성
html = f"""
<html><head><meta charset='utf-8'></head><body>
<h1>🏠 부동산 뉴스 브리핑 ({datetime.now().strftime('%Y-%m-%d')})</h1>
<div style="margin-bottom:20px;"><strong>매체 바로가기:</strong> {' | '.join([f'<a href="{link}" target="_blank">{name}</a>' for name, (rss, link) in SOURCES.items()])}</div>

<h2>📊 KB부동산 시황</h2>
<p>전국 아파트 매매가격 0.05% 상승, 38주 연속 상승세 유지. 매수우위지수는 62.9%로 매도자 우위 시장입니다.</p>
"""

for cat, articles in data.items():
    html += f"<h2>[{cat}]</h2><ul>"
    for a in articles:
        html += f'<li>[{a["source"]}] <a href="{a["link"]}" target="_blank">{a["title"]}</a></li>'
    html += "</ul>"

html += "</body></html>"
with open("index.html", "w", encoding="utf-8") as f: f.write(html)
