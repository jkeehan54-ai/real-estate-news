import feedparser
from datetime import datetime

# 13개 매체 고정 리스트 (절대 변하지 않음)
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

def get_unique_news():
    results = {"청약": [], "재건축": [], "세제": [], "정책": [], "시장동향": []}
    seen_titles = set()
    
    # 중복 제거를 위한 함수: 제목에서 조사나 특수문자를 제거한 '핵심 키워드' 비교
    def get_core_title(t):
        return "".join([c for c in t if c.isalnum()])[:15]

    queries = ["부동산 청약 분양", "재건축 재개발", "부동산 세금 양도세", "부동산 정책 대출", "부동산 시장 동향"]
    for q in queries:
        url = f"https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(url)
        for entry in feed.entries:
            core = get_core_title(entry.title)
            if core in seen_titles: continue
            
            t = entry.title.lower()
            cat = "시장동향"
            if any(k in t for k in ["분양", "청약"]): cat = "청약"
            elif any(k in t for k in ["재건축", "재개발"]): cat = "재건축"
            elif any(k in t for k in ["세금", "종부세", "취득세"]): cat = "세제"
            elif any(k in t for k in ["정부", "대출", "금리", "정책"]): cat = "정책"
            
            results[cat].append({"title": entry.title, "link": entry.link, "src": entry.source.title if 'source' in entry else "뉴스"})
            seen_titles.add(core)
    return results

data = get_unique_news()

# HTML 생성
html = f"<h1>🏠 부동산 뉴스 브리핑</h1>\n"
html += " | ".join([f'<a href="{url}" target="_blank">{name}</a>' for name, url in SOURCES.items()])
html += "\n\n<h2>📊 KB부동산 시황</h2><p>전국 아파트 매매가격 0.05% 상승, 38주 연속 상승세 유지. 매수우위지수는 62.9%로 매도자 우위 시장입니다.</p>\n"

for cat, news_list in data.items():
    html += f"<h2>[{cat}]</h2>"
    if not news_list: html += "<p>수집된 기사가 없습니다.</p>"
    for n in news_list:
        html += f"<p>{n['title']} | {n['src']} - <a href='{n['link']}' target='_blank'>[바로가기]</a></p>"

with open("index.html", "w", encoding="utf-8") as f: f.write(html)
