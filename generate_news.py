import feedparser
from datetime import datetime

# [기준 매체 리스트] - 여기를 수정하지 않으면 삭제되지 않습니다.
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
    "KB부동산": ("https://kbland.kr/today", "https://kbland.kr/today"),
    "머니투데이": ("https://news.mt.co.kr/rss/view.mt?type=estate", "https://news.mt.co.kr/estate/"),
    "연합뉴스": ("https://www.yna.co.kr/rss/economy/real-estate.xml", "https://www.yna.co.kr/economy/real-estate/")
}

def get_real_estate_news():
    seen = set()
    # 1. 먼저 카테고리별로 빈 리스트 생성
    result = {cat: [] for cat in ["청약", "재건축", "세제", "정책", "시장동향"]}
    
    # 2. 모든 매체에서 뉴스 수집
    for name, (rss, link) in SOURCES.items():
        feed = feedparser.parse(rss)
        for entry in feed.entries:
            title = entry.title.strip()
            # 중복 제거
            if title in seen: continue
            
            # 부동산 관련성 필터링 (키워드 강조)
            t = title.lower()
            keywords = ["부동산", "아파트", "청약", "분양", "재건축", "재개발", "주택", "전세", "월세", "집값", "대출", "공급", "임대", "건설"]
            if not any(k in t for k in keywords): continue
            
            # 카테고리 분류
            cat = "시장동향"
            if any(k in t for k in ["분양", "청약", "공급"]): cat = "청약"
            elif any(k in t for k in ["재건축", "재개발", "시공사"]): cat = "재건축"
            elif any(k in t for k in ["세금", "종부세", "취득세", "양도세"]): cat = "세제"
            elif any(k in t for k in ["정부", "규제", "대출", "금리", "정책", "법"]): cat = "정책"
            
            result[cat].append({"title": title, "link": entry.link, "source": name})
            seen.add(title)
    return result

# 실행 및 HTML 저장 로직은 유지됩니다.
