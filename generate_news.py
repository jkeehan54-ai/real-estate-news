import feedparser
from datetime import datetime

# 1. 13개 매체 바로가기 링크
SOURCES_LINKS = {
    "조선일보": "https://www.chosun.com/economy/realestate/",
    "중앙일보": "https://www.joongang.co.kr/realestate",
    "동아일보": "https://www.donga.com/news/Economy/Realestate",
    "한겨레": "https://www.hani.co.kr/arti/economy/property/",
    "매일경제": "https://www.mk.co.kr/news/realestate/",
    "한국경제": "https://www.hankyung.com/realestate",
    "부산일보": "https://www.busan.com/economy/",
    "국제신문": "https://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0200",
    "네이버부동산": "https://land.naver.com/news/",
    "한국부동산원": "https://www.reb.or.kr/reb/main.do",
    "KB부동산": "https://kbland.kr/",
    "머니투데이": "https://news.mt.co.kr/estate/",
    "연합뉴스": "https://www.yna.co.kr/economy/real-estate/"
}

# 2. 13개 매체 뉴스 수집 대상 (RSS 우선)
FEEDS = {
    "조선일보": "https://www.chosun.com/arc/outboundfeeds/rss/category/economy/?outputType=xml",
    "중앙일보": "https://rss.joins.com/joins_realestate_list.xml",
    "동아일보": "https://rss.donga.com/economy.xml",
    "한겨레": "https://www.hani.co.kr/rss/economy/",
    "매일경제": "https://www.mk.co.kr/rss/realestate.xml",
    "한국경제": "https://www.hankyung.com/feed/realestate",
    "부산일보": "http://www.busan.com/rss/pc/economy.xml",
    "국제신문": "http://www.kookje.co.kr/news2011/rss/rss_0200.xml",
    "네이버부동산": "https://news.google.com/rss/search?q=부동산+아파트",
    "한국부동산원": "https://news.google.com/rss/search?q=한국부동산원+부동산뉴스",
    "KB부동산": "https://news.google.com/rss/search?q=KB부동산+아파트뉴스",
    "머니투데이": "https://news.mt.co.kr/rss/view.mt?type=estate",
    "연합뉴스": "https://www.yna.co.kr/rss/economy/real-estate.xml"
}

# 3. HTML 생성
html = f"""
<html><head><meta charset='utf-8'>
<style>
    body {{font-family: sans-serif; padding: 20px; line-height: 1.5;}}
    .nav-bar {{background: #f8f9fa; padding: 15px; border-bottom: 2px solid #ccc; margin-bottom: 20px;}}
    .nav-bar a {{margin-right: 15px; text-decoration: none; color: #0056b3; font-weight: bold;}}
    h2 {{color: #333; border-bottom: 1px solid #333; padding-bottom: 5px; margin-top: 30px;}}
    a:link {{color: #0000FF !important; text-decoration: none;}}
    a:visited {{color: #800080 !important;}}
</style>
</head><body>
<h1>오늘의 부동산 종합 리포트 ({datetime.now().strftime('%Y-%m-%d')})</h1>
<div class='nav-bar'>
"""
for name, url in SOURCES_LINKS.items():
    html += f"<a href='{url}' target='_blank'>{name}</a>"
html += "</div>"

# 4. 13개 매체 뉴스 수집 로직
for name, url in FEEDS.items():
    html += f"<h2>[{name}] 부동산 주요 이슈</h2><ul>"
    feed = feedparser.parse(url)
    count = 0
    for entry in feed.entries:
        # 제목에 부동산 관련 키워드가 포함된 경우만 필터링
        if any(k in entry.title for k in ["부동산", "아파트", "청약", "분양", "전세", "월세", "금리", "집값", "재건축", "재개발"]):
            html += f"<li><a href='{entry.link}' target='_blank'>{entry.title}</a></li>"
            count += 1
        if count >= 8: break
    if count == 0: html += "<li>최신 부동산 관련 뉴스가 없습니다.</li>"
    html += "</ul>"

html += "</body></html>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
