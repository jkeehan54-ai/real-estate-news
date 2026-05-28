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

# &sort=date 를 추가하여 최신순으로 정렬
RSS_URL = "https://news.google.com/rss/search?q=%EB%B6%90%EB%8F%99%EC%82%B0+OR+%EC%95%84%ED%8C%8C%ED%8A%B8&hl=ko&gl=KR&ceid=KR:ko&sort=date"
feed = feedparser.parse(RSS_URL)

# 2. HTML 구성 (디자인 포함)
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

# 3. 뉴스 데이터 처리 (중복 제거 및 최신성 우선)
for keyword in KEYWORDS:
    html += f"<h2>#{keyword}</h2><ul>"
    found = False
    seen_keys = set()
    
    # 최신순으로 정렬된 데이터를 하나씩 처리
    for entry in feed.entries:
        if keyword in entry.title:
            # 특수문자 제거 후 5자 이상 명사 조합으로 고유 키 생성
            words = re.findall(r'[가-힣]{2,}', entry.title)
            topic_key = "_".join(words[:2]) # 앞 단어 2개 조합으로 더 엄격하게 중복 판단
            
            if topic_key in seen_keys:
                continue
            
            html += f"<li><a href='{entry.link}' target='_blank'>{entry.title}</a></li>"
            seen_keys.add(topic_key)
            found = True
            
            # 키워드별로 너무 많은 기사가 나오지 않게 5개로 제한
            if len(seen_keys) >= 5: break
            
    if not found:
        html += "<li>해당 키워드 최신 뉴스가 없습니다.</li>"
    html += "</ul>"

html += "</body></html>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
