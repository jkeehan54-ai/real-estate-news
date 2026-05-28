import feedparser

# 1. 요청하신 순서대로 카테고리 재배치 및 설정
KEYWORDS = ["집값", "부동산정책", "부동산규제", "부동산세금", "청약", "분양", "전세", "금리", "대출", "재개발", "재건축", "오피스텔", "공급", "인테리어", "경매", "교통호재", "지역개발"]

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

# 2. RSS 데이터 가져오기
RSS_URL = "https://news.google.com/rss/search?q=부동산+아파트+주택&hl=ko&gl=KR&ceid=KR:ko"
feed = feedparser.parse(RSS_URL)

# 3. HTML 생성
html = """
<html><head><meta charset='utf-8'>
<style>
    body{font-family:sans-serif; padding:10px;}
    .source-bar{margin-bottom:20px; padding:10px; background:#f4f4f4;}
    .source-bar a{margin-right:10px;}
    h2{color:#333; border-bottom:2px solid #333; padding-bottom:5px; margin-top:30px;}
</style>
</head><body>
<h1>부동산 뉴스 대시보드</h1>
<div class='source-bar'><strong>매체 바로가기: </strong>
"""
for name, url in SOURCES.items():
    html += f"<a href='{url}' target='_blank'>{name}</a>"
html += "</div>"

# 4. 키워드별 매칭 (요청하신 순서대로 처리)
for keyword in KEYWORDS:
    html += f"<h2>#{keyword}</h2><ul>"
    matches = []
    for entry in feed.entries:
        # 제목에서 키워드 포함 여부 확인
        if keyword in entry.title:
            matches.append(f"<li><a href='{entry.link}' target='_blank'>{entry.title}</a></li>")
    
    if matches:
        # 결과가 있으면 최대 5개 표시
        html += "".join(matches[:5])
    else:
        html += "<li>관련 뉴스가 현재 집계되지 않았습니다.</li>"
    html += "</ul>"

html += "</body></html>"

# 5. 파일 저장
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
