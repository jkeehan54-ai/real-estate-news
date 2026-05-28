import feedparser
from datetime import datetime

# 1. 키워드 및 필터링 핵심 단어 정의 (매우 엄격하게 설정)
KEYWORD_MAP = {
    "집값/아파트값": ["집값", "아파트값"],
    "부동산정책": ["부동산정책", "부동산 정책", "부동산 대책"],
    "부동산규제": ["부동산규제", "부동산 규제", "대출 규제"],
    "부동산세금": ["부동산 세금", "종부세", "취득세", "양도세"],
    "청약": ["청약"],
    "분양": ["분양"],
    "전세": ["전세", "월세"],
    "금리": ["금리", "기준금리", "통화정책"],
    "대출": ["대출", "주담대"],
    "재개발": ["재개발"],
    "재건축": ["재건축"],
    "오피스텔": ["오피스텔"],
    "공급": ["공급", "입주 물량"],
    "인테리어": ["인테리어", "리모델링"],
    "경매": ["경매"],
    "교통호재": ["GTX", "지하철 연장", "교통 호재"],
    "지역개발": ["도시재생", "지역 개발"]
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

# 4. HTML 생성
html = f"""
<html><head><meta charset='utf-8'>
<style>
    body {{font-family: sans-serif; padding: 15px;}}
    .source-bar {{margin-bottom: 20px; padding: 15px; background: #f0f0ff; border-radius: 8px;}}
    .source-bar a {{margin: 5px; display: inline-block; padding: 8px 12px; background: #fff; border: 1px solid #ccc; text-decoration: none; color: #0056b3; font-size: 0.9em; border-radius: 4px;}}
    h2 {{font-size: 1.1em; color: #0056b3; border-left: 4px solid #0056b3; padding-left: 10px; margin-top: 25px; background: #f0f7ff;}}
    /* 클릭 전 링크 파란색, 클릭 후 보라색 강제 설정 */
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

# 5. 카테고리별 필터링
for category, keywords in KEYWORD_MAP.items():
    html += f"<h2>#{category}</h2><ul>"
    count = 0
    seen = set()
    for e in all_entries:
        if e.link in seen: continue
        # 각 카테고리의 필수 키워드가 제목에 포함된 경우만 수집
        if any(k in e.title for k in keywords):
            html += f"<li><a href='{e.link}' target='_blank'>{e.title}</a></li>"
            seen.add(e.link)
            count += 1
        if count >= 6: break
    
    if count == 0: html += "<li>현재 해당 카테고리에 올라온 관련 뉴스가 없습니다.</li>"
    html += "</ul>"

html += "</body></html>"

# 6. 파일 저장
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
