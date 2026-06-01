import feedparser
from datetime import datetime

# 1. 13개 매체 전체 정의
SOURCES = {
    "조선일보": "chosun.com", "중앙일보": "joins.com", "동아일보": "donga.com",
    "한겨레": "hani.co.kr", "매일경제": "mk.co.kr", "한국경제": "hankyung.com",
    "부산일보": "busan.com", "국제신문": "kookje.co.kr", "네이버부동산": "land.naver.com",
    "한국부동산원": "reb.or.kr", "KB부동산": "kbland.kr", "머니투데이": "mt.co.kr",
    "연합뉴스": "yna.co.kr"
}

# 2. 카테고리 분류 함수
def get_category(title):
    t = title.lower()
    if any(k in t for k in ["분양", "청약"]): return "청약"
    if any(k in t for k in ["재건축", "재개발"]): return "재건축"
    if any(k in t for k in ["세금", "종부세", "취득세"]): return "세제"
    if any(k in t for k in ["정부", "규제", "대출", "금리"]): return "정책"
    return "전체"

# 3. 뉴스 수집 로직 (13개 매체 전체 순회)
articles = []
seen = set()

for name, domain in SOURCES.items():
    # 구글 뉴스 검색을 통해 13개 매체로부터 부동산 관련 최신 뉴스 수집
    feed = feedparser.parse(f"https://news.google.com/rss/search?q=site:{domain}+부동산+when:7d&hl=ko&gl=KR&ceid=KR:ko")
    for entry in feed.entries[:3]:
        if entry.title not in seen:
            articles.append({
                "title": entry.title,
                "source": name,
                "category": get_category(entry.title),
                "link": entry.link
            })
            seen.add(entry.title)

# 4. HTML 생성
html = f"""
<html><head><meta charset='utf-8'>
<style>
    body {{font-family: 'Malgun Gothic', sans-serif; padding: 20px; line-height: 1.6;}}
    .article-box {{margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 10px;}}
    .category {{font-weight: bold; color: #3498db;}}
</style>
</head><body>
<h1>🏠 오늘의 부동산 종합 리포트 ({datetime.now().strftime('%Y-%m-%d')})</h1>

<h2>🔥 TOP 이슈</h2>
"""

for art in articles[:5]:
    html += f"<div class='article-box'><b>{art['title']}</b><br><small>{art['source']}</small></div>"

html += "<h2>📰 전체 뉴스</h2>"
for art in articles:
    html += f"""
    <div class='article-box'>
        <span class='category'>[{art['category']}]</span>
        <a href='{art['link']}' target='_blank'>{art['title']}</a><br>
        <small>{art['source']}</small>
    </div>"""

html += "</body></html>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
