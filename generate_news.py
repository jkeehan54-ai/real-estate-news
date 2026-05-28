import feedparser
from datetime import datetime

# 1. 13개 매체 부동산 섹션 최신 RSS/피드 주소
FEEDS = {
    "조선일보": "https://www.chosun.com/arc/outboundfeeds/rss/category/economy/?outputType=xml",
    "중앙일보": "https://rss.joins.com/joins_realestate_list.xml",
    "동아일보": "https://rss.donga.com/economy.xml",
    "한겨레": "https://www.hani.co.kr/rss/economy/",
    "매일경제": "https://www.mk.co.kr/rss/realestate.xml",
    "한국경제": "https://www.hankyung.com/feed/realestate",
    "부산일보": "http://www.busan.com/rss/pc/economy.xml",
    "국제신문": "http://www.kookje.co.kr/news2011/rss/rss_0200.xml",
    "네이버부동산": "https://news.naver.com/main/list.naver?mode=LS2D&mid=shm&sid1=101&sid2=260",
    "한국부동산원": "https://www.reb.or.kr/reb/main.do",
    "KB부동산": "https://kbland.kr/main",
    "머니투데이": "https://news.mt.co.kr/rss/view.mt?type=estate",
    "연합뉴스": "https://www.yna.co.kr/rss/economy/real-estate.xml"
}

# 2. 부동산 관련 키워드 (이 단어가 제목에 있어야만 수집)
KEYWORDS = ["부동산", "아파트", "청약", "분양", "전세", "월세", "금리", "집값", "재건축", "재개발", "오피스텔", "주택"]

html = f"""
<html><head><meta charset='utf-8'>
<style>
    body {{font-family: sans-serif; padding: 20px;}}
    h2 {{color: #0056b3; border-bottom: 2px solid #0056b3; margin-top: 30px;}}
    a:link {{color: #0000FF !important; text-decoration: none;}}
    a:visited {{color: #800080 !important;}}
</style>
</head><body>
<h1>부동산 종합 리포트 ({datetime.now().strftime('%Y-%m-%d')})</h1>
"""

for name, url in FEEDS.items():
    html += f"<h2>[{name}] 부동산 이슈</h2><ul>"
    feed = feedparser.parse(url)
    count = 0
    
    # 기사가 있는 경우 필터링하여 출력
    for entry in feed.entries:
        if any(keyword in entry.title for keyword in KEYWORDS):
            html += f"<li><a href='{entry.link}' target='_blank'>{entry.title}</a></li>"
            count += 1
        if count >= 6: break # 매체당 6개 뉴스만
    
    # 필터링 결과가 없으면 해당 페이지로 안내
    if count == 0:
        html += f"<li><a href='{url}' target='_blank'>[기사 확인] {name} 부동산 페이지 바로가기</a></li>"
    html += "</ul>"

html += "</body></html>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
