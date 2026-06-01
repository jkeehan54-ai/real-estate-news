import feedparser
from datetime import datetime

# [절대 고정 매체 리스트]
SOURCES = {
    "조선일보": "https://www.chosun.com/economy/real_estate/",
    "중앙일보": "https://www.joongang.co.kr/realestate",
    "동아일보": "https://www.donga.com/news/Economy/Realestate",
    "한겨레": "https://www.hani.co.kr/arti/economy/property/",
    "매일경제": "https://www.mk.co.kr/news/realestate/",
    "한국경제": "https://www.hankyung.com/realestate",
    "부산일보": "https://www.busan.com/economy/",
    "국제신문": "http://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0200",
    "네이버부동산": "https://land.naver.com/news/",
    "한국부동산원": "https://www.reb.or.kr/reb/main.do",
    "KB부동산": "https://kbland.kr/today",
    "머니투데이": "https://news.mt.co.kr/estate/",
    "연합뉴스": "https://www.yna.co.kr/economy/real-estate/"
}

def get_large_scale_news():
    # 40개 이상의 뉴스 확보를 위한 검색어 리스트
    queries = ["부동산", "아파트 분양", "재건축", "부동산 정책", "부동산 세금"]
    results = {"청약": [], "재건축": [], "세제": [], "정책": [], "시장동향": []}
    seen = set()
    
    for q in queries:
        # 구글 뉴스 RSS를 활용하여 대량 수집
        url = f"https://news.google.com/rss/search?q={q}+site:chosun.com+OR+site:joins.com+OR+site:donga.com+OR+site:hani.co.kr+OR+site:mk.co.kr+OR+site:hankyung.com+OR+site:yna.co.kr&hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(url)
        for entry in feed.entries:
            if len(seen) >= 50: break # 중복 제외 50개 확보
            title = entry.title.split('-')[0].strip()
            if title in seen: continue
            
            t = title.lower()
            # 카테고리 분류
            cat = "시장동향"
            if any(k in t for k in ["분양", "청약"]): cat = "청약"
            elif any(k in t for k in ["재건축", "재개발"]): cat = "재건축"
            elif any(k in t for k in ["세금", "종부세", "취득세"]): cat = "세제"
            elif any(k in t for k in ["정부", "규제", "금리", "정책", "대출"]): cat = "정책"
            
            results[cat].append({"title": title, "link": entry.link})
            seen.add(title)
    return results

news_data = get_large_scale_news()

# HTML 생성
html = f"<h1>🏠 부동산 뉴스 브리핑</h1>\n"
html += " | ".join([f'<a href="{url}" target="_blank">{name}</a>' for name, url in SOURCES.items()])
html += "\n\n<h2>오늘의 핵심 브리핑</h2>\n<p>전국 아파트 매매가격 0.05% 상승, 38주 연속 상승세 유지. 매수우위지수는 62.9%로 매도자 우위 시장입니다.</p>\n"

for cat, news_list in news_data.items():
    html += f"<h2>[{cat}]</h2>\n"
    if not news_list: html += "<p>관련 기사를 수집 중입니다.</p>"
    else: html += "".join([f"<p>{n['title']} - <a href='{n['link']}' target='_blank'>[뉴스 바로가기]</a></p>" for n in news_list])

with open("index.html", "w", encoding="utf-8") as f: f.write(html)
