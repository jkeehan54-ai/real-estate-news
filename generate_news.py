import feedparser
from datetime import datetime

# 1. 13개 매체 정의 (RSS 및 검색용 도메인)
SOURCES = {
    "조선일보": "chosun.com/economy/real_estate", "중앙일보": "joins.com/realestate",
    "동아일보": "donga.com/news/Economy/Realestate", "한겨레": "hani.co.kr/arti/economy/property",
    "매일경제": "mk.co.kr/news/realestate", "한국경제": "hankyung.com/realestate",
    "부산일보": "busan.com/economy", "국제신문": "kookje.co.kr",
    "네이버부동산": "land.naver.com", "한국부동산원": "reb.or.kr",
    "KB부동산": "kbland.kr", "머니투데이": "news.mt.co.kr/estate", "연합뉴스": "yna.co.kr/economy/real-estate"
}

# 2. 부동산 키워드 필터링 및 카테고리 분류
def get_category(title):
    t = title.lower()
    if any(k in t for k in ["분양", "청약", "공급"]): return "청약"
    if any(k in t for k in ["재건축", "재개발"]): return "재건축"
    if any(k in t for k in ["세금", "종부세", "취득세", "양도세"]): return "세제"
    if any(k in t for k in ["정부", "규제", "대출", "금리", "정책", "부동산법"]): return "정책"
    return "시장동향"

# 3. 뉴스 수집 로직 (구글 검색 활용으로 수량 대폭 확보)
data = {cat: [] for cat in ["청약", "재건축", "세제", "정책", "시장동향"]}
seen = set()

for name, domain in SOURCES.items():
    # 검색 쿼리를 더 넓게 설정하여 뉴스 수량 확보
    query = f"https://news.google.com/rss/search?q=site:{domain}+부동산&hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(query)
    for entry in feed.entries[:10]: # 매체당 최대 10개까지 수집
        if entry.title not in seen:
            cat = get_category(entry.title)
            data[cat].append({'title': entry.title, 'link': entry.link, 'source': name})
            seen.add(entry.title)

# 4. HTML 생성
html = f"<html><head><meta charset='utf-8'></head><body>"
html += f"<h1>🏠 부동산 뉴스 브리핑 ({datetime.now().strftime('%Y-%m-%d')})</h1>"
html += "<div><strong>매체 바로가기:</strong> " + " | ".join([f'<a href="https://{domain.split("/")[0]}" target="_blank">{name}</a>' for name, domain in SOURCES.items()]) + "</div>"

# KB부동산 시장 요약 반영
html += "<h2>KB부동산 시황</h2>"
html += "<p>전국 아파트 매매가격 0.05% 상승, 38주 연속 상승세 유지. 매수우위지수는 62.9%로 매도자 우위 시장입니다.</p>"

# 카테고리별 출력
for cat, articles in data.items():
    html += f"<h2>[{cat}]</h2><ul>"
    if not articles: html += "<li>최신 관련 기사가 없습니다.</li>"
    for a in articles:
        html += f"<li>[{a['source']}] <a href='{a['link']}' target='_blank'>{a['title']}</a></li>"
    html += "</ul>"

html += "</body></html>"

with open("index.html", "w", encoding="utf-8") as f: f.write(html)
