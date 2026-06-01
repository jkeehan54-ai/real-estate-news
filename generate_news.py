import feedparser
from datetime import datetime

# 1. 13개 매체 및 검색용 도메인 (네이버 부동산 주소 업데이트)
SOURCES_LINKS = {
    "조선일보": ("chosun.com", "https://www.chosun.com/economy/realestate/"),
    "중앙일보": ("joins.com", "https://www.joongang.co.kr/realestate"),
    "동아일보": ("donga.com", "https://www.donga.com/news/Economy/Realestate"),
    "한겨레": ("hani.co.kr", "https://www.hani.co.kr/arti/economy/property/"),
    "매일경제": ("mk.co.kr", "https://www.mk.co.kr/news/realestate/"),
    "한국경제": ("hankyung.com", "https://www.hankyung.com/realestate"),
    "부산일보": ("busan.com", "https://www.busan.com/economy/"),
    "국제신문": ("kookje.co.kr", "https://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0200"),
    "네이버부동산": ("land.naver.com", "https://land.naver.com/news/headline.naver"),
    "한국부동산원": ("reb.or.kr", "https://www.reb.or.kr/reb/main.do"),
    "KB부동산": ("kbland.kr", "https://kbland.kr/"),
    "머니투데이": ("mt.co.kr", "https://news.mt.co.kr/estate/"),
    "연합뉴스": ("yna.co.kr", "https://www.yna.co.kr/economy/real-estate/")
}

def get_category(title):
    t = title.lower()
    if any(k in t for k in ["분양", "청약", "입주", "공급"]): return "청약/분양"
    if any(k in t for k in ["정부", "규제", "세금", "대출", "정책", "금리"]): return "정책/규제"
    if any(k in t for k in ["매매", "전세", "월세", "시세", "가격", "거래"]): return "시장동향"
    if any(k in t for k in ["서울", "부산", "수도권", "재건축", "재개발", "도시"]): return "지역이슈"
    return "기타/산업"

# 2. 뉴스 통합 및 중복 제거 로직
categories = {"청약/분양": [], "정책/규제": [], "시장동향": [], "지역이슈": [], "기타/산업": []}
seen_titles = set() # 중복 체크용 셋

for name, (domain, url) in SOURCES_LINKS.items():
    # 네이버는 별도 RSS가 없으므로 구글 뉴스 검색을 통함
    search_url = f"https://news.google.com/rss/search?q=site:{domain}+부동산+when:7d&hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(search_url)
    
    for entry in feed.entries[:3]:
        if entry.title not in seen_titles: # 중복 제목 필터링
            cat = get_category(entry.title)
            categories[cat].append({'title': entry.title, 'link': entry.link, 'source': name})
            seen_titles.add(entry.title)

# 3. HTML 생성 (생략된 부분은 동일)
# ... [상단 디자인은 이전 코드와 동일하게 유지] ...
