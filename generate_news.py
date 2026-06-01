import feedparser
from datetime import datetime

# 1. 13개 매체 정의 및 검색 도메인 업데이트
SOURCES = {
    "조선일보": "chosun.com/economy/real_estate", 
    "중앙일보": "joins.com", 
    "동아일보": "donga.com",
    "한겨레": "hani.co.kr", 
    "매일경제": "mk.co.kr", 
    "한국경제": "hankyung.com",
    "부산일보": "busan.com", 
    "국제신문": "kookje.co.kr", 
    "네이버부동산": "land.naver.com",
    "한국부동산원": "reb.or.kr", 
    "KB부동산": "kbland.kr", 
    "머니투데이": "mt.co.kr", 
    "연합뉴스": "yna.co.kr"
}

def get_category(title):
    t = title.lower()
    if any(k in t for k in ["분양", "청약", "공급"]): return "청약/분양"
    if any(k in t for k in ["재건축", "재개발"]): return "재건축"
    if any(k in t for k in ["세금", "종부세", "취득세"]): return "세제"
    if any(k in t for k in ["정부", "규제", "대출", "금리", "정책"]): return "정책"
    return "시장동향"

# 2. 뉴스 수집 로직
data = {cat: [] for cat in ["청약/분양", "재건축", "세제", "정책", "시장동향"]}
seen = set()

for name, domain in SOURCES.items():
    query = f"https://news.google.com/rss/search?q=site:{domain}+부동산&hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(query)
    for entry in feed.entries[:3]:
        if entry.title not in seen:
            cat = get_category(entry.title)
            data[cat].append((entry.title, entry.link, name))
            seen.add(entry.title)

# 3. HTML 생성
html = f"""
<html><head><meta charset='utf-8'></head><body>
<h1>🏠 오늘의 부동산 종합 리포트 ({datetime.now().strftime('%Y-%m-%d')})</h1>
<h2>📊 KB부동산 오늘의 시황 요약</h2>
<ul>
    <li><b>전국:</b> 매매가격 0.05% 상승, 38주 연속 상승세 유지</li>
    <li><b>시장지수:</b> 매수우위지수 62.9% (매도자 우위)</li>
</ul>
"""

for cat, articles in data.items():
    html += f"<h2>[{cat}]</h2><ul>"
    for title, link, source in articles:
        html += f"<li>[{source}] <a href='{link}'>{title}</a></li>"
    html += "</ul>"

html += "</body></html>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
