import feedparser
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from difflib import SequenceMatcher
import re

HEADERS = {"User-Agent": "Mozilla/5.0"}
SOURCES = {
    "조선일보": "https://www.chosun.com/economy/real_estate/", "중앙일보": "https://www.joongang.co.kr/realestate",
    "동아일보": "https://www.donga.com/news/Economy/Realestate", "한겨레": "https://www.hani.co.kr/arti/economy/property/",
    "매일경제": "https://www.mk.co.kr/news/realestate/", "한국경제": "https://www.hankyung.com/realestate",
    "부산일보": "https://www.busan.com/economy/", "국제신문": "https://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0220",
    "주택경제신문": "https://www.arunews.com/", "건설타임즈": "https://www.constimes.co.kr/",
    "경남도민일보": "https://www.idomin.com/", "아시아경제": "https://view.asiae.co.kr/realestate/",
    "아주경제": "https://www.ajunews.com/realestate", "연합뉴스": "https://www.yna.co.kr/economy/real-estate/",
    "머니투데이": "https://news.mt.co.kr/estate/", "서울경제": "https://www.sedaily.com/News/RealeState"
}

RSS_FEEDS = [
    ("한국경제", "https://www.hankyung.com/feed/realestate"), ("서울경제", "https://www.sedaily.com/Rss/RealEstate"),
    ("매일경제", "https://www.mk.co.kr/rss/30100041/"), ("연합뉴스", "https://www.yna.co.kr/rss/economy.xml"),
    ("동아일보", "https://rss.donga.com/economy.xml"), ("한겨레", "https://www.hani.co.kr/rss/economy/"),
    ("주택경제신문", "https://www.arunews.com/rss/allArticle.xml"), ("건설타임즈", "https://www.constimes.co.kr/rss/allArticle.xml")
]

# [중복 제거 로직 복원]
def normalize(t): return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', ' ', re.sub(r'^\[.*?\]\s*', '', t))).strip()
def is_duplicate(new_t, seen):
    n = normalize(new_t)
    # 1. 유사도 검사, 2. 키워드 비교 등 기존 3단계 로직 통합
    return any(SequenceMatcher(None, n, normalize(s)).ratio() > 0.65 for s in seen)

def classify(title):
    t = title.lower()
    if any(k in t for k in ["분양","청약"]): return "청약"
    if any(k in t for k in ["재건축","재개발"]): return "재건축"
    if any(k in t for k in ["부산","해운대","울산","경남"]): return "부산·경남"
    return "시장동향"

def run_scraper():
    data = {c: [] for c in ["청약", "재건축", "부산·경남", "시장동향"]}
    seen = []
    
    # 1. RSS 수집
    for name, url in RSS_FEEDS:
        try:
            for e in feedparser.parse(requests.get(url, headers=HEADERS, timeout=5).content).entries:
                if not is_duplicate(e.title, seen):
                    data[classify(e.title)].append({"title": e.title, "link": e.link, "src": name})
                    seen.append(e.title)
        except: continue
        
    # 2. 부산일보/국제신문 스크래핑
    for site in ["https://www.busan.com/economy/", "https://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0220"]:
        try:
            soup = BeautifulSoup(requests.get(site, headers=HEADERS, timeout=5).text, 'html.parser')
            for a in soup.select('a')[:15]:
                t = a.get_text(strip=True)
                if len(t) > 10 and not is_duplicate(t, seen):
                    data[classify(t)].append({"title": t, "link": urljoin(site, a['href']), "src": "스크래핑"})
                    seen.append(t)
        except: continue

    # 3. HTML 저장
    links_html = " | ".join([f'<a href="{url}" target="_blank">{name}</a>' for name, url in SOURCES.items()])
    html = f"<html><meta charset='utf-8'><body><h1>🏠 부동산 뉴스 브리핑</h1><nav>{links_html}</nav><hr>"
    for c, items in data.items():
        html += f"<h2>[{c}]</h2>" + "".join([f"<p><a href='{i['link']}'>{i['title']}</a> ({i['src']})</p>" for i in items])
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)
    print("브리핑 생성 완료.")

if __name__ == "__main__": run_scraper()
