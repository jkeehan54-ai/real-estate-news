import feedparser
from datetime import datetime

# 1. 키워드 설정
KEYWORDS = ["집값/아파트값", "부동산정책", "부동산규제", "부동산세금", "청약", "분양", "전세", "금리", "대출", "재개발", "재건축", "오피스텔", "공급", "인테리어", "경매", "교통호재", "지역개발"]

# 2. 매체 바로가기
SOURCES = {
    "조선일보": "https://www.chosun.com/economy/", "중앙일보": "https://www.joongang.co.kr/realestate",
    "동아일보": "https://www.donga.com/news/Economy/Realestate", "한겨레": "https://www.hani.co.kr/arti/economy/property/",
    "매일경제": "https://www.mk.co.kr/news/realestate/", "한국경제": "https://www.hankyung.com/realestate",
    "부산일보": "https://www.busan.com/economy/", "국제신문": "https://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0200&vHeadTitle=%B0%E6%C1%A6",
    "네이버부동산": "https://land.naver.com/", "한국부동산원": "https://www.reb.or.kr/reb/main.do",
    "KB부동산": "https://kbland.kr/", "머니투데이": "https://www.mt.co.kr/estate", "연합뉴스": "https://www.yna.co.kr/economy/real-estate"
}

# 3. 13개 매체 피드
FEEDS = {
    "조선일보": "https://www.chosun.com/arc/outboundfeeds/rss/category/economy/?outputType=xml",
    "중앙일보": "https://rss.joins.com/joins_realestate_list.xml",
    "동아일보": "https://rss.donga.com/economy.xml",
    "한겨레": "https://www.hani.co.kr/rss/economy/",
    "매일경제": "https://www.mk.co.kr/rss/realestate.xml",
    "한국경제": "https://www.hankyung.com/feed/realestate",
    "부산일보": "http://www.busan.com/rss/pc/economy.xml",
    "국제신문": "http://www.kookje.co.kr/news2011/rss/rss_0200.xml",
    "네이버부동산": "https://news.google.com/rss/search?q=부동산+아파트+소식",
    "한국부동산원": "https://news.google.com/rss/search?q=부동산+아파트+동향",
    "KB부동산": "https://news.google.com/rss/search?q=부동산+아파트+시세",
    "머니투데이": "https://news.mt.co.kr/rss/view.mt?type=estate",
    "연합뉴스": "https://www.yna.co.kr/rss/economy/real-estate.xml"
}

# 4. HTML 생성 (파란색 링크 + 방문 시 보라색으로 변경)
html = """
<html><head><meta charset='utf-8'>
<style>
    body{font-family:sans-serif; padding:15px;}
    .source-bar{margin-bottom:20px; padding:15px; background:#f0f0ff; border-radius:8px;}
    .source-bar a{margin:5px; display:inline-block; padding:8px 12px; background:#fff; border:1px solid #ccc; text-decoration:none; color:#0056b3; font-size:0.9em; border-radius:4px;}
    h2{font-size:1.1em; color:#0056b3; border-left:4px solid #0056b3; padding-left:10px; margin-top:25px; background:#f0f7ff;}
    ul{list-style-type:none; padding-left:10px;}
    li{margin-bottom:8px;}
    a:link {color: #0000FF; text-decoration: none;}
    a:visited {color: #800080;}
</style>
</head><body>
<h1>오늘의 부동산 뉴스 ({})</h1>
<div class='source-bar'><strong>매체 바로가기: </strong>
""".format(datetime.now().strftime('%Y-%m-%d'))

for name, url in SOURCES.items():
    html += f"<a href='{url}' target='_blank'>{name}</a>"
html += "</div>"

# 5. 데이터 수집 및 엄격한 키워드 필터링
all_entries = []
for name, url in FEEDS.items():
    all_entries.extend(feedparser.parse(url).entries)

for keyword in KEYWORDS:
    html += f"<h2>#{keyword}</h2><ul>"
    count = 0
    # 키워드 세분화: 통합 단어 외에는 검색 키워드를 엄격하게 제한
    terms = ["집값", "아파트값"] if keyword == "집값/아파트값" else [keyword.replace("부동산", "")]
    
    seen = set()
    for e in all_entries:
        if e.link in seen: continue
        # 제목에 키워드가 정확히 포함된 경우만 수집
        if any(t in e.title for t in terms):
            html += f"<li><a href='{e.link}' target='_blank'>{e.title}</a></li>"
            seen.add(e.link)
            count += 1
        if count >= 6: break
            
    if count == 0: html += "<li>관련 뉴스가 없습니다.</li>"
    html += "</ul>"

html += "</body></html>"
with open("index.html", "w", encoding="utf-8") as f: f.write(html)
