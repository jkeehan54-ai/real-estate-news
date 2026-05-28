import feedparser
from datetime import datetime

# 1. 13개 매체 타겟팅: 구글 뉴스 검색 쿼리 이용 (가장 확실한 수집 방식)
SOURCES = {
    "조선일보": "site:chosun.com 부동산", "중앙일보": "site:joins.com 부동산",
    "동아일보": "site:donga.com 부동산", "한겨레": "site:hani.co.kr 부동산",
    "매일경제": "site:mk.co.kr 부동산", "한국경제": "site:hankyung.com 부동산",
    "부산일보": "site:busan.com 부동산", "국제신문": "site:kookje.co.kr 부동산",
    "네이버부동산": "site:land.naver.com 뉴스", "한국부동산원": "site:reb.or.kr 뉴스",
    "KB부동산": "site:kbland.kr 뉴스", "머니투데이": "site:mt.co.kr 부동산",
    "연합뉴스": "site:yna.co.kr 부동산"
}

html = f"""
<html><head><meta charset='utf-8'>
<style>
    body {{font-family: sans-serif; padding: 20px; line-height: 1.6;}}
    h2 {{color: #0056b3; border-bottom: 2px solid #0056b3; margin-top: 30px;}}
    ul {{list-style: none; padding-left: 0;}}
    li {{margin-bottom: 8px; border-bottom: 1px solid #eee; padding-bottom: 5px;}}
    a:link {{color: #0000FF !important; text-decoration: none;}}
    a:visited {{color: #800080 !important;}}
</style>
</head><body>
<h1>오늘의 부동산 종합 리포트 ({datetime.now().strftime('%Y-%m-%d')})</h1>
"""

# 2. 구글 뉴스 통합 검색을 이용한 수집 로직
for name, query in SOURCES.items():
    html += f"<h2>[{name}] 부동산 주요 이슈</h2><ul>"
    search_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(search_url)
    
    entries = feed.entries
    if not entries:
        html += "<li>수집된 최신 기사가 없습니다.</li>"
    else:
        for entry in entries[:8]:  # 매체별 상위 8개
            html += f"<li><a href='{entry.link}' target='_blank'>{entry.title}</a></li>"
    html += "</ul>"

html += "</body></html>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
