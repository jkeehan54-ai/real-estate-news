"""
부동산 뉴스 브리핑 - 멀티소스 수집 + 3단계 중복 제거
────────────────────────────────────────────────────────
수집 경로:
  A. RSS 피드      - 작동 확인된 16개 매체
  B. 웹 스크래핑   - 부산일보 / 국제신문 (RSS 미제공)
  C. Google News   - 위 경로 보완

설치:
  pip install feedparser requests beautifulsoup4
"""

import feedparser
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin
from difflib import SequenceMatcher
from datetime import datetime, timezone, timedelta
import re
import time

KST = timezone(timedelta(hours=9))

# ── 링크 표시용 매체 목록 ─────────────────────────────────────────────────────
SOURCES = {
    "조선일보":    "https://www.chosun.com/economy/real_estate/",
    "중앙일보":    "https://www.joongang.co.kr/realestate",
    "동아일보":    "https://www.donga.com/news/Economy/Realestate",
    "한겨레":      "https://www.hani.co.kr/arti/economy/property/",
    "매일경제":    "https://www.mk.co.kr/news/realestate/",
    "한국경제":    "https://www.hankyung.com/realestate",
    "서울경제":    "https://www.sedaily.com/News/RealeState",
    "아주경제":    "https://www.ajunews.com/realestate",
    "연합뉴스":    "https://www.yna.co.kr/economy/real-estate/",
    "머니투데이":  "https://news.mt.co.kr/estate/",
    "부산일보":    "https://www.busan.com/economy/",
    "국제신문":    "https://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0220",
    "주택경제신문": "https://www.arunews.com/",
    "건설타임즈":  "https://www.constimes.co.kr/",
}

# ── 공통 헤더 ─────────────────────────────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": "https://www.google.com/",
}

# ── RSS 피드 목록 (테스트로 작동 확인된 것만) ─────────────────────────────────
RSS_FEEDS = [
    # 부동산 전용 피드
    ("한국경제",    "https://www.hankyung.com/feed/realestate",                   True),
    ("서울경제",    "https://www.sedaily.com/Rss/RealEstate",                     True),
    ("주택경제신문", "https://www.arunews.com/rss/allArticle.xml",                True),
    ("건설타임즈",  "https://www.constimes.co.kr/rss/allArticle.xml",             True),
    # 경제 전체 피드 (부동산 키워드 필터링)
    ("매일경제",    "https://www.mk.co.kr/rss/30100041/",                         False),
    ("매일경제2",   "https://www.mk.co.kr/rss/50100032/",                         False),
    ("동아일보",    "https://rss.donga.com/economy.xml",                          False),
    ("한겨레",      "https://www.hani.co.kr/rss/economy/",                        False),
    ("연합뉴스",    "https://www.yna.co.kr/rss/economy.xml",                      False),
    ("연합뉴스2",   "https://www.yna.co.kr/rss/news.xml",                         False),
    ("아주경제",    "https://www.ajunews.com/rss/economy.xml",                    False),
    ("아시아경제",  "https://www.asiae.co.kr/rss/all.htm",                        False),
    ("조선일보",    "https://www.chosun.com/arc/outboundfeeds/rss/?outputType=xml", False),
    ("경남도민일보", "https://www.idomin.com/rss/allArticle.xml",                 False),
]

# ── 부동산 키워드 (전체 피드에서 필터용) ──────────────────────────────────────
RE_ESTATE = re.compile(
    r'아파트|부동산|청약|재건축|재개발|전세|월세|임대차|분양|주택|매매|'
    r'PF|프로젝트파이낸싱|건설사|시행사|LH|SH|HUG|준공|착공|입주|'
    r'종부세|취득세|양도세|재산세|임대료|전셋값|집값|매물|갭투자'
)

# ── 중복 제거 설정 ─────────────────────────────────────────────────────────────
STOPWORDS = {
    "은","는","이","가","을","를","의","에","도","와","과","하고","으로","로",
    "에서","까지","부터","이다","합니다","입니다","했다","한다","됩니다","됐다",
    "및","등","것","안","돼","안돼","반드시","이제","탈출","공화국","않다",
    "이라고","라며","했으며","라고","하며","대해","위해","한다","있다","없다",
    "하다","된다","한","더","또","위","아래","앞","뒤","속","간","전","후",
}
LOC_ENTITIES = {
    "수도권","서울","강남","강북","강동","강서","부산","경기","인천",
    "대구","광주","대전","울산","세종","제주","경남","경북","전남","전북",
    "충남","충북","강원","용산","마포","송파","성동","노원","은평","영등포",
    "해운대","수영","사하","북구","사상","강서구","기장","동래","연제","금정",
}
ORG_ENTITIES = {
    "국세청","당근부동산","한국부동산원","법원","국토부",
    "금융위","금감원","LH","SH","HUG","주택도시보증공사",
}

