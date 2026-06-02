import feedparser
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from difflib import SequenceMatcher
import json
import re

# 1. 설정
HEADERS = {"User-Agent": "Mozilla/5.0"}
SOURCES = ["조선일보", "중앙일보", "동아일보", "한겨레", "매일경제", "한국경제", "부산일보", "국제신문", "주택경제신문", "건설타임즈", "경남도민일보", "아시아경제", "아주경제", "연합뉴스", "머니투데이", "서울경제"]
RSS_FEEDS = [
    ("한국경제", "https://www.hankyung.com/feed/realestate"), ("서울경제", "https://www.sedaily.com/Rss/RealEstate"),
    ("매일경제", "https://www.mk.co.kr/rss/30100041/"), ("연합뉴스", "https://www.yna.co.kr/rss/economy.xml"),
    ("동아일보", "https://rss.donga.com/economy.xml"), ("한겨레", "https://www.hani.co.kr/rss/economy/"),
    ("주택경제신문", "https://www.arunews.com/rss/allArticle.xml"), ("건설타임즈", "https://www.constimes.co.kr/rss/allArticle.xml")
]

# 2. 로직: 분류 및 중복제거
def classify(title):
    t = title.lower()
    if any(k in t for k in ["분양","청약"]): return "청약"
    if any(k in t for k in ["재건축","재개발"]): return "재건축"
    if any(k in t for k in ["세금","종부세","취득세"]): return "세제"
    if any(k in t for k in ["정부","대출","정책","금리"]): return "정책"
    return "시장동향"

def is_duplicate(new_t, seen):
    norm = re.sub(r'[^\w\s]', '', new_t)
    return any(SequenceMatcher(None, norm, re.sub(r'[^\w\s]', '', s)).ratio() > 0.6 for s in seen)

# 3. 데이터 수집 및 JSON 저장 (GitHub Actions용)
def run_scraper():
    articles = []
    seen = []
    
    # RSS 수집
    for name, url in RSS_FEEDS:
        try:
            for e in feedparser.parse(requests.get(url, headers=HEADERS, timeout=5).content).entries:
                if not is_duplicate(e.title, seen):
                    articles.append({"category": classify(e.title), "title": e.title, "link": e.link, "source": name})
                    seen.append(e.title)
        except: continue
        
    # 웹 스크래핑
    for site in ["https://www.busan.com/economy/", "https://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0220"]:
        try:
            soup = BeautifulSoup(requests.get(site, headers=HEADERS, timeout=5).text, 'html.parser')
            for a in soup.select('a')[:10]:
                t = a.get_text(strip=True)
                if len(t) > 10 and not is_duplicate(t, seen):
                    articles.append({"category": classify(t), "title": t, "link": urljoin(site, a['href']), "source": "스크래핑"})
                    seen.append(t)
        except: continue

    # JSON 파일로 저장하여 Jekyll이 읽게 함
    with open("_data/news.json", "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)
    print("뉴스 데이터 업데이트 완료.")

if __name__ == "__main__": run_scraper()
