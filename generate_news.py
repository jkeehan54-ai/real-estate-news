import feedparser
import requests
from bs4 import BeautifulSoup
from difflib import SequenceMatcher
from datetime import datetime, timezone, timedelta
import re

# ── 설정 및 소스 ─────────────────────────────────────────────────────────────
KST = timezone(timedelta(hours=9))
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}

SOURCES = {
    "조선일보": "https://www.chosun.com/economy/real_estate/", "중앙일보": "https://www.joongang.co.kr/realestate",
    "동아일보": "https://www.donga.com/news/Economy/Realestate", "한겨레": "https://www.hani.co.kr/arti/economy/property/",
    "매일경제": "https://www.mk.co.kr/news/realestate/", "한국경제": "https://www.hankyung.com/realestate",
    "부산일보": "https://www.busan.com/economy/", "국제신문": "http://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0200",
    "네이버부동산": "https://land.naver.com/news/", "한국부동산원": "https://www.reb.or.kr/reb/main.do",
    "KB부동산": "https://kbland.kr/today", "머니투데이": "https://news.mt.co.kr/estate/", "연합뉴스": "https://www.yna.co.kr/economy/real-estate/"
}

RSS_SOURCES = [
    ('매일경제_전체', 'https://www.mk.co.kr/rss/30100041/'), ('한국경제_부동산', 'https://www.hankyung.com/feed/realestate'),
    ('서울경제_부동산', 'https://www.sedaily.com/Rss/RealEstate'), ('동아일보_경제', 'https://rss.donga.com/economy.xml'),
    ('연합뉴스_v1', 'https://www.yna.co.kr/rss/economy.xml'), ('연합뉴스_v3', 'https://www.yna.co.kr/rss/news.xml'),
    ('매일경제_부동산v3', 'https://www.mk.co.kr/rss/50100032/'), ('조선일보_v1', 'https://www.chosun.com/arc/outboundfeeds/rss/?outputType=xml'),
    ('조선일보_v2', 'https://www.chosun.com/arc/outboundfeeds/rss/category/economy/?outputType=xml'), ('아시아경제_전체', 'https://www.asiae.co.kr/rss/all.htm'),
    ('아주경제_v1', 'https://www.ajunews.com/rss/economy.xml'), ('주택경제신문', 'https://www.arunews.com/rss/allArticle.xml'),
    ('더피알', 'https://www.the-pr.co.kr/rss/allArticle.xml'), ('건설타임즈', 'https://www.constimes.co.kr/rss/allArticle.xml'),
    ('경남도민일보', 'https://www.idomin.com/rss/allArticle.xml')
]

# ── 정제 및 분류 로직 ──────────────────────────────────────────────────
def normalize(title: str) -> str:
    title = re.split(r'\s[-|]\s', title)[0].strip()
    title = re.sub(r'^\[.*?\]\s*', '', title)
    title = re.sub(r'\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}', '', title)
    title = re.sub(r'[^\w\s]', ' ', title)
    return re.sub(r'\s+', ' ', title).strip()

def is_duplicate(new_title: str, seen: list) -> bool:
    norm_new = normalize(new_title)
    for s in seen:
        if SequenceMatcher(None, norm_new, normalize(s)).ratio() >= 0.65: return True
    return False

def classify(title: str) -> str:
    t = normalize(title).lower()
    if any(k in t for k in ["분양","청약"]): return "청약"
    elif any(k in t for k in ["재건축","재개발"]): return "재건축"
    elif any(k in t for k in ["세금","종부세","취득세","양도세"]): return "세제"
    elif any(k in t for k in ["정부","대출","금리","정책","규제"]): return "정책"
    elif any(k in t for k in ["부산","해운대","사하","동래","강서","기장"]): return "부산"
    return "시장동향"

# ── 수집 및 스크래핑 로직 ─────────────────────────────────────────────────
def get_clean_news():
    data = {"청약":[], "재건축":[], "세제":[], "정책":[], "부산":[], "시장동향":[]}
    seen_raw = []

    # 1. RSS 수집
    for name, url in RSS_SOURCES:
        try:
            feed = feedparser.parse(requests.get(url, headers=HEADERS, timeout=5).content)
            for entry in feed.entries:
                if not is_duplicate(entry.title, seen_raw):
                    cat = classify(entry.title)
                    if len(data[cat]) < 6:
                        data[cat].append({'title': entry.title, 'link': entry.link, 'src': name})
                        seen_raw.append(entry.title)
        except: continue

    # 2. 스크래핑 (부산일보, 국제신문)
    try:
        res = requests.get("https://www.busan.com/list/sec/1010", headers=HEADERS, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        for item in soup.select('.news_list_item a')[:5]:
            title = item.get_text(strip=True)
            if not is_duplicate(title, seen_raw):
                data["부산"].append({'title': title, 'link': "https://www.busan.com" + item['href'], 'src': '부산일보'})
                seen_raw.append(title)
        
        res = requests.get("http://www.kookje.co.kr/news2011/section/0200/", headers=HEADERS, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        for item in soup.select('.news_lst a')[:5]:
            title = item.get_text(strip=True)
            if not is_duplicate(title, seen_raw):
                data["부산"].append({'title': title, 'link': "http://www.kookje.co.kr" + item['href'], 'src': '국제신문'})
                seen_raw.append(title)
    except: pass
    
    return data

def save_html(data):
    today = datetime.now(KST).strftime('%Y년 %m월 %d일')
    nav = " | ".join([f'<a href="{url}" target="_blank">{name}</a>' for name, url in SOURCES.items()])
    html = f"<h1>🏠 부동산 뉴스 브리핑 ({today})</h1><nav style='margin-bottom:20px;'>{nav}</nav>"
    for cat, items in data.items():
        html += f"<h2>[{cat}]</h2>"
        html += "".join([f"<p><a href='{i['link']}' target='_blank'>{normalize(i['title'])}</a> ({i['src']})</p>" for i in items]) if items else "<p>기사 없음</p>"
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__":
    save_html(get_clean_news())
    print("브리핑 생성 완료: RSS와 스크래핑 데이터가 중복 제거되어 분류되었습니다.")
