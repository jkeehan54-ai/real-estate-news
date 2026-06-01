import feedparser
from datetime import datetime

# 1. 13개 매체 데이터 (RSS 주소 중심)
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
    if any(k in t for k in ["분양", "청약", "공급"]): return "청약/분양"
    if any(k in t for k in ["재건축", "재개발"]): return "재건축"
    if any(k in t for k in ["세금", "종부세", "취득세"]): return "세제"
    if any(k in t for k in ["정부", "규제", "대출", "금리", "정책"]): return "정책"
    return "시장동향"

# 2. 수집 및 중복 제거 (세트 기반의 빠른 처리)
data = {cat: [] for cat in ["청약/분양", "재건축", "세제", "정책", "시장동향"]}
seen_titles = set() 

for name, (rss_url, link_url) in SOURCES.items():
    feed = feedparser.parse(rss_url)
    for entry in feed.entries[:3]:
        if entry.title not in seen_titles:
            cat = get_category(entry.title)
            data[cat].append({'title': entry.title, 'link': entry.link, 'source': name})
            seen_titles.add(entry.title)

# 3. HTML 생성 (단일 루프)
html = f"<html><body><h1>🏠 부동산 종합 리포트 ({datetime.now().strftime('%Y-%m-%d')})</h1>"
html += "<div><strong>매체 바로가기:</strong> " + " | ".join([f"<a href='{link}'>{name}</a>" for name, (rss, link) in SOURCES.items()]) + "</div>"
html += f"<h2>📊 KB부동산 시황 요약</h2><p>전국 매매가격 0.05% 상승, 매수우위지수 62.9% [참조: image_446c75.jpg]</p>"

for cat, articles in data.items():
    html += f"<h2>[{cat}]</h2><ul>"
    for art in articles:
        html += f"<li>[{art['source']}] <a href='{art['link']}'>{art['title']}</a></li>"
    html += "</ul>"
html += "</body></html>"
