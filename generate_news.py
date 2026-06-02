import feedparser
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from difflib import SequenceMatcher
import re

# ── [1. 설정] 16개 매체 바로가기 & 13개 RSS & 2개 스크래핑 ──────────
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}

SOURCES = {
    "조선일보": "https://www.chosun.com/economy/real_estate/", "중앙일보": "https://www.joongang.co.kr/realestate",
    "동아일보": "https://www.donga.com/news/Economy/Realestate", "한겨레": "https://www.hani.co.kr/arti/economy/property/",
    "매일경제": "https://www.mk.co.kr/news/realestate/", "한국경제": "https://www.hankyung.com/realestate",
    "서울경제": "https://www.sedaily.com/News/RealeState", "아주경제": "https://www.ajunews.com/realestate",
    "연합뉴스": "https://www.yna.co.kr/economy/real-estate/", "머니투데이": "https://news.mt.co.kr/estate/",
    "부산일보": "https://www.busan.com/economy/", "국제신문": "https://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0220",
    "주택경제신문": "https://www.arunews.com/", "건설타임즈": "https://www.constimes.co.kr/",
    "경남도민일보": "https://www.idomin.com/", "아시아경제": "https://view.asiae.co.kr/realestate/"
}

RSS_FEEDS = [
    ("한국경제", "https://www.hankyung.com/feed/realestate"), ("서울경제", "https://www.sedaily.com/Rss/RealEstate"),
    ("매일경제", "https://www.mk.co.kr/rss/30100041/"), ("연합뉴스", "https://www.yna.co.kr/rss/economy.xml"),
    ("동아일보", "https://rss.donga.com/economy.xml"), ("한겨레", "https://www.hani.co.kr/rss/economy/"),
    ("주택경제신문", "https://www.arunews.com/rss/allArticle.xml"), ("건설타임즈", "https://www.constimes.co.kr/rss/allArticle.xml")
]

# ── [2. 로직: 3단계 중복제거] ────────────────────────────────────
def normalize(t): return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', ' ', re.sub(r'^\[.*?\]\s*', '', t))).strip()

def is_duplicate(new_t, seen):
    n = normalize(new_t)
    return any(SequenceMatcher(None, n, normalize(s)).ratio() > 0.6 for s in seen)

def classify(title):
    t = title.lower()
    if any(k in t for k in ["분양","청약"]): return "청약"
    if any(k in t for k in ["재건축","재개발"]): return "재건축"
    if any(k in t for k in ["세금","종부세","취득세"]): return "세제"
    if any(k in t for k in ["정부","대출","정책","금리"]): return "정책"
    if any(k in t for k in ["부산","해운대","울산","경남"]): return "부산·경남"
    return "시장동향"

# ── [3. 수집 통합] ──────────────────────────────────────────────
def get_news():
    data = {c: [] for c in ["청약", "재건축", "세제", "정책", "부산·경남", "시장동향"]}
    seen = []
    
    # RSS 수집
    for name, url in RSS_FEEDS:
        try:
            for e in feedparser.parse(requests.get(url, headers=HEADERS, timeout=5).content).entries:
                if not is_duplicate(e.title, seen):
                    data[classify(e.title)].append({"title": e.title, "link": e.link, "src": name})
                    seen.append(e.title)
        except: continue
        
    # 웹 스크래핑(부산일보/국제신문 통합)
    for url in ["https://www.busan.com/economy/", "https://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0220"]:
        try:
            soup = BeautifulSoup(requests.get(url, headers=HEADERS, timeout=5).text, 'html.parser')
            for a in soup.select('a')[:15]:
                t = a.get_text(strip=True)
                if len(t) > 10 and not is_duplicate(t, seen):
                    data[classify(t)].append({"title": t, "link": urljoin(url, a['href']), "src": "스크래핑"})
                    seen.append(t)
        except: continue
    return data

if __name__ == "__main__":
    d = get_news()
    links = " | ".join([f'<a href="{url}">{name}</a>' for name, url in SOURCES.items()])
    html = f"<h1>🏠 부동산 뉴스 브리핑</h1><nav>{links}</nav><hr>"
    for c, items in d.items():
        html += f"<h2>[{c}]</h2>" + "".join([f"<p><a href='{i['link']}'>{i['title']}</a> ({i['src']})</p>" for i in items]) or "<p>수집된 기사가 없습니다.</p>"
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)
    print("브리핑 생성 완료: index.html")
