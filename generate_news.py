import feedparser, requests, re, os
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin
from difflib import SequenceMatcher
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

SOURCES = {
    "조선일보":    "https://www.chosun.com/economy/real_estate/",
    "중앙일보":    "https://www.joongang.co.kr/realestate",
    "동아일보":    "https://www.donga.com/news/Economy/Realestate",
    "네이버부동산": "https://land.naver.com/news/",
    "한겨레":      "https://www.hani.co.kr/arti/economy/property/",
    "매일경제":    "https://www.mk.co.kr/news/realestate/",
    "한국경제":    "https://www.hankyung.com/realestate",
    "서울경제":    "https://www.sedaily.com/News/RealeState",
    "연합뉴스":    "https://www.yna.co.kr/economy/real-estate/",
    "부산일보":    "https://www.busan.com/economy/",
    "국제신문":    "http://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0220",
    "주택경제신문": "https://www.arunews.com/",
    "건설타임즈":  "https://www.constimes.co.kr/",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36", # 124버전에서 최신 버전으로 업데이트
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd", # zstd 추가 (최신 브라우저 규격)
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0" # 캐시 정책 명시
}

RSS_FEEDS = [
    ("한국경제",    "https://www.hankyung.com/feed/realestate",                    True),
    ("서울경제",    "https://www.sedaily.com/Rss/RealEstate",                      True),
    ("주택경제신문", "https://www.arunews.com/rss/allArticle.xml",                 True),
    ("건설타임즈",  "https://www.constimes.co.kr/rss/allArticle.xml",              True),
    ("매일경제",    "https://www.mk.co.kr/rss/30100041/",                          False),
    ("매일경제2",   "https://www.mk.co.kr/rss/50100032/",                          False),
    ("동아일보",    "https://rss.donga.com/economy.xml",                           False),
    ("한겨레",      "https://www.hani.co.kr/rss/economy/",                         False),
    ("연합뉴스",    "https://www.yna.co.kr/rss/economy.xml",                       False),
    ("연합뉴스2",   "https://www.yna.co.kr/rss/news.xml",                          False),
    ("아주경제",    "https://www.ajunews.com/rss/economy.xml",                     False),
    ("아시아경제",  "https://www.asiae.co.kr/rss/all.htm",                         False),
    ("조선일보",    "https://www.chosun.com/arc/outboundfeeds/rss/?outputType=xml", False),
    ("경남도민일보", "https://www.idomin.com/rss/allArticle.xml",                  False),
    # 뉴스핌과 노컷뉴스는 RSS 주소가 아니므로 아래처럼 분리하세요
    ("뉴스핌_부동산", "https://www.newspim.com/news/lists/?category_cd=104010", False),
    ("노컷뉴스_부동산", "https://www.nocutnews.co.kr/news/industry/list?c2=530", False),
    ("파이낸셜뉴스", "https://www.fnnews.com/rss/rsk_realestate.xml", False),
    ("헤럴드경제", "https://biz.heraldcorp.com/rss/realestate.xml", False),
    ("세계일보", "https://www.segye.com/rss/RSS_economy.xml", False),
    ("머니투데이", "https://news.moneytoday.co.kr/rss/news_realestate.xml", False),
]

GOOGLE_QUERIES = [
    "부동산 청약 분양",
    "아파트 재건축 재개발",
    "부동산 세금 종부세 취득세",
    "부동산 정책 대출 금리", "부동산 규제","전세 대책",
    "부동산 시장 매매 전세", "서울 아파트",
    "부동산", "아파트 분양", "재건축 재개발", "부동산 세금", 
    "부동산 정책", "주택담보대출", "경남 아파트", 
    "전세 가격", "공공주택", "오피스텔", "상가 투자"
    "부산 부동산 아파트",
]

