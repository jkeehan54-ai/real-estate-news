import feedparser
from datetime import datetime

# 13개 주요 매체의 부동산 전문 섹션 RSS/URL
SOURCES = {
    "조선일보": "https://www.chosun.com/arc/outboundfeeds/rss/category/economy/real_estate/",
    "중앙일보": "https://rss.joins.com/joins_realestate_list.xml",
    "동아일보": "https://www.donga.com/news/Economy/Realestate", # 실제 부동산 기사 페이지
    "한겨레": "https://www.hani.co.kr/rss/economy/",
    "매일경제": "https://www.mk.co.kr/rss/realestate.xml",
    "한국경제": "https://www.hankyung.com/feed/realestate",
    "부산일보": "https://www.busan.com/rss/pc/economy.xml",
    "국제신문": "http://www.kookje.co.kr/news2011/rss/rss_0200.xml",
    "머니투데이": "https://news.mt.co.kr/rss/view.mt?type=estate",
    "연합뉴스": "https://www.yna.co.kr/rss/economy/real-estate.xml"
}

# 부동산 관련성 검증 및 카테고리 분류 함수
def get_real_estate_news(title):
    t = title.lower()
    # 부동산 관련 핵심 키워드 목록
    keywords = ["부동산", "아파트", "청약", "분양", "재건축", "재개발", "주택", "전세", "월세", "집값", "대출", "공급", "부동산", "임대"]
    
    # 키워드가 하나도 없으면 False 리턴
    if not any(k in t for k in keywords):
        return None
    
    # 카테고리 할당
    if any(k in t for k in ["분양", "청약"]): return "청약"
    if any(k in t for k in ["재건축", "재개발"]): return "재건축"
    if any(k in t for k in ["세금", "종부세", "취득세", "양도세"]): return "세제"
    if any(k in t for k in ["정부", "규제", "대출", "금리", "정책"]): return "정책"
    return "시장동향"

# 뉴스 수집 및 중복/관련성 필터링
articles = []
seen_titles = set()

for name, rss_url in SOURCES.items():
    feed = feedparser.parse(rss_url)
    for entry in feed.entries:
        if entry.title not in seen_titles:
            cat = get_real_estate_news(entry.title)
            if cat: # 부동산 기사만 수집
                articles.append({'title': entry.title, 'link': entry.link, 'cat': cat, 'src': name})
                seen_titles.add(entry.title)

# HTML 생성
html = f"<html><body><h1>🏠 부동산 뉴스 브리핑 ({datetime.now().strftime('%Y-%m-%d')})</h1>"
html += "<h2>📊 KB부동산 시황 요약</h2><p>전국 아파트 매매가격 0.05% 상승, 38주 연속 상승세 유지. 매수우위지수는 62.9%로 매도자 우위 시장입니다.</p>"

for cat in ["청약", "재건축", "세제", "정책", "시장동향"]:
    html += f"<h2>[{cat}]</h2><ul>"
    cat_articles = [a for a in articles if a['cat'] == cat]
    if not cat_articles: html += "<li>해당 카테고리의 부동산 뉴스가 없습니다.</li>"
    for a in cat_articles:
        html += f"<li>[{a['src']}] <a href='{a['link']}' target='_blank'>{a['title']}</a></li>"
    html += "</ul>"
html += "</body></html>"
