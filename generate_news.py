import feedparser
from datetime import datetime

# 1. 뉴스 소스 및 설정
SOURCES = {
    "조선일보": "https://www.chosun.com/arc/outboundfeeds/rss/category/economy/realestate/",
    "중앙일보": "https://rss.joins.com/joins_realestate_list.xml",
    "동아일보": "https://rss.donga.com/economy.xml",
    "한겨레": "https://www.hani.co.kr/rss/economy/",
    "매일경제": "https://www.mk.co.kr/rss/realestate.xml",
    "한국경제": "https://www.hankyung.com/feed/realestate",
    "부산일보": "http://www.busan.com/rss/pc/economy.xml",
    "국제신문": "http://www.kookje.co.kr/news2011/rss/rss_0200.xml",
    "네이버부동산": "https://news.google.com/rss/search?q=네이버부동산+부동산&hl=ko&gl=KR&ceid=KR:ko",
    "한국부동산원": "https://news.google.com/rss/search?q=한국부동산원+부동산&hl=ko&gl=KR&ceid=KR:ko",
    "KB부동산": "https://news.google.com/rss/search?q=KB부동산+부동산+시황&hl=ko&gl=KR&ceid=KR:ko",
    "머니투데이": "https://news.mt.co.kr/rss/view.mt?type=estate",
    "연합뉴스": "https://www.yna.co.kr/rss/economy/real-estate.xml"
}

# 2. 고도화된 필터링 및 카테고리 분류 함수
def get_category(title):
    t = title.lower()
    # 부동산 관련성이 낮은 기사 즉시 제외
    if not any(k in t for k in ["부동산", "아파트", "청약", "분양", "주택", "전세", "재건축", "세금", "공급", "시세"]): return None
    
    if any(k in t for k in ["분양", "청약", "공급"]): return "청약/분양"
    if any(k in t for k in ["재건축", "재개발"]): return "재건축"
    if any(k in t for k in ["세금", "종부세", "취득세", "양도세"]): return "세제"
    if any(k in t for k in ["정부", "규제", "대출", "금리", "정책"]): return "정책"
    return "시장동향"

# 3. 뉴스 수집 로직
data = {cat: [] for cat in ["청약/분양", "재건축", "세제", "정책", "시장동향"]}
seen = set()

for name, rss in SOURCES.items():
    feed = feedparser.parse(rss)
    for entry in feed.entries[:3]:
        if entry.title not in seen:
            cat = get_category(entry.title)
            if cat:
                data[cat].append((entry.title, entry.link, name))
                seen.add(entry.title)

# 4. HTML 생성
html = f"<html><head><meta charset='utf-8'></head><body><h1>🏠 부동산 종합 리포트 ({datetime.now().strftime('%Y-%m-%d')})</h1>"
html += "<div><strong>매체 바로가기:</strong> " + " | ".join([f"<a href='{name}'>{name}</a>" for name in SOURCES.keys()]) + "</div>"

for cat, articles in data.items():
    html += f"<h2>[{cat}]</h2><ul>"
    if not articles: html += "<li>관련 뉴스가 없습니다.</li>"
    for title, link, source in articles:
        html += f"<li>[{source}] <a href='{link}'>{title}</a></li>"
    html += "</ul>"

html += "</body></html>"
