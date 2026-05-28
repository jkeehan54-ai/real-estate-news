import feedparser
import time
from datetime import datetime

# 1. 키워드 설정
KEYWORDS = ["집값", "부동산정책", "부동산규제", "부동산세금", "청약", "분양", "전세", "금리", "대출", "재개발", "재건축", "오피스텔", "공급", "인테리어", "경매", "교통호재", "지역개발"]

# 2. 13개 매체 바로가기 리스트
SOURCES = {
    "조선일보": "https://www.chosun.com/economy/",
    "중앙일보": "https://www.joongang.co.kr/realestate",
    "동아일보": "https://www.donga.com/news/Economy/Realestate",
    "한겨레": "https://www.hani.co.kr/arti/economy/property/",
    "매일경제": "https://www.mk.co.kr/news/realestate/",
    "한국경제": "https://www.hankyung.com/realestate",
    "부산일보": "https://www.busan.com/economy/",
    "국제신문": "https://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0200&vHeadTitle=%B0%E6%C1%A6",
    "네이버부동산": "https://land.naver.com/",
    "한국부동산원": "https://www.reb.or.kr/reb/main.do",
    "KB부동산": "https://kbland.kr/",
    "머니투데이": "https://www.mt.co.kr/estate",
    "연합뉴스": "https://www.yna.co.kr/economy/real-estate"
}

# 3. 13개 매체 대응 직접 수집 피드 (공식 RSS 및 대체 수집 경로)
FEEDS = [
    "https://www.chosun.com/arc/outboundfeeds/rss/category/economy/?outputType=xml", # 조선일보
    "https://rss.joins.com/joins_realestate_list.xml",                               # 중앙일보
    "https://rss.donga.com/economy.xml",                                             # 동아일보
    "https://www.hani.co.kr/rss/economy/",                                           # 한겨레
    "https://www.mk.co.kr/rss/realestate.xml",                                       # 매일경제
    "https://www.hankyung.com/feed/realestate",                                      # 한국경제
    "http://www.busan.com/rss/pc/economy.xml",                                       # 부산일보
    "http://www.kookje.co.kr/news2011/rss/rss_0200.xml",                             # 국제신문
    "https://news.google.com/rss/search?q=site:land.naver.com",                      # 네이버부동산(대체)
    "https://news.google.com/rss/search?q=site:reb.or.kr",                           # 한국부동산원(대체)
    "https://news.google.com/rss/search?q=site:kbland.kr",                           # KB부동산(대체)
    "https://news.mt.co.kr/rss/view.mt?type=estate",                                 # 머니투데이
    "https://www.yna.co.kr/rss/economy/real-estate.xml"                              # 연합뉴스
]

today_str = datetime.now().strftime('%Y-%m-%d')

# 4. HTML 생성
html = f"""
<html><head><meta charset='utf-8'>
<style>
    body{{font-family:sans-serif; padding:15px; line-height:1.5;}}
    .source-bar{{margin-bottom:20px; padding:15px; background:#f0f0ff; border-radius:8px;}}
    .source-bar a{{margin:5px; display:inline-block; padding:8px 12px; background:#fff; border:1px solid #ccc; text-decoration:none; color:#000; font-size:0.9em; border-radius:4px;}}
    h2{{font-size:1.1em; color:#0056b3; border-left:4px solid #0056b3; padding-left:10px; margin-top:25px; background:#f0f7ff;}}
</style>
</head><body>
<h1>오늘의 부동산 뉴스 ({today_str})</h1>
<div class='source-bar'><strong>매체 바로가기: </strong>
"""
for name, url in SOURCES.items():
    html += f"<a href='{url}' target='_blank'>{name}</a>"
html += "</div>"

# 5. 모든 데이터 통합 수집
all_entries = []
for url in FEEDS:
    feed = feedparser.parse(url)
    for entry in feed.entries:
        try:
            pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed)).strftime('%Y-%m-%d')
            if pub_date == today_str:
                all_entries.append(entry)
        except: continue

# 6. 키워드별 분류
for keyword in KEYWORDS:
    html += f"<h2>#{keyword}</h2><ul>"
    found_count = 0
    # 제목/본문 키워드 매칭
    matches = [e for e in all_entries if keyword in e.title or (hasattr(e, 'summary') and keyword in e.summary)]
    for entry in matches[:6]:
        html += f"<li><a href='{entry.link}' target='_blank'>{entry.title}</a></li>"
        found_count += 1
            
    if found_count == 0:
        html += "<li style='color:#777;'>오늘 발행된 관련 뉴스가 없습니다.</li>"
    html += "</ul>"

html += "</body></html>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
