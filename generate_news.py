import feedparser
from datetime import datetime

# 1. 각 카테고리별로 기사를 걸러낼 엄격한 검색어 매핑
KEYWORD_MAP = {
    "집값/아파트값": ["집값", "아파트값"],
    "부동산정책": ["정책", "국토부"],
    "부동산규제": ["규제", "대책"],
    "부동산세금": ["세금", "종부세", "취득세"],
    "청약": ["청약"],
    "분양": ["분양"],
    "전세": ["전세", "월세"],
    "금리": ["금리", "통화", "한은"],
    "대출": ["대출", "주담대"],
    "재개발": ["재개발"],
    "재건축": ["재건축"],
    "오피스텔": ["오피스텔"],
    "공급": ["공급", "입주"],
    "인테리어": ["인테리어", "리모델링"],
    "경매": ["경매"],
    "교통호재": ["GTX", "지하철"],
    "지역개발": ["개발", "도시재생"]
}

# 2. 13개 매체 및 피드 리스트
SOURCES = {
    "조선일보": "https://www.chosun.com/economy/", "중앙일보": "https://www.joongang.co.kr/realestate",
    "동아일보": "https://www.donga.com/news/Economy/Realestate", "한겨레": "https://www.hani.co.kr/arti/economy/property/",
    "매일경제": "https://www.mk.co.kr/news/realestate/", "한국경제": "https://www.hankyung.com/realestate",
    "부산일보": "https://www.busan.com/economy/", "국제신문": "https://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0200&vHeadTitle=%B0%E6%C1%A6",
    "네이버부동산": "https://land.naver.com/", "한국부동산원": "https://www.reb.or.kr/reb/main.do",
    "KB부동산": "https://kbland.kr/", "머니투데이": "https://www.mt.co.kr/estate", "연합뉴스": "https://www.yna.co.kr/economy/real-estate"
}

FEEDS = [
    "https://www.mk.co.kr/rss/realestate.xml", "https://www.hankyung.com/feed/realestate",
    "https://www.yna.co.kr/rss/economy/real-estate.xml", "https://news.mt.co.kr/rss/view.mt?type=estate",
    "https://rss.joins.com/joins_realestate_list.xml", "https://www.chosun.com/arc/outboundfeeds/rss/category/economy/?outputType=xml",
    "https://rss.donga.com/economy.xml", "https://www.hani.co.kr/rss/economy/",
    "http://www.busan.com/rss/pc/economy.xml", "http://www.kookje.co.kr/news2011/rss/rss_0200.xml"
]

# 3. 데이터 수집
all_entries = []
for url in FEEDS:
    all_entries.extend(feedparser.parse(url).entries)

# 4. HTML 생성 (CSS 우선순위 강화 및 스타일 고정)
html = f"""
<html><head><meta charset='utf-8'>
<style>
    body {{font-family: sans-serif; padding: 15px;}}
    .source-bar {{margin-bottom: 20px; padding: 15px; background: #f0f0ff; border-radius: 8px;}}
    .source-bar a {{margin: 5px; display: inline-block; padding: 8px 12px; background: #fff; border: 1px solid #ccc; text-decoration: none; color: #0056b3; font-size: 0.9em; border-radius: 4px;}}
    h2 {{font-size: 1.1em; color: #0056b3; border-left: 4px solid #0056b3; padding-left: 10px; margin-top: 25px; background: #f0f7ff;}}
    /* 파란색 링크 유지 및 방문 시 보라색으로 강제 변경 */
    a:link {{color: #0000FF !important; text-decoration: none;}}
    a:visited {{color: #800080 !important;}}
</style>
</head><body>
<h1>오늘의 부동산 뉴스 ({datetime.now().strftime('%Y-%m-%d')})</h1>
<div class='source-bar'><strong>매체 바로가기: </strong>
"""
for name, url in SOURCES.items():
    html += f"<a href='{url}' target='_blank'>{name}</a>"
html += "</div>"

# 5. 키워드별 필터링
for category, keywords in KEYWORD_MAP.items():
    html += f"<h2>#{category}</h2><ul>"
    count = 0
    seen = set()
    for e in all_entries:
        if e.link in seen: continue
        # 각 키워드가 제목에 정확히 들어간 뉴스만 필터링
        if any(k in e.title for k in keywords):
            html += f"<li><a href='{e.link}' target='_blank'>{e.title}</a></li>"
            seen.add(e.link)
            count += 1
        if count >= 6: break
    
    if count == 0: html += "<li>현재 관련 뉴스가 없습니다.</li>"
    html += "</ul>"

html += "</body></html>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
