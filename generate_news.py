import feedparser

KEYWORDS = ["청약", "분양", "집값", "전세", "금리", "재개발", "재축", "대출", "부동산규제", "오피스텔", "공급"]

# 접속이 더 확실한 고정 URL로 교체했습니다
SOURCES = {
    "조선일보": "https://www.chosun.com/economy/realestate/",
    "중앙일보": "https://www.joongang.co.kr/realestate",
    "동아일보": "https://www.donga.com/news/Economy/Realestate",
    "한겨레": "https://www.hani.co.kr/arti/economy/property/",
    "부산일보": "https://www.busan.com/list/economy/realestate",
    "국제신문": "https://www.kookje.co.kr/news2011/asp/newslist.asp?code=0200",
    "네이버부동산": "https://land.naver.com/",
    "한국부동산원": "https://www.reb.or.kr/reb/main.do",
    "KB부동산": "https://kbland.kr/",
    "머니투데이": "https://news.mt.co.kr/newsList.html?code=estate",
    "연합뉴스": "https://www.yna.co.kr/economy/real-estate"
}

RSS_URL = "https://news.google.com/rss/search?q=%EB%B6%90%EB%8F%99%EC%82%B0+OR+%EC%95%84%ED%8C%8C%ED%8A%B8&hl=ko&gl=KR&ceid=KR:ko"
feed = feedparser.parse(RSS_URL)

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
