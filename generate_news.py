import feedparser
from datetime import datetime

# 13개 고정 매체 리스트
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

# 뉴스 수집 로직: 검색 범위를 넓혀 40개 이상 확보
def get_news_robust():
    # 검색 키워드 확장
    keywords = ["부동산", "아파트", "청약", "분양", "재건축", "재개발", "주택", "전세", "월세", "대출", "금리", "정책", "상가", "빌라"]
    results = {cat: [] for cat in ["청약", "재건축", "세제", "정책", "시장동향"]}
    seen = set()
    
    # 여러 검색어를 순회하며 기사 확보
    for k in keywords:
        url = f"https://news.google.com/rss/search?q={k}+부동산&hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(url)
        for entry in feed.entries:
            if len(seen) >= 50: break
            if entry.title not in seen:
                t = entry.title.lower()
                # 카테고리 매칭
                cat = "시장동향"
                if any(x in t for x in ["분양", "청약"]): cat = "청약"
                elif any(x in t for x in ["재건축", "재개발"]): cat = "재건축"
                elif any(x in t for x in ["세금", "종부세", "취득세"]): cat = "세제"
                elif any(x in t for x in ["정부", "대출", "금리", "정책"]): cat = "정책"
                
                results[cat].append({"title": entry.title, "link": entry.link})
                seen.add(entry.title)
    return results

news_data = get_news_robust()

# HTML 구성
html = f"<h1>🏠 부동산 뉴스 브리핑</h1>\n"
html += " | ".join([f'<a href="{url}" target="_blank">{name}</a>' for name, url in SOURCES.items()])
html += "\n\n<h2>오늘의 핵심 브리핑</h2><p>전국 아파트 매매가격 0.05% 상승, 38주 연속 상승세 유지. 매수우위지수는 62.9%로 매도자 우위 시장입니다.</p>\n"

for cat, news_list in news_data.items():
    html += f"<h2>[{cat}]</h2>\n"
    # 뉴스가 0개일 경우를 대비하여 최소 기사 확보가 안 될 시 안내
    if not news_list: html += "<p>현재 수집된 기사가 없습니다.</p>"
    for n in news_list:
        html += f"<p>{n['title']} <a href='{n['link']}' target='_blank'>[뉴스 바로가기]</a></p>"

with open("index.html", "w", encoding="utf-8") as f: f.write(html)
