import feedparser
from datetime import datetime

# 1. 13개 매체 부동산 전문 RSS/검색 피드 (수집폭 극대화)
SOURCES = {
    "조선일보": "https://www.chosun.com/economy/", "중앙일보": "https://www.joongang.co.kr/realestate",
    "동아일보": "https://www.donga.com/news/Economy/Realestate", "한겨레": "https://www.hani.co.kr/rss/economy/",
    "매일경제": "https://www.mk.co.kr/rss/realestate.xml", "한국경제": "https://www.hankyung.com/feed/realestate",
    "부산일보": "http://www.busan.com/rss/pc/economy.xml", "국제신문": "http://www.kookje.co.kr/news2011/rss/rss_0200.xml",
    "네이버부동산": "https://news.google.com/rss/search?q=부동산+아파트+분양+청약",
    "한국부동산원": "https://news.google.com/rss/search?q=한국부동산원+뉴스",
    "KB부동산": "https://news.google.com/rss/search?q=KB부동산+아파트",
    "머니투데이": "https://news.mt.co.kr/rss/view.mt?type=estate", "연합뉴스": "https://www.yna.co.kr/rss/economy/real-estate.xml"
}

# 2. 데이터 수집 (모든 기사를 일단 다 가져옵니다)
all_entries = []
for name, url in SOURCES.items():
    feed = feedparser.parse(url)
    for entry in feed.entries:
        all_entries.append({
            "title": entry.title,
            "link": entry.link,
            "category": name # 매체별 카테고리 기입
        })

# 3. HTML 생성 및 스타일 적용 (방문 링크 보라색 강제)
html = f"""
<html><head><meta charset='utf-8'>
<style>
    body {{font-family: sans-serif; padding: 20px;}}
    h2 {{color: #0056b3; border-bottom: 2px solid #0056b3; margin-top: 40px;}}
    a:link {{color: #0000FF !important; text-decoration: none;}}
    a:visited {{color: #800080 !important;}}
    ul {{list-style: none; padding: 0;}}
    li {{margin-bottom: 10px; padding: 5px; border-bottom: 1px solid #eee;}}
</style>
</head><body>
<h1>부동산 종합 뉴스 리포트 ({datetime.now().strftime('%Y-%m-%d')})</h1>
<p>매체별 부동산 주요 이슈를 실시간 종합한 리스트입니다.</p>
"""

# 4. 단순 나열이 아닌 매체별 묶음으로 노출 (뉴스가 끊기지 않도록)
for name, url in SOURCES.items():
    html += f"<h2>[{name}] 부동산 이슈</h2><ul>"
    count = 0
    for e in all_entries:
        if e['category'] == name:
            html += f"<li><a href='{e['link']}' target='_blank'>{e['title']}</a></li>"
            count += 1
        if count >= 10: break # 매체당 10개씩 노출
    html += "</ul>"

html += "</body></html>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
