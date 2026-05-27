import feedparser

# 1. 사용자님의 11가지 키워드 정의
KEYWORDS = ["청약", "분양", "집값", "전세", "금리", "재개발", "재건축", "대출", "부동산규제", "오피스텔", "공급"]
RSS_URL = "https://news.google.com/rss/search?q=%EB%B6%90%EB%8F%99%EC%82%B0+OR+%EC%95%84%ED%8C%8C%ED%8A%B8&hl=ko&gl=KR&ceid=KR:ko"

feed = feedparser.parse(RSS_URL)

# 2. HTML 구조 생성 시작
html = "<html><head><meta charset='utf-8'></head><body><h1>부동산 맞춤 뉴스</h1>"

# 3. 카테고리별 분류 및 출력
for keyword in KEYWORDS:
    html += f"<h2>#{keyword}</h2><ul>"
    found = False
    for entry in feed.entries:
        if keyword in entry.title:
            # 매체명은 feedparser의 source 객체나 title에서 추출 가능
            source = entry.get('source', {}).get('title', '일반매체')
            html += f"<li>[{source}] <a href='{entry.link}'>{entry.title}</a></li>"
            found = True
    if not found:
        html += "<li>해당 키워드 뉴스가 없습니다.</li>"
    html += "</ul>"

html += "</body></html>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
