import feedparser

# 1. 뉴스 키워드 및 매체 리스트 정의
KEYWORDS = ["청약", "분양", "집값", "전세", "금리", "재개발", "재건축", "대출", "부동산규제", "오피스텔", "공급"]
# 주요 매체 바로가기 링크 설정 (사용자님이 자주 보시는 곳들로 추가 가능)
SOURCES = {
    "조선일보": "https://www.chosun.com/economy/realestate/",
    "중앙일보": "https://www.joongang.co.kr/realestate",
    "머니투데이": "https://news.mt.co.kr/newsList.html?pDepth1=estate",
    "연합뉴스": "https://www.yna.co.kr/economy/real-estate"
}

RSS_URL = "https://news.google.com/rss/search?q=%EB%B6%90%EB%8F%99%EC%82%B0+OR+%EC%95%84%ED%8C%8C%ED%8A%B8&hl=ko&gl=KR&ceid=KR:ko"
feed = feedparser.parse(RSS_URL)

# 2. HTML 구성
html = "<html><head><meta charset='utf-8'><style>body{font-family:sans-serif; padding:15px;} .source-bar{margin-bottom:20px; padding:10px; background:#f4f4f4;} .source-bar a{margin-right:10px; text-decoration:none; color:blue; font-weight:bold;}</style></head><body>"

# 상단 매체 바로가기 바 생성
html += "<h1>부동산 맞춤 뉴스</h1><div class='source-bar'><strong>매체 바로가기: </strong>"
for name, url in SOURCES.items():
    html += f"<a href='{url}' target='_blank'>{name}</a>"
html += "</div>"

# 카테고리별 뉴스 본문 생성
for keyword in KEYWORDS:
    html += f"<h2>#{keyword}</h2><ul>"
    found = False
    for entry in feed.entries:
        if keyword in entry.title:
            html += f"<li><a href='{entry.link}' target='_blank'>{entry.title}</a></li>"
            found = True
    if not found:
        html += "<li>해당 키워드 뉴스가 없습니다.</li>"
    html += "</ul>"

html += "</body></html>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
