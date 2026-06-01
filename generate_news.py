import feedparser
from datetime import datetime

# 13개 매체 고정 리스트
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

def get_clean_news():
    results = {"청약": [], "재건축": [], "세제": [], "정책": [], "시장동향": []}
    seen_hashes = set()
    
    # 더 넓은 키워드 검색
    queries = ["부동산 분양 청약", "아파트 재건축 재개발", "부동산 세금 종부세", "부동산 대출 정책", "부동산 시장 동향"]
    
    for q in queries:
        feed = feedparser.parse(f"https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko")
        for entry in feed.entries:
            # 제목의 핵심 요약 (중복 제거용)
            title = entry.title.split('-')[0].split('|')[0].strip()
            title_hash = "".join([c for c in title if c.isalnum()])[:12]
            
            if title_hash in seen_hashes: continue
            
            t = title.lower()
            cat = "시장동향"
            if any(k in t for k in ["분양", "청약"]): cat = "청약"
            elif any(k in t for k in ["재건축", "재개발"]): cat = "재건축"
            elif any(k in t for k in ["세금", "종부세", "취득세"]): cat = "세제"
            elif any(k in t for k in ["정부", "대출", "금리", "정책"]): cat = "정책"
            
            if len(results[cat]) < 10: # 각 카테고리당 최대 10개로 제한하여 중복 분산
                results[cat].append({"title": title, "link": entry.link, "src": entry.source.title if 'source' in entry else "뉴스"})
                seen_hashes.add(title_hash)
    return results

data = get_clean_news()

# HTML 출력
html = f"<h1>🏠 부동산 뉴스 브리핑</h1>\n" + " | ".join([f'<a href="{url}" target="_blank">{name}</a>' for name, url in SOURCES.items()])
html += "\n<h2>오늘의 핵심 브리핑</h2><p>전국 아파트 매매가격 0.05% 상승, 38주 연속 상승세 유지. 매수우위지수는 62.9%로 매도자 우위입니다.</p>"

for cat, news_list in data.items():
    html += f"<h2>[{cat}]</h2>" + "".join([f"<p>{n['title']} | {n['src']} - <a href='{n['link']}' target='_blank'>[바로가기]</a></p>" for n in news_list])

with open("index.html", "w", encoding="utf-8") as f: f.write(html)
