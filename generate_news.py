import feedparser
import time
from datetime import datetime

# 1. 키워드 및 매체 설정
KEYWORDS = ["집값", "부동산정책", "부동산규제", "부동산세금", "청약", "분양", "전세", "금리", "대출", "재개발", "재건축", "오피스텔", "공급", "인테리어", "경매", "교통호재", "지역개발"]

SOURCES = {
    "조선일보": "chosun.com", "중앙일보": "joongang.co.kr", "동아일보": "donga.com", 
    "한겨레": "hani.co.kr", "매일경제": "mk.co.kr", "한국경제": "hankyung.com", 
    "부산일보": "busan.com", "국제신문": "kookje.co.kr", "네이버부동산": "land.naver.com", 
    "한국부동산원": "reb.or.kr", "KB부동산": "kbland.kr", "머니투데이": "mt.co.kr", "연합뉴스": "yna.co.kr"
}

# 2. 13개 매체를 사이트별로 검색하는 통합 쿼리 생성
query = "부동산 아파트 (" + " OR ".join([f"site:{url}" for url in SOURCES.values()]) + ")"
RSS_URL = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko&sort=date"
feed = feedparser.parse(RSS_URL)

today_str = datetime.now().strftime('%Y-%m-%d')

# 3. HTML 생성
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
    html += f"<a href='https://{url}' target='_blank'>{name}</a>"
html += "</div>"

# 4. 수집 및 분류
for keyword in KEYWORDS:
    html += f"<h2>#{keyword}</h2><ul>"
    found_count = 0
    for entry in feed.entries:
        try:
            pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed)).strftime('%Y-%m-%d')
            if pub_date == today_str and keyword in entry.title:
                html += f"<li><a href='{entry.link}' target='_blank'>{entry.title}</a></li>"
                found_count += 1
        except: continue
        if found_count >= 5: break
    if found_count == 0:
        html += "<li>오늘 발행된 관련 뉴스가 없습니다.</li>"
    html += "</ul>"

html += "</body></html>"
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