# ── 날짜 유틸 ─────────────────────────────────────────────────────────────────
def get_pub_dt(entry) -> datetime | None:
    pub = entry.get("published_parsed")
    if not pub:
        return None
    return datetime(*pub[:6], tzinfo=timezone.utc).astimezone(KST)

# ── 정규화 / 키워드 / 엔티티 ──────────────────────────────────────────────────
def normalize(title: str) -> str:
    title = re.split(r'\s[-|]\s', title)[0].strip()
    title = re.sub(r'^\[.*?\]\s*', '', title)
    title = re.sub(r'\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}', '', title)
    title = re.sub(r'[^\w\s]', ' ', title)
    title = re.sub(r'(?<!\w)[一-龥](?!\w)', '', title)
    return re.sub(r'\s+', ' ', title).strip()

def keywords(title: str) -> set:
    return {w for w in normalize(title).split()
            if w not in STOPWORDS and len(w) >= 2}

def extract_entities(title: str) -> set:
    t = re.sub(r'[^\w\s]', ' ', title)
    ents = set()
    for m in re.finditer(
        r'\d+\.?\d*\s*(?:억|만|천|백|건|%|개월|곳|층|평|㎡|채|명|가구|세대)', t
    ):
        ents.add(m.group().strip())
    for loc in LOC_ENTITIES:
        if loc in t: ents.add(loc)
    for org in ORG_ENTITIES:
        if org in t: ents.add(org)
    return ents

# ── 3단계 중복 판별 ───────────────────────────────────────────────────────────
def is_duplicate(new_raw: str, seen_raw: list,
                 sim_thr=0.65, kw_thr=0.45, ent_thr=2) -> bool:
    norm_new = normalize(new_raw)
    kw_new   = keywords(new_raw)
    ent_new  = extract_entities(new_raw)
    for seen in seen_raw:
        norm_s = normalize(seen)
        if SequenceMatcher(None, norm_new, norm_s).ratio() >= sim_thr:
            return True
        kw_s  = keywords(seen)
        union = len(kw_new | kw_s)
        if union and len(kw_new & kw_s) / union >= kw_thr:
            return True
        ent_s = extract_entities(seen)
        if ent_new and ent_s and len(ent_new & ent_s) >= ent_thr:
            return True
    return False

# ── 카테고리 분류 ─────────────────────────────────────────────────────────────
def classify(title: str) -> str:
    t = normalize(title).lower()
    if   any(k in t for k in ["분양","청약"]):
        return "청약"
    elif any(k in t for k in ["재건축","재개발","정비사업","가로주택"]):
        return "재건축"
    elif any(k in t for k in ["세금","종부세","취득세","양도세","재산세","세제"]):
        return "세제"
    elif any(k in t for k in ["정부","대출","금리","정책","규제","완화","dsr","ltv"]):
        return "정책"
    elif any(k in t for k in ["부산","해운대","수영","사하","동래","기장",
                               "북구","사상","연제","금정","경남","울산"]):
        return "부산·경남"
    return "시장동향"

# ── A. RSS 수집 ───────────────────────────────────────────────────────────────
def fetch_rss_all(cutoff: datetime) -> list:
    """(pub_dt, title, link, src) 튜플 리스트"""
    results = []
    for src_name, url, estate_only in RSS_FEEDS:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=8)
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)
            count = 0
            for entry in feed.entries:
                pub_dt = get_pub_dt(entry)
                if pub_dt and pub_dt < cutoff:
                    continue
                title = entry.title.strip()
                # 전체 피드는 부동산 키워드 필터
                if not estate_only and not RE_ESTATE.search(title):
                    continue
                link = entry.link
                # source 필드 직접 주입
                name = (entry.source.title
                        if hasattr(entry, 'source') and hasattr(entry.source, 'title')
                        else src_name)
                results.append((pub_dt, title, link, name))
                count += 1
            print(f"  ✅ RSS [{src_name}] {count}건")
        except Exception as e:
            print(f"  ❌ RSS [{src_name}] {type(e).__name__}: {str(e)[:45]}")
    return results

