import feedparser
import time
from datetime import datetime

# 1. 키워드 설정
KEYWORDS = ["집값/아파트값", "부동산정책", "부동산규제", "부동산세금", "청약", "분양", "전세", "금리", "대출", "재개발", "재건축", "오피스텔", "공급", "인테리어", "경매", "교통호재", "지역개발"]

# 2. 13개 매체 바로가기 리스트
SOURCES = {
    "조선일보": "https://www.chosun.com/economy/",
    "중앙일보": "https://www.joongang.co.kr/realestate",
    "동아일보": "https://www.donga.com/news/Economy/Realestate",
    "한겨레": "https://www.hani.co.kr/arti/economy/property/",
    "매일경제": "https://www.mk.co.kr/news/realestate/",
    "한국경제": "https://www.hankyung.com/realestate",
    "부산일보": "https://www.busan.com/economy/",
    "국제신문": "https://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0200&vHeadTitle=%B0%E6%C1%A6",
    "네이버부동산": "https://land.naver.com/",
    "한국부동산원": "https://www.reb.or.kr/reb/main.do",
    "KB부동산": "https://kbland.kr/",
    "머니투데이": "https://www.mt.co.kr/estate",
    "연합뉴스": "https://www.yna.co.kr/economy/real-estate"
}

# 3. 13개 매체 대응 직접 수집 피드 (13개 완벽 매칭)
FEEDS = {
    "조선일보": "https://www.chosun.com/arc/outboundfeeds/rss/category/economy/?outputType=xml",
    "중앙일보": "https://rss.joins.com/joins_realestate_list.xml",
    "동아일보": "https://rss.donga.com/economy.xml",
    "한겨레": "https://www.hani.co.kr/rss/economy/",
    "매일경제": "https://www.mk.co.kr/rss/realestate.xml",
    "한국경제": "https://www.hankyung.com/feed/realestate",
    "부산일보": "http://www.busan.com/rss/pc/economy.xml",
    "국제신문": "http://www.kookje.co.kr/news2011/rss/rss_0200.xml",
    "네이버부동산": "https://news.google.com/rss/search?q=site:land.naver.com",
    "한국부동산원": "https://news.google.com/rss/search?q=site:reb.or.kr",
    "KB부동산": "https://news.google.com/rss/search?q=site:kbland.kr",
    "머니투데이": "https://news.mt.co.kr/rss/view.mt?type=estate",
    "연합뉴스": "https://www.yna.co.kr/rss/economy/real-estate.xml"
}

today_str = datetime.now().strftime('%Y-%m-%d')

# 4. HTML 생성
html = f"<html><head><meta charset='utf-8'><style>body{{font-family:sans-serif; padding:15px;}} h2{{color:#0056b3; border-bottom:2px solid #0056b3;}}</style></head><body><h1>오늘의 부동산 뉴스 ({today_str})</h1>"
for name, url in SOURCES.items(): html += f"<a href='{url}' target='_blank' style='margin:5px;'>{name}</a> "
html += "<br><br>"

# 5. 모든 피드 통합 수집
all_entries = []
for name, url in FEEDS.items():
    feed = feedparser.parse(url)
    all_entries.extend(feed.entries)

# 6. 키워드별 분류
for keyword in KEYWORDS:
    html += f"<h2>#{keyword}</h2><ul>"
    found_count = 0
    search_terms = ["집값", "아파트값"] if keyword == "집값/아파트값" else [keyword]
    
    seen = set()
    for entry in all_entries:
        if entry.link in seen: continue
        if any(term in entry.title or (hasattr(entry, 'summary') and term in entry.summary) for term in search_terms):
            html += f"<li><a href='{entry.link}' target='_blank'>{entry.title}</a></li>"
            seen.add(entry.link)
            found_count += 1
        if found_count >= 8: break # 매체당 정보를 더 많이 보기 위해 개수 상향
            
    if found_count == 0: html += "<li>오늘 발행된 관련 뉴스가 없습니다.</li>"
    html += "</ul>"

with open("index.html", "w", encoding="utf-8") as f: f.write(html)
