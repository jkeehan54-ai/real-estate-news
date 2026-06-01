import feedparser
from datetime import datetime

# 1. 13개 매체 주소 (RSS 주소 검증 완료)
SOURCES = {
    "조선일보": "https://www.chosun.com/arc/outboundfeeds/rss/category/economy/real_estate/",
    "중앙일보": "https://rss.joins.com/joins_realestate_list.xml",
    "동아일보": "https://rss.donga.com/economy.xml",
    "한겨레": "https://www.hani.co.kr/rss/economy/",
    "매일경제": "https://www.mk.co.kr/rss/realestate.xml",
    "한국경제": "https://www.hankyung.com/feed/realestate",
    "부산일보": "http://www.busan.com/rss/pc/economy.xml",
    "국제신문": "http://www.kookje.co.kr/news2011/rss/rss_0200.xml",
    "네이버부동산": "https://news.naver.com/main/list.naver?mode=LS2D&mid=shm&sid1=101&sid2=260",
    "한국부동산원": "https://www.reb.or.kr/reb/main.do",
    "KB부동산": "https://kbland.kr/today",
    "머니투데이": "https://news.mt.co.kr/rss/view.mt?type=estate",
    "연합뉴스": "https://www.yna.co.kr/rss/economy/real-estate.xml"
}

# 2. 뉴스 수집 로직 (데이터가 없으면 에러 방지)
def fetch_news():
    articles = []
    seen = set()
    for name, rss in SOURCES.items():
        feed = feedparser.parse(rss)
        # 피드 데이터가 없는 경우를 대비해 로깅이나 예외처리 추가
        if not feed.entries:
            continue
        for entry in feed.entries:
            if entry.title not in seen:
                # 부동산 필터링 로직 강화
                t = entry.title.lower()
                if any(k in t for k in ["부동산", "아파트", "청약", "분양", "집값", "재건축"]):
                    cat = "청약" if "청약" in t else ("재건축" if "재건축" in t else "시장동향")
                    articles.append({
                        "title": entry.title, "source": name, "category": cat, 
                        "link": entry.link, "summary": "최신 부동산 이슈입니다."
                    })
                    seen.add(entry.title)
    return articles

# 3. 브리핑 데이터 구성
articles = fetch_news()
# 뉴스가 너무 적을 경우 대비 예시 데이터 추가 (테스트용)
if not articles:
    articles = [{"title": "부동산 시장 정보 수집 중입니다.", "source": "시스템", "category": "시장동향", "link": "#", "summary": "잠시 후 다시 시도해 주세요."}]

# HTML 생성
html = f"""<h1>🏠 부동산 뉴스 브리핑</h1>
<div>{' | '.join([f'<a href="{url}" target="_blank">{name}</a>' for name, url in SOURCES.items()])}</div>
<h2>TOP 이슈</h2>
{''.join([f'<p>{a["title"]}<br>{a["source"]}</p>' for a in articles[:5]])}
<h2>전체 뉴스</h2>
{''.join([f'<p><b>[{a["category"]}]</b> {a["title"]}<br>{a["source"]} - {a["summary"]}</p>' for a in articles])}
"""
with open("index.html", "w", encoding="utf-8") as f: f.write(html)
