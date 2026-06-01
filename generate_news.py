import feedparser
from datetime import datetime

# 1. 13개 매체 주소 (RSS 우선 사용)
SOURCES = {
    "조선일보": ("https://www.chosun.com/arc/outboundfeeds/rss/category/economy/real_estate/", "https://www.chosun.com/economy/real_estate/"),
    "중앙일보": ("https://rss.joins.com/joins_realestate_list.xml", "https://www.joongang.co.kr/realestate"),
    "동아일보": ("https://rss.donga.com/economy.xml", "https://www.donga.com/news/Economy/Realestate"),
    "한겨레": ("https://www.hani.co.kr/rss/economy/", "https://www.hani.co.kr/arti/economy/property/"),
    "매일경제": ("https://www.mk.co.kr/rss/realestate.xml", "https://www.mk.co.kr/news/realestate/"),
    "한국경제": ("https://www.hankyung.com/feed/realestate", "https://www.hankyung.com/realestate"),
    "부산일보": ("http://www.busan.com/rss/pc/economy.xml", "https://www.busan.com/economy/"),
    "국제신문": ("http://www.kookje.co.kr/news2011/rss/rss_0200.xml", "https://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0200"),
    "네이버부동산": ("https://news.naver.com/main/list.naver?mode=LS2D&mid=shm&sid1=101&sid2=260", "https://land.naver.com/news/"),
    "한국부동산원": ("https://www.reb.or.kr/reb/main.do", "https://www.reb.or.kr/reb/main.do"),
    "KB부동산": ("https://kbland.kr/today?xy=37.5194908,126.9249743,19", "https://kbland.kr/today"),
    "머니투데이": ("https://news.mt.co.kr/estate/", "https://news.mt.co.kr/estate/"),
    "연합뉴스": ("https://www.yna.co.kr/rss/economy/real-estate.xml", "https://www.yna.co.kr/economy/real-estate/")
}

# 2. 강력한 부동산 필터링 및 카테고리 분류
def is_real_estate(title):
    keywords = ["부동산", "아파트", "청약", "분양", "재건축", "재개발", "주택", "전세", "월세", "집값", "대출", "공급", "상가", "빌라"]
    return any(k in title for k in keywords)

def get_category(title):
    t = title.lower()
    if any(k in t for k in ["분양", "청약"]): return "청약"
    if any(k in t for k in ["재건축", "재개발"]): return "재건축"
    if any(k in t for k in ["세금", "종부세", "취득세"]): return "세제"
    if any(k in t for k in ["정부", "규제", "대출", "금리", "정책"]): return "정책"
    return "시장동향"

# 3. 뉴스 수집 (중복 제거 및 관련성 필터링)
articles = []
seen_titles = set()

for name, (rss, link) in SOURCES.items():
    feed = feedparser.parse(rss)
    for entry in feed.entries: # 매체당 수집량 최대화
        if entry.title not in seen_titles and is_real_estate(entry.title):
            articles.append({
                "title": entry.title, "source": name, 
                "category": get_category(entry.title), "link": entry.link
            })
            seen_titles.add(entry.title)

# 4. HTML 생성
html = f"<html><head><meta charset='utf-8'></head><body>"
html += f"<h1>🏠 부동산 뉴스 브리핑 ({datetime.now().strftime('%Y-%m-%d')})</h1>"
html += "<div><strong>매체 바로가기:</strong> " + " | ".join([f'<a href="{link}" target="_blank">{name}</a>' for name, (rss, link) in SOURCES.items()]) + "</div>"

# KB부동산 시황 요약 (고정)
html += "<h2>오늘의 핵심 브리핑 (KB부동산 시황)</h2>"
html += "<p>전국 아파트 매매가격 0.05% 상승, 38주 연속 상승세 유지 (매수우위지수 62.9% - 매도자 우위)</p>"

html += "<h2>TOP 이슈</h2>"
html += "".join([f'<p><a href="{a["link"]}" target="_blank">{a["title"]}</a> - {a["source"]}</p>' for a in articles[:5]])

html += "<h2>전체 뉴스</h2>"
html += "".join([f'<p>[{a["category"]}] <a href="{a["link"]}" target="_blank">{a["title"]}</a> ({a["source"]})</p>' for a in articles])

html += "</body></html>"

with open("index.html", "w", encoding="utf-8") as f: f.write(html)
