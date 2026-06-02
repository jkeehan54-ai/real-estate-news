import feedparser
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from difflib import SequenceMatcher
import re

# 1. 설정
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}

SOURCES = {
    "조선일보": "https://www.chosun.com/economy/real_estate/", "중앙일보": "https://www.joongang.co.kr/realestate",
    "동아일보": "https://www.donga.com/news/Economy/Realestate", "한겨레": "https://www.hani.co.kr/arti/economy/property/",
    "매일경제": "https://www.mk.co.kr/news/realestate/", "한국경제": "https://www.hankyung.com/realestate",
    "부산일보": "https://www.busan.com/economy/", "국제신문": "https://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0220"
}

RSS_FEEDS = [
    ("한국경제", "https://www.hankyung.com/feed/realestate"), ("매일경제", "https://www.mk.co.kr/rss/30100041/"),
    ("연합뉴스", "https://www.yna.co.kr/rss/economy.xml"), ("서울경제", "https://www.sedaily.com/Rss/RealEstate")
]

# 2. 분류 및 중복제거 (유연한 키워드 검사)
def classify(title):
    t = title.lower()
    if any(k in t for k in ["분양","청약","입주"]): return "청약"
    if any(k in t for k in ["재건축","재개발","정비"]): return "재건축"
    if any(k in t for k in ["세금","종부세","취득세","세제"]): return "세제"
    if any(k in t for k in ["정부","대출","정책","금리","규제","부동산"]): return "정책"
    if any(k in t for k in ["부산","해운대","울산","경남"]): return "부산·경남"
    return "시장동향"

def is_duplicate(new_t, seen):
    norm = re.sub(r'[^\w\s]', '', new_t)
    return any(SequenceMatcher(None, norm, re.sub(r'[^\w\s]', '', s)).ratio() > 0.5 for s in seen)

# 3. 데이터 수집
def run_scraper():
    data = {c: [] for c in ["청약", "재건축", "세제", "정책", "부산·경남", "시장동향"]}
    seen = []
    
    # RSS 수집
    for name, url in RSS_FEEDS:
        try:
            feed = feedparser.parse(requests.get(url, headers=HEADERS, timeout=10).content)
            for e in feed.entries:
                if not is_duplicate(e.title, seen):
                    data[classify(e.title)].append({"title": e.title, "link": e.link, "src": name})
                    seen.append(e.title)
        except: continue
        
    # 웹 스크래핑 보강 (실제 뉴스 리스트 클래스 탐색)
    try:
        res = requests.get("https://www.busan.com/economy/", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        # 기사 제목이 포함된 태그들을 타겟팅
        for a in soup.select('a.news_ttl, div.news_list_item a'):
            t = a.get_text(strip=True)
            if len(t) > 10 and not is_duplicate(t, seen):
                cat = classify(t)
                data[cat].append({"title": t, "link": urljoin("https://www.busan.com", a['href']), "src": "부산일보"})
                seen.append(t)
    except: pass

    # HTML 생성
    nav = " | ".join([f'<a href="{url}" target="_blank">{name}</a>' for name, url in SOURCES.items()])
    html = f"<html><head><meta charset='utf-8'></head><body><h1>🏠 부동산 뉴스 브리핑</h1><nav>{nav}</nav><hr>"
    for c, items in data.items():
        html += f"<h2>[{c}]</h2>"
        if items:
            for i in items:
                html += f"<p><a href='{i['link']}' target='_blank'>{i['title']}</a> ({i['src']})</p>"
        else:
            html += "<p>오늘 수집된 기사가 없습니다.</p>"
    html += "</body></html>"
    
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)
    print("브리핑 생성 완료. index.html을 다시 확인하세요.")

if __name__ == "__main__":
    run_scraper()