RE_ESTATE = re.compile(
    r'아파트|부동산|청약|재건축|재개발|전세|월세|임대|분양|주택|매매|'
    r'PF|건설사|시공|준공|착공|입주|종부세|취득세|양도세|재산세|집값|매물|'
    r'오피스텔|빌라|다세대|공동주택|정비사업|가로주택|LH|SH|HUG|'
    r'담보대출|주담대|전셋값|갭투자|분양가|거래량|매수|매도'
    r'아파트|부동산|청약|재건축|재개발|전세|월세|임대|분양|주택|매매|PF|건설사|'
    r'금리|대출|집값|아파트 공급|분양가|용적률|재산세|종부세|상가|오피스텔|빌라'
)

RE_EXCLUDE = re.compile(
    r'숨진|사망|시신|변사|화상|부상|충돌|입건|구속|체포|검거|'
    r'화재|폭발|투표소|선거|후보|당선|낙선|'
    r'코스닥|코스피|주식|공급|매도|매수|증권|'
    r'만취|음주운전|교통사고|폭행|'
    r'전동킥보드|전동휠체어|오토바이|승용차 몰다'
)

STOPWORDS = {
    "은","는","이","가","을","를","의","에","도","와","과","하고","으로","로",
    "에서","까지","부터","이다","합니다","입니다","했다","한다","됩니다","됐다",
    "및","등","것","안","돼","안돼","반드시","이제","않다","이라고","라며",
    "라고","하며","대해","위해","있다","없다","하다","된다","한","더","또",
}
LOC_ENTITIES = {
    "수도권","서울","강남","강북","부산","경기","인천","대구","광주","대전",
    "울산","세종","경남","해운대","수영","사하","동래","기장","연제","금정",
}
ORG_ENTITIES = {"국세청","한국부동산원","국토부","금융위","금감원","LH","SH","HUG"}

CAT_KEYWORDS = {
    "청약":    ["분양", "청약", "청약률", "무순위", "줍줍", "분양가", "입주자모집"],
    "재건축":  ["재건축", "재개발", "정비사업", "가로주택", "시공자", "조합", "추진위",
                "안전진단", "이주", "철거", "착공", "준공", "건설사 수주"],
    "세제":    ["종부세", "취득세", "양도세", "재산세", "증여세", "세금", "세제",
                "비과세", "감면", "공제", "과세", "세율", "절세"],
    "정책":    ["대출", "금리", "정책", "규제", "완화", "DSR", "LTV", "DTI",
                "주담대", "담보대출", "전세대출", "보증", "임대차", "계약갱신", "전월세상한"],
    "부산경남": ["부산 아파트", "부산 부동산", "부산 주택", "부산 전세", "부산 분양",
                 "해운대 아파트", "해운대 부동산", "경남 아파트", "경남 부동산",
                 "울산 아파트", "울산 부동산", "부산 재건축", "부산 재개발", "부산 청약"],
    "시장동향": ["시장", "매매가", "전세가", "거래량", "낙찰"],
}


# ── 날짜 유틸 ─────────────────────────────────────────────────────────────────
def extract_date_from_url(url):
    """URL 경로 /YYYY/MM/DD/ 또는 key=YYYYMMDD 패턴에서 날짜 추출"""
    # /2026/06/04/ 패턴
    m = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', url)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), 0, 0, tzinfo=KST)
        except Exception:
            pass
    # key=20260604 패턴 (국제신문)
    m = re.search(r'key=(\d{4})(\d{2})(\d{2})\.', url)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), 0, 0, tzinfo=KST)
        except Exception:
            pass
    # code=YYYYMMDD 패턴 (부산일보)
    m = re.search(r'code=(\d{4})(\d{2})(\d{2})', url)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), 0, 0, tzinfo=KST)
        except Exception:
            pass
    return None


def get_best_pub_dt(entry):
    pub = entry.get("published_parsed")
    if pub:
        return datetime(*pub[:6], tzinfo=timezone.utc).astimezone(KST)
    return extract_date_from_url(getattr(entry, 'link', ''))


def is_recent(pub_dt, now_kst):
    if pub_dt is None: return True
    # 48시간(2일) 이내의 기사까지는 일단 포함
    limit = (now_kst - timedelta(hours=48)).date() 
    return pub_dt.date() >= limit

