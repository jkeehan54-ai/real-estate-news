import feedparser
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from difflib import SequenceMatcher
import re

# ── [1. 설정 및 매체 확대] ──────────────────────────────────────────────────
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}

SOURCES = {
    "조선일보": "https://www.chosun.com/economy/real_estate/", "중앙일보": "https://www.joongang.co.kr/realestate",
    "동아일보": "https://www.donga.com/news/Economy/Realestate", "한겨레": "https://www.hani.co.kr/arti/economy/property/",
    "매일경제": "https://www.mk.co.kr/news/realestate/", "한국경제": "https://www.hankyung.com/realestate",
    "서울경제": "https://www.sedaily.com/News/RealeState", "아주경제": "https://www.ajunews.com/realestate",
    "연합뉴스": "https://www.yna.co.kr/economy/real-estate/", "머니투데이": "https://news.mt.co.kr/estate/",
    "부산일보": "https://www.busan.com/economy/", "국제신문": "https://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0220",
    "주택경제신문": "https://www.arunews.com/", "건설타임즈": "https://www.constimes.co.kr/",
    "경남도민일보": "https://www.idomin.com/news/articleList.html?sc_section_code=S1N8",
    "아시아경제": "https://view.asiae.co.kr/realestate/"
}

RSS_FEEDS = [
    ("한국경제", "https://www.hankyung.com/feed/realestate"), ("서울경제", "https://www.sedaily.com/Rss/RealEstate"),
    ("매일경제", "https://www.mk.co.kr/rss/30100041/"), ("매일경제2", "https://www.mk.co.kr/rss/50100032/"),
    ("연합뉴스", "https://www.yna.co.kr/rss/economy.xml"), ("연합뉴스2", "https://www.yna.co.kr/rss/news.xml"),
    ("동아일보", "https://rss.donga.com/economy.xml"), ("한겨레", "https://www.hani.co.kr/rss/economy/"),
    ("아주경제", "https://www.ajunews.com/rss/economy.xml"), ("아시아경제", "https://www.asiae.co.kr/rss/all.htm"),
    ("주택경제신문", "https://www.arunews.com/rss/allArticle.xml"), ("건설타임즈", "https://www.constimes.co.kr/rss/allArticle.xml"),
    ("경남도민일보", "https://www.idomin.com/rss/allArticle.xml")
]

STOPWORDS = {"은","는","이","가","을","를","의","에","도","와","과","으로","로","에서","까지","부터","이다","합니다","입니다","했다","한다","됩니다","및","등"}
LOC_ENTITIES = {"수도권","서울","강남","부산","경기","인천","대구","광주","대전","울산","세종","해운대","수영","사하","동래","기장","북구","연제","금정","경남"}
ORG_ENTITIES = {"국세청","한국부동산원","법원","국토부","금융위","LH","SH","HUG"}

# ── [2. 검증된 로직] ──────────────────────────────────────────────
def normalize(title):
    title = re.split(r'\s[-|]\s', title)[0].strip()
    title = re.sub(r'^\[.*?\]\s*', '', title)
    title = re.sub(r'[^\w\s]', ' ', title)
    return re.sub(r'\s+', ' ', title).strip()

def keywords(title):
    return {w for w in normalize(title).split() if w not in STOPWORDS and len(w) >= 2}

def extract_entities(title):
    t = re.sub(r'[^\w\s]', ' ', title)
    return {loc for loc in LOC_ENTITIES if loc in t} | {org for org in ORG_ENTITIES if org in t}

def is_duplicate(new_raw, seen_raw):
    norm_new, kw_new, ent_new = normalize(new_raw), keywords(new_raw), extract_entities(new_raw)
    for seen in seen_raw:
        if SequenceMatcher(None, norm_new, normalize(seen)).ratio() >= 0.65: return True
        kw_s = keywords(seen)
        if len(kw_new | kw_s) > 0 and len(kw_new & kw_s) / len(kw_new | kw_s) >= 0.45: return True
        ent_s = extract_entities(seen)
        if ent_new and ent_s and len(ent_new & ent_s) >= 2: return True
    return False

def classify(title):
    t = normalize(title).lower()
    if any(k in t for k in ["분양","청약"]): return "청약"
    if any(k in t for k in ["재건축","재개발"]): return "재건축"
    if any(k in t for k in ["부산","해운대","울산","경남"]): return "부산·경남"
    return "시장동향"

# ── [3. 수집 및 HTML 통합] ──────────────────────────────────────────
def get_news():
    results = {c: [] for c in ["청약", "재건축", "부산·경남", "시장동향"]}
    seen_raw = []
    for name, url in RSS_FEEDS:
        try:
            for e in feedparser.parse(requests.get(url, headers=HEADERS, timeout=5).content).entries:
                if not is_duplicate(e.title, seen_raw):
                    results[classify(e.title)].append({"title": e.title, "link": e.link, "src": name})
                    seen_raw.append(e.title)
        except: continue
    return results

if __name__ == "__main__":
    data = get_news()
    nav = " | ".join([f'<a href="{url}" target="_blank">{name}</a>' for name, url in SOURCES.items()])
    html = f"<h1>🏠 부동산 뉴스 브리핑</h1><nav>{nav}</nav><hr>"
    for c, items in data.items():
        html += f"<h2>[{c}]</h2>" + "".join([f"<p><a href='{i['link']}' target='_blank'>{i['title']}</a> ({i['src']})</p>" for i in items])
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("브리핑 생성 완료: index.html")
