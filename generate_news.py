import feedparser

KEYWORDS = ["청약", "분양", "집값", "전세", "금리", "재개발", "재건축", "대출", "부동산규제", "오피스텔", "공급"]
RSS_URL = "https://news.google.com/rss/search?q=%EB%B6%90%EB%8F%99%EC%82%B0+OR+%EC%95%84%ED%8C%8C%ED%8A%B8&hl=ko&gl=KR&ceid=KR:ko"

feed = feedparser.parse(RSS_URL)

html = "<html><head><meta charset='utf-8'><style>body{font-family:sans-serif; padding:10px;} h2{font-size:1.2em; border-left:5px solid #333; padding-left:10px;}</style></head><body><h1>부동산 맞춤 뉴스</h1>"

for keyword in KEYWORDS:
    html += f"<h2>#{keyword}</h2><ul>"
    found = False
    for entry in feed.entries:
        if keyword in entry.title:
            # 제목에서 매체명 분리 (제목 끝의 '- 매체명' 형식 처리)
            title_parts = entry.title.split(' - ')
            clean_title = title_parts[0]
            source = title_parts[-1] if len(title_parts) > 1 else "뉴스"
            
            # 매체명과 제목을 각각 명확하게 배치
            html += f"<li><b>[{source}]</b> <a href='{entry.link}' target='_blank'>{clean_title}</a></li>"
            found = True
    if not found:
        html += "<li>해당 키워드 뉴스가 없습니다.</li>"
    html += "</ul>"

html += "</body></html>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