# ── B. 웹 스크래핑 - 부산일보 ────────────────────────────────────────────────
def scrape_busan_ilbo(cutoff: datetime) -> list:
    """부산일보 부동산 기사 스크래핑"""
    results = []
    urls = [
        "https://www.busan.com/economy/",
        "https://www.busan.com/economy/realestate/",
    ]
    session = requests.Session()
    session.headers.update(HEADERS)

    for url in urls:
        try:
            # 메인 먼저 방문해서 쿠키 획득
            session.get("https://www.busan.com/", timeout=6)
            session.headers["Referer"] = "https://www.busan.com/"
            resp = session.get(url, timeout=8)
            if resp.status_code != 200:
                print(f"  ❌ 부산일보 [{url}] HTTP {resp.status_code}")
                continue

            soup = BeautifulSoup(resp.text, 'html.parser')

            # 부산일보 기사 구조: <ul class="list_news"> 또는 <div class="news_list">
            articles = []
            for selector in [
                'ul.list_news li', 'div.news_list li',
                'div.article_list li', 'ul.news_list li',
                'div.list_area li', 'article',
            ]:
                articles = soup.select(selector)
                if articles:
                    break

            # fallback: h3/h4 안의 a 태그
            if not articles:
                anchors = soup.select('h3 a, h4 a, .title a, .tit a')
                for a in anchors:
                    title = a.get_text(strip=True)
                    href  = a.get('href', '')
                    if not title or not href or len(title) < 10:
                        continue
                    if not RE_ESTATE.search(title):
                        continue
                    link = urljoin("https://www.busan.com", href)
                    results.append((None, title, link, "부산일보"))
                print(f"  {'✅' if results else '⚠️ '} 부산일보 fallback {len(results)}건")
                continue

            for item in articles:
                a = item.find('a')
                if not a:
                    continue
                title = a.get_text(strip=True)
                if not title or len(title) < 10:
                    # 제목 텍스트가 a에 없는 경우 형제 요소에서 탐색
                    title_tag = item.find(['h3','h4','strong','p'], class_=re.compile(r'tit|title|subject'))
                    if title_tag:
                        title = title_tag.get_text(strip=True)
                if not title or len(title) < 10:
                    continue
                if not RE_ESTATE.search(title):
                    continue
                href = a.get('href', '')
                link = urljoin("https://www.busan.com", href)
                results.append((None, title, link, "부산일보"))

            print(f"  {'✅' if results else '⚠️ '} 부산일보 {len(results)}건 ({url})")

        except Exception as e:
            print(f"  ❌ 부산일보 {type(e).__name__}: {str(e)[:50]}")

    # 중복 제거 (같은 링크)
    seen_links = set()
    unique = []
    for item in results:
        if item[2] not in seen_links:
            seen_links.add(item[2])
            unique.append(item)
    return unique

# ── B. 웹 스크래핑 - 국제신문 ────────────────────────────────────────────────
def scrape_kookje(cutoff: datetime) -> list:
    """국제신문 경제/부동산 기사 스크래핑"""
    results = []
    urls = [
        "https://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0220",  # 부동산
        "https://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0200",  # 경제
    ]
    session = requests.Session()
    session.headers.update(HEADERS)

    for url in urls:
        try:
            session.get("https://www.kookje.co.kr/", timeout=6)
            session.headers["Referer"] = "https://www.kookje.co.kr/"
            resp = session.get(url, timeout=8)
            if resp.status_code != 200:
                print(f"  ❌ 국제신문 [{url}] HTTP {resp.status_code}")
                continue

            soup = BeautifulSoup(resp.text, 'html.parser')

            # 국제신문 기사 구조 탐색
            articles = []
            for selector in [
                'ul.news_list li', 'div.news_list li',
                'table.news_table tr', 'ul.list li',
                '.article_list li',
            ]:
                articles = soup.select(selector)
                if articles:
                    break

            # fallback
            if not articles:
                anchors = soup.select('td a, .title a, h4 a, h3 a')
                for a in anchors:
                    title = a.get_text(strip=True)
                    href  = a.get('href', '')
                    if not title or not href or len(title) < 10:
                        continue
                    if not RE_ESTATE.search(title):
                        continue
                    link = urljoin("https://www.kookje.co.kr", href)
                    results.append((None, title, link, "국제신문"))
                print(f"  {'✅' if results else '⚠️ '} 국제신문 fallback {len(results)}건")
                continue

            for item in articles:
                a_tags = item.find_all('a')
                for a in a_tags:
                    title = a.get_text(strip=True)
                    if not title or len(title) < 10:
                        continue
                    if not RE_ESTATE.search(title):
                        continue
                    href = a.get('href', '')
                    if not href:
                        continue
                    link = urljoin("https://www.kookje.co.kr", href)
                    results.append((None, title, link, "국제신문"))
                    break  # 한 항목당 첫 번째 유효 링크만

            print(f"  {'✅' if results else '⚠️ '} 국제신문 {len(results)}건 ({url[-30:]})")

        except Exception as e:
            print(f"  ❌ 국제신문 {type(e).__name__}: {str(e)[:50]}")

    seen_links = set()
    unique = []
    for item in results:
        if item[2] not in seen_links:
            seen_links.add(item[2])
            unique.append(item)
    return unique

