import feedparser
from datetime import datetime

# 1. 13개 매체와 피드 URL 1:1 매칭
# RSS 피드가 없는 경우 Google 뉴스 검색 API를 통해 실시간 데이터를 수집
SOURCES = {
    "조선일보": "https://www.chosun.com/arc/outboundfeeds/rss/category/economy/?outputType=xml",
    "중앙일보": "https://rss.joins.com/joins_realestate_list.xml",
    "동아일보": "https://rss.donga.com/economy.xml",
    "한겨레": "https://www.hani.co.kr/rss/economy/",
    "매일경제": "https://www.mk.co.kr/rss/realestate.xml",
    "한국경제": "https://www.hankyung.com/feed/realestate",
    "부산일보": "http://www.busan.com/rss/pc/economy.xml",
    "국제신문": "http://www.kookje.co.kr/news2011/rss/rss_0200.xml",
    "네이버부동산": "https://news.google.com/rss/search?q=부동산+아파트+분양",
    "한국부동산원": "https://news.google.com/rss/search?q=한국부동산원+부동산",
    "KB부동산": "https://news.google.com/rss/search?q=KB부동산+아파트",
    "머니투데이": "https://news.mt.co.kr/rss/view.mt?type=estate",
    "연합뉴스": "https://www.yna.co.kr/rss/economy/real-estate.xml"
}

# 2. HTML 스타일 설정 및 파일 생성
html = f"""
<html><head><meta charset='utf-8'>
<style>
    body {{font-family: sans-serif; padding: 20px; line-height: 1.6;}}
    h2 {{color: #0056b3; border-bottom: 2px solid #0056b3; margin-top: 30px;}}
    ul {{list-style-type: none; padding-left: 0;}}
    li {{margin-bottom: 8px; border-bottom: 1px solid #eee; padding-bottom: 5px;}}
    a:link {{color: #0000FF !important; text-decoration: none;}}
    a:visited {{color: #800080 !important;}}
</style>
</head><body>
<h1>오늘의 부동산 종합 리포트 ({datetime.now().strftime('%Y-%m-%d')})</h1>
"""

# 3. 데이터 수집 및 노출
for name, url in SOURCES.items():
    html += f"<h2>[{name}] 부동산 주요 이슈</h2><ul>"
    feed = feedparser.parse(url)
    
    entries = feed.entries
    if not entries:
        html += "<li>현재 수집된 기사가 없습니다.</li>"
    else:
        for entry in entries[:10]:  # 매체당 최대 10개
            html += f"<li><a href='{entry.link}' target='_blank'>{entry.title}</a></li>"
    html += "</ul>"

html += "</body></html>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
