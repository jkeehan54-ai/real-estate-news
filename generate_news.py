import feedparser

# RSS URL
url = "https://news.google.com/rss/search?q=%EB%B6%90%EB%8F%99%EC%82%B0+OR+%EC%95%84%ED%8C%8C%ED%8A%B8&hl=ko&gl=KR&ceid=KR:ko"
feed = feedparser.parse(url)

html = "<html><body><h1>부동산 뉴스</h1><ul>"
for entry in feed.entries[:10]: # 최신 10개만
    html += f"<li><a href='{entry.link}'>{entry.title}</a></li>"
html += "</ul></body></html>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