# ── C. Google News RSS 보완 ───────────────────────────────────────────────────
def fetch_google_news(cutoff: datetime) -> list:
    results = []
    queries = [
        "부동산 청약 분양",
        "아파트 재건축 재개발",
        "부동산 세금 종부세 취득세",
        "부동산 정책 대출 금리",
        "부동산 시장 매매 전세",
        "부산 부동산 아파트",
        "경남 울산 부동산",
    ]
    for q in queries:
        try:
            url  = f"https://news.google.com/rss/search?q={quote_plus(q)}&hl=ko&gl=KR&ceid=KR:ko"
            resp = requests.get(url, headers=HEADERS, timeout=8)
            feed = feedparser.parse(resp.content)
            count = 0
            for entry in feed.entries:
                pub_dt = get_pub_dt(entry)
                if pub_dt and pub_dt < cutoff:
                    continue
                title = entry.title.strip()
                src   = (entry.source.title
                         if hasattr(entry, 'source') and hasattr(entry.source, 'title')
                         else "뉴스")
                results.append((pub_dt, title, entry.link, src))
                count += 1
            print(f"  ✅ Google [{q}] {count}건")
        except Exception as e:
            print(f"  ❌ Google [{q}] {type(e).__name__}: {str(e)[:40]}")
    return results

# ── 메인 수집 함수 ────────────────────────────────────────────────────────────
def get_clean_news() -> dict:
    categories = ["청약","재건축","세제","정책","부산·경남","시장동향"]
    results    = {c: [] for c in categories}
    seen_raw   = []

    now_kst = datetime.now(KST)
    cutoff  = now_kst.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(hours=6)

    all_entries: list[tuple] = []

    print("\n[A] RSS 피드 수집")
    all_entries.extend(fetch_rss_all(cutoff))

    print("\n[B] 부산일보 스크래핑")
    all_entries.extend(scrape_busan_ilbo(cutoff))

    print("\n[B] 국제신문 스크래핑")
    all_entries.extend(scrape_kookje(cutoff))

    print("\n[C] Google News RSS 보완")
    all_entries.extend(fetch_google_news(cutoff))

    # 최신순 정렬 (날짜 없는 기사는 최상위)
    all_entries.sort(
        key=lambda x: x[0] or datetime.max.replace(tzinfo=KST),
        reverse=True
    )

    total = dropped = 0
    for pub_dt, title, link, src in all_entries:
        total += 1
        if is_duplicate(title, seen_raw):
            dropped += 1
            continue

        cat = classify(title)
        if len(results[cat]) < 12:
            pub_str = pub_dt.strftime("%m/%d %H:%M") if pub_dt else ""
            results[cat].append({
                "title":  normalize(title),
                "link":   link,
                "src":    src,
                "pub_dt": pub_str,
            })
            seen_raw.append(title)

    kept = total - dropped
    print(f"\n[결과] 전체 {total}건 | 중복제거 {dropped}건 | 최종 {kept}건")
    return results

# ── HTML 생성 ─────────────────────────────────────────────────────────────────
def build_html(data: dict) -> str:
    today_str = datetime.now(KST).strftime("%Y년 %m월 %d일")
    html  = f"<h1>🏠 부동산 뉴스 브리핑 ({today_str})</h1>\n"
    html += " | ".join(
        f'<a href="{u}" target="_blank">{n}</a>' for n, u in SOURCES.items()
    )
    html += "\n<h2>오늘의 핵심 브리핑</h2>"
    html += "<p>실시간 부동산 시장 주요 뉴스입니다.</p>"

    icons = {
        "청약":    "🏗",
        "재건축":  "🔨",
        "세제":    "💰",
        "정책":    "📋",
        "부산·경남": "🌊",
        "시장동향": "📈",
    }
    for cat, lst in data.items():
        html += f"<h2>[{icons.get(cat,'')} {cat}]</h2>"
        if lst:
            html += "".join(
                f"<p><a href='{n['link']}' target='_blank'>{n['title']}</a>"
                f" | <b>{n['src']}</b>"
                + (f" <small style='color:#999'>({n['pub_dt']})</small>" if n['pub_dt'] else "")
                + "</p>"
                for n in lst
            )
        else:
            html += "<p>오늘 수집된 기사가 없습니다.</p>"
    return html

# ── 실행 ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    data = get_clean_news()
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(build_html(data))
    total = sum(len(v) for v in data.values())
    print(f"\n[완료] index.html 생성 | 총 {total}건")
    for cat, lst in data.items():
        print(f"  [{cat}] {len(lst)}건" + (" ← 부산일보/국제신문 포함" if cat == "부산·경남" else ""))
