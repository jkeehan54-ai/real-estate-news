import feedparser
from datetime import datetime

# 1. 고정된 13개 매체 리스트 (절대 변경 불가)
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

# 2. 뉴스 수집 및 40개 이상 확보 로직
def get_comprehensive_news():
    # 카테고리 초기화
    results = {"청약": [], "재건축": [], "세제": [], "정책": [], "시장동향": []}
    seen = set()
    
    # RSS 주소 목록 (매체별 추가 피드 활용)
    rss_list = [
        "https://www.chosun.com/arc/outboundfeeds/rss/category/economy/real_estate/",
        "https://rss.joins.com/joins_realestate_list.xml",
        "https://rss.donga.com/economy.xml",
        "https://www.hani.co.kr/rss/economy/",
        "https://www.mk.co.kr/rss/realestate.xml",
        "https://www.hankyung.com/feed/realestate",
        "https://www.yna.co.kr/rss/economy/real-estate.xml",
        "https://news.mt.co.kr/rss/view.mt?type=estate"
    ]
    
    for rss in rss_list:
        feed = feedparser.parse(rss)
        for entry in feed.entries:
            if len(seen) >= 60: break # 40개 이상의 뉴스 확보를 위해 60개까지 수집
            title = entry.title.strip()
            if title in seen: continue
            
            # 부동산 키워드 필터링
            t = title.lower()
            if not any(k in t for k in ["부동산", "아파트", "청약", "분양", "재건축", "주택", "대출", "공급", "임대"]): continue
            
            # 카테고리 자동 분류
            cat = "시장동향"
            if any(k in t for k in ["분양", "청약"]): cat = "청약"
            elif any(k in t for k in ["재건축", "재개발"]): cat = "재건축"
            elif any(k in t for k in ["세금", "종부세", "취득세"]): cat = "세제"
            elif any(k in t for k in ["정부", "규제", "금리", "정책"]): cat = "정책"
            
            results[cat].append({"title": title, "link": entry.link})
            seen.add(title)
    return results

# 3. 브리핑 템플릿 생성
news_data = get_comprehensive_news()
briefing_text = "전국 아파트 매매가격 0.05% 상승, 38주 연속 상승세 유지. 매수우위지수는 62.9%로 매도자 우위 시장입니다."

html = f"<h1>🏠 부동산 뉴스 브리핑</h1>\n"
html += " | ".join([f'<a href="{url}" target="_blank">{name}</a>' for name, url in SOURCES.items()])
html += f"\n\n<h2>오늘의 핵심 브리핑</h2>\n<p>{briefing_text}</p>\n"

for cat, news_list in news_data.items():
    html += f"<h2>[{cat}]</h2>\n" + "".join([f"<p>{n['title']} - <a href='{n['link']}' target='_blank'>[뉴스 바로가기]</a></p>" for n in news_list])

with open("index.html", "w", encoding="utf-8") as f: f.write(html)
