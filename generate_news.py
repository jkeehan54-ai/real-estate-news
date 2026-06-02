import feedparser
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from difflib import SequenceMatcher
import re

# ── [1. 설정] ──────────────────────────────────────────────────
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

# ── [2. 로직: 중복제거/분류/스크래핑] ──────────────────────────
def normalize(title): return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', ' ', re.sub(r'^\[.*?\]\s*', '', title))).strip()

def is_duplicate(new_title, seen):
    norm = normalize(new_title)
    return any(SequenceMatcher(None, norm, normalize(s)).ratio() > 0.6 for s in seen)

def classify(title):
    t = title.lower()
    if any(k in t for k in ["분양","청약"]): return "청약"
    if any(k in t for k in ["재건축","재개발","정비"]): return "재건축"
    if any(k in t for k in ["세금","종부세","취득세","세제"]): return "세제"
    if any(k in t for k in ["정부","대출","정책","금리","규제"]): return "정책"
    if any(k in t for k in ["부산","해운대","울산","경남","국제신문"]): return "부산·경남"
    return "시장동향"

def get_news():
    results = {c: [] for c in ["청약", "재건축", "세제", "정책", "부산·경남", "시장동향"]}
    seen = []
    
    # RSS 수집
    for name, url in RSS_FEEDS:
        try:
            for e in feedparser.parse(requests.get(url, headers=HEADERS, timeout=5).content).entries:
                if not is_duplicate(e.title, seen):
                    results[classify(e.title)].append({"title": e.title, "link": e.link, "src": name})
                    seen.append(e.title)
        except: continue

    # 부산일보 스크래핑 강제 실행
    try:
        soup = BeautifulSoup(requests.get("https://www.busan.com/economy/", headers=HEADERS).text, 'html.parser')
        for a in soup.select('a')[:20]:
            title = a.get_text(strip=True)
            if len(title) > 10 and not is_duplicate(title, seen):
                results[classify(title)].append({"title": title, "link": urljoin("https://www.busan.com", a['href']), "src": "부산일보"})
                seen.append(title)
    except: pass
    return results

# ── [3. 출력] ──────────────────────────────────────────────────
if __name__ == "__main__":
    data = get_news()
    links = " | ".join([f'<a href="{url}" target="_blank">{name}</a>' for name, url in SOURCES.items()])
    html = f"<h1>🏠 부동산 뉴스 브리핑</h1><nav>{links}</nav><hr>"
    for c, items in data.items():
        html += f"<h2>[{c}]</h2>" + "".join([f"<p><a href='{i['link']}' target='_blank'>{i['title']}</a> ({i['src']})</p>" for i in items])
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)
    print("브리핑 생성 완료. index.html을 확인하세요.")
