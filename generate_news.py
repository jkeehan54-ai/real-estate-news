import feedparser
import re

# 1. 설정: 키워드 및 매체 리스트
KEYWORDS = ["청약", "분양", "집값", "전세", "금리", "재개발", "재건축", "대출", "부동산규제", "오피스텔", "공급"]

SOURCES = {
    "조선일보": "https://www.chosun.com/economy/",
    "중앙일보": "https://www.joongang.co.kr/realestate",
    "동아일보": "https://www.donga.com/news/Economy/Realestate",
    "한겨레": "https://www.hani.co.kr/arti/economy/property/",
    "부산일보": "https://www.busan.com/economy/",
    "국제신문": "https://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0200&vHeadTitle=%B0%E6%C1%A6",
    "네이버부동산": "https://land.naver.com/",
    "한국부동산원": "https://www.reb.or.kr/reb/main.do",
    "KB부동산": "https://kbland.kr/",
    "머니투데이": "https://www.mt.co.kr/estate",
    "연합뉴스": "https://www.yna.co.kr/economy/real-estate"
}

RSS_URL = "https://news.google.com/rss/search?q=%EB%B6%90%EB%8F%99%EC%82%B0+OR+%EC%95%84%ED%8C%8C%ED%8A%B8&hl=ko&gl=KR&ceid=KR:ko"
feed = feedparser.parse(RSS_URL)

# 2. HTML 구성
html = """
<html><head><meta charset='utf-8'>
<style>
    body{font-family:sans-serif; padding:10px; line-height:1.6;}
    .source-bar{margin-bottom:20px; padding:15px; background:#eef; border-radius:8px;}
    .source-bar a{margin:5px; display:inline-block; padding:8px 12px; background:#fff; border:1px solid #999; text-decoration:none; color:#000; font-size:0.9em; border-radius:4px;}
    .source-bar a:hover{background:#333; color:#fff;}
    h1{font-size:1.5em; margin-bottom:10px;}
    h2{font-size:1.1em; border-left:4px solid #0056b3; padding-left:10px; margin-top:25px; background:#f0f7ff;}
    ul{padding-left:25px;}
    li{margin-bottom:5px;}
</style>
</head><body>
"""

html += "<h1>부동산 맞춤 뉴스</h1><div class='source-bar'><strong>매체 바로가기: </strong>"
for name, url in SOURCES.items():
    html += f"<a href='{url}' target='_blank'>{name}</a>"
html += "</div>"

# 3. 뉴스 데이터 처리 (중복 제거 로직 포함)
for keyword in KEYWORDS:
    html += f"<h2>#{keyword}</h2><ul>"
    found = False
    seen_topics = set()
    
    for entry in feed.entries:
        if keyword in entry.title:
            # 대괄호 태그 제거 및 정규화
            clean_title = re.sub(r'\[.*?\]', '', entry.title).strip()
            # 제목 앞부분 12글자를 기준으로 주제 유사도 판단 (핵심 중복 제거)
            topic = clean_title[:12]
            
            if topic in seen_topics:
                continue
            
            html += f"<li><a href='{entry.link}' target='_blank'>{entry.title}</a></li>"
            seen_topics.add(topic)
            found = True
            
    if not found:
        html += "<li>해당 키워드 뉴스가 없습니다.</li>"
    html += "</ul>"

html += "</body></html>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
