import feedparser
from datetime import datetime

# 1. 13개 언론사의 부동산 전문 RSS 피드 (뉴스 누락 방지)
FEEDS = {
    "조선일보": "https://www.chosun.com/arc/outboundfeeds/rss/category/economy/?outputType=xml",
    "중앙일보": "https://rss.joins.com/joins_realestate_list.xml",
    "동아일보": "https://rss.donga.com/economy.xml",
    "한겨레": "https://www.hani.co.kr/rss/economy/",
    "매일경제": "https://www.mk.co.kr/rss/realestate.xml",
    "한국경제": "https://www.hankyung.com/feed/realestate",
    "부산일보": "http://www.busan.com/rss/pc/economy.xml",
    "국제신문": "http://www.kookje.co.kr/news2011/rss/rss_0200.xml",
    "네이버부동산": "https://news.naver.com/main/list.nhn?mode=LS2D&mid=shm&sid1=101&sid2=260",
    "한국부동산원": "https://www.reb.or.kr/reb/main.do",
    "KB부동산": "https://kbland.kr/main",
    "머니투데이": "https://news.mt.co.kr/rss/view.mt?type=estate",
    "연합뉴스": "https://www.yna.co.kr/rss/economy/real-estate.xml"
}

# 2. HTML 생성
html = f"""
<html><head><meta charset='utf-8'>
<style>
    body {{font-family: sans-serif; padding: 20px;}}
    .nav-bar {{margin-bottom: 20px;}}
    .nav-bar a {{margin-right: 15px; text-decoration: none; color: #0056b3; font-weight: bold;}}
    h2 {{color: #333; border-bottom: 2px solid #333; margin-top: 30px;}}
    a:link {{color: #0000FF !important; text-decoration: none;}}
    a:visited {{color: #800080 !important;}}
</style>
</head><body>
<h1>부동산 종합 리포트 ({datetime.now().strftime('%Y-%m-%d')})</h1>
<div class='nav-bar'>
"""

# 상단 바로가기 메뉴
for name, url in FEEDS.items():
    html += f"<a href='{url}' target='_blank'>{name}</a>"
html += "</div>"

# 3. 데이터 수집 및 본문 생성
for name, url in FEEDS.items():
    html += f"<h2>[{name}] 부동산 이슈</h2><ul>"
    feed = feedparser.parse(url)
    if not feed.entries:
        html += f"<li><a href='{url}' target='_blank'>[직접 확인하기] {name} 부동산 섹션으로 이동</a></li>"
    else:
        for entry in feed.entries[:8]:
            html += f"<li><a href='{entry.link}' target='_blank'>{entry.title}</a></li>"
    html += "</ul>"

html += "</body></html>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