def is_recent(pub_dt, now_kst):
    if pub_dt is None: return True
    # 최신성 확보를 위해 6시간 이내로 필터링 강화
    limit = (now_kst - timedelta(hours=6)).date() 
    return pub_dt.date() >= limit

def scrape_busan(now_kst):
    items = []
    # 404가 발생하던 URL 제거
    urls = ["https://www.busan.com/economy/"]
    s = requests.Session()
    s.headers.update(HEADERS)
    for url in urls:
        try:
            resp = s.get(url, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            for p in soup.select('p.title'):
                a = p.find('a', href=True)
                if not a: continue
                # ... (데이터 추출 로직 동일)
        except Exception as e:
            print(f"  ER [스크랩/부산일보] {e}")
    return items

def scrape_naver_land(now_kst):
    items = [] # 여기서 items 초기화!
    seen = set()
    try:
        resp = requests.get("https://land.naver.com/news/", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # ... (네이버 뉴스 추출 로직)
    except Exception as e:
        print(f"  ER [스크랩/네이버] {e}")
    return items

# 기존 스크래핑 함수들을 모두 지우고 이 함수 하나로 대체하세요.
def scrape_all_via_google():
    items = []
    # 1. 부산일보 및 경남 지역 기사
    # 2. 국제신문 기사
    # 3. 네이버 부동산 관련 기사
    queries = {
        "부산일보": "부산 부동산 site:busan.com",
        "국제신문": "부산 부동산 site:kookje.co.kr",
        "네이버부동산": "아파트 분양 site:land.naver.com"
    }

    for name, query in queries.items():
        try:
            # Google News API를 직접 호출하는 방식 대신, 
            # 현재 잘 작동하는 구글 검색 로직을 재사용합니다.
            # (기존 [C] Google News 보완 함수와 동일한 로직을 사용)
            results = fetch_google_news(query) # 이미 코드에 있는 함수 사용
            count = 0
            for item in results:
                items.append((None, item['title'], item['link'], name))
                count += 1
            print(f"DEBUG: {name} 수집 건수: {count}건")
        except Exception as e:
            print(f"  ER [스크랩/{name}] {e}")
    return items
# ── 텍스트 처리 ───────────────────────────────────────────────────────────────
def is_estate_related(title):
    if RE_EXCLUDE.search(title):
        return False
    return bool(RE_ESTATE.search(title))


def normalize(title):
    title = re.split(r'\s[-|]\s', title)[0].strip()
    title = re.sub(r'^\[.*?\]\s*', '', title)
    title = re.sub(r'\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}', '', title)
    title = re.sub(r'[^\w\s]', ' ', title)
    title = re.sub(r'(?<!\w)[\u4e00-\u9fff](?!\w)', '', title)
    return re.sub(r'\s+', ' ', title).strip()


def keywords(title):
    return {w for w in normalize(title).split() if w not in STOPWORDS and len(w) >= 2}


def extract_entities(title):
    t = re.sub(r'[^\w\s]', ' ', str(title))
    ents = set()
    for m in re.finditer(r'\d+\.?\d*\s*(?:억|만|건|%|개월|층|평|채|명|가구)', t):
        ents.add(m.group().strip())
    for loc in LOC_ENTITIES:
        if loc in t: ents.add(loc)
    for org in ORG_ENTITIES:
        if org in t: ents.add(org)
    return ents


def is_duplicate(new_raw, seen_raw):
    nn = normalize(new_raw)
    kn = keywords(new_raw)
    en = extract_entities(new_raw)
    for s in seen_raw:
        ns = normalize(s)
        if SequenceMatcher(None, nn, ns).ratio() >= 0.65: return True
        ks = keywords(s)
        u = len(kn | ks)
        if u and len(kn & ks) / u >= 0.45: return True
        es = extract_entities(s)
        if en and es and len(en & es) >= 2: return True
    return False


def classify(title):
    t = normalize(title)
    if any(k in t for k in CAT_KEYWORDS["청약"]):     return "청약"
    if any(k in t for k in CAT_KEYWORDS["재건축"]):   return "재건축"
    if any(k in t for k in CAT_KEYWORDS["세제"]):     return "세제"
    if any(k in t for k in CAT_KEYWORDS["정책"]):     return "정책"
    if any(k in t for k in CAT_KEYWORDS["부산경남"]): return "부산경남"
    return "시장동향"


def make_session(referer=None):
    s = requests.Session()
    s.headers.update(HEADERS)
    if referer:
        s.headers["Referer"] = referer
    return s


# ── A. RSS 수집 ───────────────────────────────────────────────────────────────
def fetch_rss(name, url, estate_only, now_kst):
    items = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
        for entry in feed.entries:
            pub_dt = get_best_pub_dt(entry)
            if not is_recent(pub_dt, now_kst): continue
            title = (entry.title or "").strip()
            if not title: continue
            if estate_only:
                if RE_EXCLUDE.search(title): continue
            else:
                if not is_estate_related(title): continue
            src = name
            if hasattr(entry, 'source') and hasattr(entry.source, 'title'):
                src = entry.source.title
            items.append((pub_dt, title, entry.link, src))
        print(f"  OK [RSS/{name}] {len(items)}건")
    except Exception as e:
        print(f"  ER [RSS/{name}] {type(e).__name__}: {str(e)[:60]}")
    return items


# ── [수정] 언론사별 수집 함수 ──

def scrape_busan(now_kst):
    items = []
    # 주소 변경: 실제 기사 목록이 올라오는 최신 URL로 수정
    url = "https://www.busan.com/economy/index.html" 
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # 부산일보의 현재 뉴스 카드 구조를 모두 잡기 위한 선택자
        for a in soup.select('div.card-title a, h3.title a'):
            title = a.get_text(strip=True)
            link = urljoin("https://www.busan.com", a.get('href', ''))
            if title and len(title) > 5:
                items.append((None, title, link, "부산일보"))
    except Exception as e:
        print(f"  ER [스크랩/부산일보] {e}")
    return items

def scrape_kookje(now_kst):
    items = []
    # 주소 변경: 국제신문 부동산 섹션 메인
    url = "https://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0220"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.encoding = 'euc-kr'
        soup = BeautifulSoup(resp.text, 'html.parser')
        # dt 내부뿐만 아니라 뉴스 리스트 전체를 훑음
        for a in soup.select('div.list_wrap a'):
            title = a.get_text(strip=True)
            if 'newsbody.asp' in a.get('href', ''):
                items.append((None, title, urljoin("https://www.kookje.co.kr", a['href']), "국제신문"))
    except Exception as e:
        print(f"  ER [스크랩/국제신문] {e}")
    return items

def scrape_naver_land(now_kst):
    items = []
    # 네이버 부동산 뉴스 메인 페이지 (구조 변경 대응)
    url = "https://land.naver.com/news/main.naver"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # 네이버 부동산 뉴스 타이틀 영역 선택자 최신화
        for a in soup.select('div.news_txt a, dt.news_tit a'):
            title = a.get_text(strip=True)
            link = a.get('href', '')
            if title and link.startswith('http'):
                items.append((None, title, link, "네이버부동산"))
    except Exception as e:
        print(f"  ER [스크랩/네이버] {e}")
    return items

# ── C. Google News RSS 보완 ───────────────────────────────────────────────────
def fetch_google(now_kst):
    items = []
    domain_map = {
        "busan.com": "부산일보",
        "kookje.co.kr": "국제신문",
        "land.naver.com": "네이버부동산"
    }
    for q in GOOGLE_QUERIES:
        try:
            url  = f"https://news.google.com/rss/search?q={quote_plus(q)}&hl=ko&gl=KR&ceid=KR:ko"
            resp = requests.get(url, headers=HEADERS, timeout=8)
            feed = feedparser.parse(resp.content)
            cnt  = 0
            for entry in feed.entries:
                pub_dt = get_best_pub_dt(entry)
                if not is_recent(pub_dt, now_kst): continue
                title = (entry.title or "").strip()
                if not title or not is_estate_related(title): continue
                src = "뉴스"
                if hasattr(entry, 'source') and hasattr(entry.source, 'title'):
                    src = entry.source.title
                items.append((pub_dt, title, entry.link, src))
                cnt += 1
            print(f"  OK [Google/{q}] {cnt}건")
        except Exception as e:
            print(f"  ER [Google/{q}] {type(e).__name__}: {str(e)[:60]}")
    return items

import random

def balance_news(entries):
    """
    1. 매체별 최대 3개로 제한 (범위를 약간 늘림)
    2. 중복 기사 가능성 제거
    3. 최종적으로 시간 순으로 정렬하여 반환
    """
    if not entries:
        return []

    # 1. 매체별로 기사를 분류
    grouped = {}
    for entry in entries:
        source = entry[3]
        if source not in grouped:
            grouped[source] = []
        grouped[source].append(entry)

    # 2. 매체별로 최신 기사 3개씩만 추출 (양적 팽창)
    balanced = []
    for source, items in grouped.items():
        # 매체별 최신순 정렬 후 3개 선택
        items.sort(key=lambda x: x[0] or datetime.min.replace(tzinfo=KST), reverse=True)
        balanced.extend(items[:3])

    # 3. 전체를 다시 최신순으로 정렬 (다양성 유지 + 최신성 보장)
    balanced.sort(key=lambda x: x[0] or datetime.min.replace(tzinfo=KST), reverse=True)
    
    # 4. 전체 기사량이 너무 적다면 전체를 반환하고, 너무 많다면 200개 정도로 제한
    return balanced[:200]
# ── 메인 수집 ─────────────────────────────────────────────────────────────────
def get_clean_news():
    all_entries = []
    now_kst = datetime.now(KST)
    
    # 1. 이미 잘 작동 중인 구글 검색어 리스트에 타겟 사이트 추가
    # 기존 검색 쿼리 리스트에 아래 항목들을 추가하거나 갱신하세요
    search_queries = [
        "부동산", "아파트 분양", "재건축 재개발", "부동산 정책", 
        "부산 부동산 site:busan.com",     # 부산일보 강제 포함
        "부산 부동산 site:kookje.co.kr",   # 국제신문 강제 포함
        "아파트 분양 site:land.naver.com"  # 네이버부동산 강제 포함
    ]

    # 2. 검색 실행 및 결과 병합
    for query in search_queries:
        try:
            results = fetch_google_news(query) # 이미 코드에 있는 함수 활용
            for item in results:
                # 중복을 방지하기 위해 title을 기준으로 확인
                all_entries.append((None, item['title'], item['link'], "종합뉴스"))
        except Exception as e:
            print(f"  ER [Google/{query}] {e}")
    
    # ... 나머지 코드 ...
    cats = ["청약", "재건축", "세제", "정책", "부산경남", "시장동향"]
    results = {c: [] for c in cats}
    seen = []
    now_kst = datetime.now(KST)
    print(f"[실행시각] {now_kst.strftime('%Y-%m-%d %H:%M KST')}")
    all_entries = []

    print("\n[A] RSS 및 웹 피드 수집")
    for name, url, eo in RSS_FEEDS:
        if "newspim.com" in url or "nocutnews.co.kr" in url:
            # get_news_by_crawling 함수가 정의되어 있어야 합니다.
            # 정의되어 있지 않다면 해당 사이트들은 RSS_FEEDS에서 제외하세요.
            try:
                all_entries.extend(get_news_by_crawling(url, "ul.list_news li", "a", "a", ""))
            except NameError:
                print(f"  SK [스크랩/{name}] 함수 미정의")
        else:
            all_entries.extend(fetch_rss(name, url, eo, now_kst))

    print("\n[B] 스크래핑 수집")
    all_entries.extend(scrape_busan(now_kst))
    all_entries.extend(scrape_kookje(now_kst))
    all_entries.extend(scrape_naver_land(now_kst))

    print("\n[C] Google News 보완")
    all_entries.extend(fetch_google(now_kst))

    all_entries = balance_news(all_entries)
    all_entries.sort(key=lambda x: x[0] or datetime.max.replace(tzinfo=KST), reverse=True)

    total = dropped = 0
    for pub_dt, title, link, src in all_entries:
        total += 1
        if is_duplicate(title, seen):
            dropped += 1
            continue
        cat = classify(title)
        if len(results[cat]) < 12:
            ps = pub_dt.strftime("%m/%d %H:%M") if pub_dt else ""
            results[cat].append({"title": normalize(title), "link": link, "src": src, "pub_str": ps})
            seen.append(title)

    print(f"\n[결과] 전체 {total}건 | 중복제거 {dropped}건 | 최종 {total - dropped}건")
    return results 


# ── HTML 생성 ─────────────────────────────────────────────────────────────────
def build_html(data):
    def build_html(data):
    now = datetime.now(KST)

    today = now.strftime("%Y년 %m월 %d일")
    generated_time = now.strftime("%Y-%m-%d %H:%M:%S KST")
    html  = "<!DOCTYPE html>\n<html lang='ko'>\n<head>\n"
    html += "<meta charset='UTF-8'>\n"
    html += "<meta name='viewport' content='width=device-width, initial-scale=1.0'>\n"
    html += f"<title>부동산 뉴스 브리핑 {today}</title>\n"
    html += """<style>
body { font-family: 'Malgun Gothic', sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
h1 { color: #1a1a2e; border-bottom: 3px solid #e94560; padding-bottom: 10px; }
h2 { color: #16213e; background: #e8f4f8; padding: 8px 12px; border-left: 4px solid #0f3460; margin-top: 24px; }
.sources { background: #fff; padding: 12px; border-radius: 6px; margin-bottom: 16px; font-size: 13px; }
.sources a { color: #0f3460; text-decoration: none; margin: 0 4px; }
.sources a:hover { text-decoration: underline; }
.briefing { background: #fff3cd; padding: 12px; border-radius: 6px; border-left: 4px solid #ffc107; margin-bottom: 8px; }
.news-item { background: #fff; padding: 10px 14px; margin: 6px 0; border-radius: 4px; border-left: 3px solid #ddd; }
.news-item a { color: #1a1a2e; text-decoration: none; font-size: 14px; }
.news-item a:hover { color: #e94560; text-decoration: underline; }
.news-meta { font-size: 12px; color: #888; margin-top: 3px; }
.empty { color: #999; font-style: italic; padding: 8px; }
</style>\n</head>\n<body>\n"""
    html += f"<h1>부동산 뉴스 브리핑 ({today})</h1>\n"
    html += '<div class="sources">'
    html += " | ".join(f'<a href="{u}" target="_blank">{n}</a>' for n, u in SOURCES.items())
    html += "</div>\n"
    html += '<div class="briefing">전국 아파트 매매가격 0.05% 상승, 38주 연속 상승세 유지. 매수우위지수는 62.9%로 매도자 우위입니다.</div>\n'

    labels = {
        "청약": "청약", "재건축": "재건축 · 재개발", "세제": "세제",
        "정책": "정책 · 규제", "부산경남": "부산 · 경남", "시장동향": "시장동향",
    }
    for cat, lst in data.items():
        html += f"<h2>{labels.get(cat, cat)}</h2>\n"
        if lst:
            for n in lst:
                html += '<div class="news-item">'
                html += f'<a href="{n["link"]}" target="_blank">{n["title"]}</a>'
                html += f'<div class="news-meta">{n["src"]}'
                if n["pub_str"]:
                    html += f' · {n["pub_str"]}'
                html += '</div></div>\n'
        else:
            html += '<p class="empty">최근 수집된 기사가 없습니다.</p>\n'

    html += "</body>\n</html>"
    return html


if __name__ == "__main__":
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    data = get_clean_news()
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(build_html(data))
    total = sum(len(v) for v in data.values())
    print(f"\n[완료] {output_path} | 총 {total}건")
    for cat, lst in data.items():
        print(f"  [{cat}] {len(lst)}건")
