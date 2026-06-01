import feedparser
from datetime import datetime

# 오늘 날짜 반영 (2026-06-01)
today_str = datetime.now().strftime('%Y-%m-%d')

# 1. 13개 매체 링크
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

# 2. 통합 뉴스 수집 및 카테고리 분류 로직
def classify_news(title):
    t = title.lower()
    if any(k in t for k in ["분양", "청약", "입주"]): return "청약/분양"
    if any(k in t for k in ["정부", "규제", "세금", "대출", "공급", "정책"]): return "정책/규제"
    if any(k in t for k in ["가격", "상승", "하락", "시세", "거래", "매매", "전세", "월세"]): return "시장동향"
    if any(k in t for k in ["서울", "부산", "수도권", "신도시", "재개발", "재건축"]): return "지역이슈"
    return "기타/산업"

# 뉴스 통합 리스트
all_news = []
# (실제 RSS 파싱 로직은 위 리스트를 순회하며 feedparser로 title과 link 수집)
# 예시로 통합 리스트 구조화
categories = {"청약/분양": [], "정책/규제": [], "시장동향": [], "지역이슈": [], "기타/산업": []}

# 3. HTML 생성
html = f"""
<html><head><meta charset='utf-8'>
<style>
    body {{font-family: sans-serif; padding: 20px;}}
    .nav-bar {{background: #f8f9fa; padding: 10px; margin-bottom: 20px; border-bottom: 2px solid #333;}}
    h2 {{color: #d35400; margin-top: 30px;}}
</style>
</head><body>
<h1>오늘의 부동산 종합 리포트 ({today_str})</h1>
<div class='nav-bar'>매체 바로가기: {" | ".join([f"<a href='{url}'>{name}</a>" for name, url in SOURCES_LINKS.items()])}</div>
"""

# 카테고리별 출력
for cat, news_list in categories.items():
    html += f"<h2>[{cat}]</h2><ul>"
    for item in news_list:
        html += f"<li><a href='{item['link']}'>{item['title']}</a></li>"
    html += "</ul>"

html += "</body></html>"
