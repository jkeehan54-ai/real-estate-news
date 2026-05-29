import feedparser
from datetime import datetime

# 1. 13개 매체 바로가기 링크 (상단 고정)
SOURCES_LINKS = {
    "조선일보": "https://www.chosun.com/economy/realestate/",
    "중앙일보": "https://www.joongang.co.kr/realestate",
    "동아일보": "https://www.donga.com/news/Economy/Realestate",
    "한겨레": "https://www.hani.co.kr/arti/economy/property/",
    "매일경제": "https://www.mk.co.kr/news/realestate/",
    "한국경제": "https://www.hankyung.com/realestate",
    "부산일보": "https://www.busan.com/economy/",
    "국제신문": "https://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0200",
    "네이버부동산": "https://land.naver.com/news/",
    "한국부동산원": "https://www.reb.or.kr/reb/main.do",
    "KB부동산": "https://kbland.kr/",
    "머니투데이": "https://news.mt.co.kr/estate/",
    "연합뉴스": "https://www.yna.co.kr/economy/real-estate/"
}

# 2. 24시간 내 최신 뉴스만 가져오기 위한 검색 쿼리 세팅
def get_google_news_url(site_domain):
    # 'when:1d' 파라미터를 통해 최근 24시간 내 기사만 선별
    return f"https://news.google.com/rss/search?q=site:{site_domain}+부동산+아파트+분양+when:1d&hl=ko&gl=KR&ceid=KR:ko"

# 3. HTML 생성
html = f"""
<html><head><meta charset='utf-8'>
<style>
    body {{font-family: sans-serif; padding: 20px; line-height: 1.6;}}
    .nav-bar {{background: #f8f9fa; padding: 15px; border: 1px solid #ccc; margin-bottom: 25px; border-radius: 5px;}}
    .nav-bar a {{margin-right: 15px; text-decoration: none; color: #0056b3; font-weight: bold; display: inline-block;}}
    h2 {{color: #333; border-bottom: 2px solid #0056b3; margin-top: 30px; padding-bottom: 5px;}}
    ul {{list-style: none; padding-left: 0;}}
    li {{margin-bottom: 8px; border-bottom: 1px solid #eee; padding-bottom: 5px;}}
    a:link {{color: #0000FF !important; text-decoration: none;}}
    a:visited {{color: #800080 !important;}}
</style>
</head><body>
<h1>오늘의 부동산 종합 리포트 ({datetime.now().strftime('%Y-%m-%d')})</h1>
<div class='nav-bar'><strong>매체 바로가기: </strong><br><br>
"""
for name, url in SOURCES_LINKS.items():
    html += f"<a href='{url}' target='_blank'>{name}</a>"
html += "</div>"

# 4. 뉴스 수집 로직
for name, domain in SOURCES_LINKS.items():
    html += f"<h2>[{name}] 부동산 최신 이슈</h2><ul>"
    url = get_google_news_url(domain.split('//')[-1].split('/')[0])
    feed = feedparser.parse(url)
    
    entries = feed.entries
    if not entries:
        html += "<li>최근 24시간 내 등록된 부동산 뉴스가 없습니다.</li>"
    else:
        for entry in entries[:6]: # 매체별 최신 6개 기사 출력
            html += f"<li><a href='{entry.link}' target='_blank'>{entry.title}</a></li>"
    html += "</ul>"

html += "</body></html>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
