import feedparser
from datetime import datetime

# 1. 13개 매체 및 검색용 도메인
SOURCES_LINKS = {
    "조선일보": ("chosun.com", "https://www.chosun.com/economy/realestate/"),
    "중앙일보": ("joins.com", "https://www.joongang.co.kr/realestate"),
    "동아일보": ("donga.com", "https://www.donga.com/news/Economy/Realestate"),
    "한겨레": ("hani.co.kr", "https://www.hani.co.kr/arti/economy/property/"),
    "매일경제": ("mk.co.kr", "https://www.mk.co.kr/news/realestate/"),
    "한국경제": ("hankyung.com", "https://www.hankyung.com/realestate"),
    "부산일보": ("busan.com", "https://www.busan.com/economy/"),
    "국제신문": ("kookje.co.kr", "https://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0200"),
    "네이버부동산": ("land.naver.com", "https://land.naver.com/news/"),
    "한국부동산원": ("reb.or.kr", "https://www.reb.or.kr/reb/main.do"),
    "KB부동산": ("kbland.kr", "https://kbland.kr/"),
    "머니투데이": ("mt.co.kr", "https://news.mt.co.kr/estate/"),
    "연합뉴스": ("yna.co.kr", "https://www.yna.co.kr/economy/real-estate/")
}

# 2. 카테고리 분류 함수
def get_category(title):
    t = title.lower()
    if any(k in t for k in ["분양", "청약", "입주", "공급"]): return "청약/분양"
    if any(k in t for k in ["정부", "규제", "세금", "대출", "정책", "금리"]): return "정책/규제"
    if any(k in t for k in ["매매", "전세", "월세", "시세", "가격", "거래"]): return "시장동향"
    if any(k in t for k in ["서울", "부산", "수도권", "재건축", "재개발", "도시"]): return "지역이슈"
    return "기타/산업"

# 3. 뉴스 통합 및 수집
categories = {"청약/분양": [], "정책/규제": [], "시장동향": [], "지역이슈": [], "기타/산업": []}

for name, (domain, url) in SOURCES_LINKS.items():
    search_url = f"https://news.google.com/rss/search?q=site:{domain}+부동산+when:7d&hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(search_url)
    for entry in feed.entries[:3]: # 매체당 최신 3개씩 수집
        cat = get_category(entry.title)
        categories[cat].append({'title': entry.title, 'link': entry.link, 'source': name})

# 4. HTML 생성
html = f"""
<html><head><meta charset='utf-8'>
<style>
    body {{font-family: sans-serif; padding: 20px; line-height: 1.6;}}
    .nav-bar {{background: #f8f9fa; padding: 15px; border: 1px solid #ccc; margin-bottom: 25px;}}
    .nav-bar a {{margin-right: 15px; text-decoration: none; color: #0056b3; font-weight: bold;}}
    h2 {{color: #fff; background: #0056b3; padding: 10px; margin-top: 30px; border-radius: 5px;}}
    ul {{list-style: none; padding-left: 0;}}
    li {{margin-bottom: 8px; border-bottom: 1px solid #eee; padding-bottom: 5px;}}
</style>
</head><body>
<h1>오늘의 부동산 종합 리포트 ({datetime.now().strftime('%Y-%m-%d')})</h1>
<div class='nav-bar'><strong>매체 바로가기: </strong><br><br>
"""
for name, (domain, url) in SOURCES_LINKS.items():
    html += f"<a href='{url}' target='_blank'>{name}</a>"
html += "</div>"

for cat, news_list in categories.items():
    html += f"<h2>{cat}</h2><ul>"
    if not news_list: html += "<li>최신 뉴스가 없습니다.</li>"
    for item in news_list:
        html += f"<li>[{item['source']}] <a href='{item['link']}' target='_blank'>{item['title']}</a></li>"
    html += "</ul>"

html += "</body></html>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
