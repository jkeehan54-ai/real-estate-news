# generate_news_modular.py
"""
부동산 뉴스 브리핑 - 비용 없는 자동 필터링
============================================
비부동산 제거: RE_ESTATE(포함) + RE_EXCLUDE(제외) 2중 규칙
중복 제거: 문자열유사도 + 키워드자카드 + 엔티티겹침 3단계
날짜: datetime.now(KST) 명시 → GitHub Actions UTC 환경에서도 정확
"""
import sys, io
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import feedparser, requests, re, os
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin
from difflib import SequenceMatcher
from datetime import datetime, timezone, timedelta
from modules.news_config import *
from modules.news_utils import *
from modules.news_filter import *
from modules.rss_engine import *
from modules.crawler_engine import *
from modules.google_engine import *
from modules.kb_market import *
from modules.html_builder import *

KST = timezone(timedelta(hours=9))

SOURCES = {
    "조선일보":    "https://www.chosun.com/economy/real_estate/",
    "중앙일보":    "https://www.joongang.co.kr/realestate",
    "동아일보":    "https://www.donga.com/news/Economy/Realestate",
    "한겨레":      "https://www.hani.co.kr/arti/economy/property/",
    "매일경제":    "https://www.mk.co.kr/news/realestate/",
    "한국경제":    "https://www.hankyung.com/realestate",
    "서울경제":    "https://www.sedaily.com/News/RealeState",
    "연합뉴스":    "https://www.yna.co.kr/economy/real-estate/",
    "부산일보":    "https://www.busan.com/economy/",
    "국제신문":    "http://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0220",
    "주택경제신문": "https://www.arunews.com/",
    "건설타임즈":  "https://www.constimes.co.kr/",
    "네이버부동산": "https://land.naver.com/news/",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": "https://www.google.com/",
    "Cache-Control": "no-cache",
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
    ("아주경제",    "https://www.ajunews.com/rss/economy.xml",                     False),
    ("아시아경제",  "https://www.asiae.co.kr/rss/all.htm",                         False),
    ("조선일보",    "https://www.chosun.com/arc/outboundfeeds/rss/?outputType=xml", False),
    ("경남도민일보", "https://www.idomin.com/rss/allArticle.xml",                  False),
]

GOOGLE_QUERIES = [
    "부동산 청약 분양",
    "아파트 재건축 재개발",
    "부동산 세금 종부세 취득세",
    "부동산 정책 대출 금리",
    "아파트 매매 전세 집값",
    "부산 부동산 아파트",
    "해운대 아파트 분양",
    "부산 재건축 재개발",
    "경남 아파트 분양",
    "분양가 상한제 아파트",
    "임대차 전세 월세",
    "신도시 공공주택 공급",
]

# ══════════════════════════════════════════════════════════════════════════════
# 핵심 필터 3개 — 이 3개만 제대로 작동하면 비부동산·중복 99% 해결
# ══════════════════════════════════════════════════════════════════════════════

# [필터1] 부동산 핵심어 — 하나라도 없으면 수집 자체를 안 함
RE_ESTATE = re.compile(
    r'아파트|부동산|청약|재건축|재개발|전세|월세|임대|분양|주택|매매|'
    r'오피스텔|빌라|다세대|공동주택|정비사업|가로주택|'
    r'LH|SH|HUG|담보대출|주담대|전셋값|갭투자|분양가|'
    r'집값|매물|공시가|실거래|종부세|취득세|양도세|재산세|'
    r'신도시|택지|용적률|역세권|준공|착공|견본주택|모델하우스|'
    r'에코델타|오시리아|북항|재산세|입주물량|미분양'
)

# [필터2] 비부동산 제외어 — 하나라도 있으면 무조건 제거
# ★ 수정 포인트: 매수·매도·공급은 부동산 용어이므로 제외 목록에서 삭제
# ★ 수정 포인트: | 연결 정확히 작성 (줄 끝 |, 다음 줄 시작으로 연결)
RE_EXCLUDE = re.compile(
    r'숨진|사망|시신|변사|화상|부상|입건|구속|체포|검거|'
    r'화재|폭발|음주운전|교통사고|폭행|'
    r'전동킥보드|전동휠체어|오토바이|승용차 몰다|'
    r'코스피|코스닥|나스닥|환율|달러|증시|주가|주식|펀드|ETF|채권|'
    r'반도체|배터리|전기차|수출입|무역|관세|원자재|'
    r'열차|철도|항공|공항|항공편|비행기|선박|'
    r'태양광|풍력|수소|원전|발전소|배출권|탄소|'
    r'LNG|액화천연가스|플랜트|해양|제련소|항만|댐|터널|교량|도로공사|'
    r'폐작업복|필통|군 복무|병역|어린이집|미술관|도서관|공연|전시|'
    r'창업|귀농|스페이스X|공모주|상장|IPO|주식청약|'
    r'입찰공고|용역공고|협력업체 선정|현장설명회|현설|'
    r'선거|투표|정당|여당|야당|국회의원 선거|대통령 선거'
)

# [필터3] 시장동향 전용 2차 필터 — 시장동향으로 분류된 기사에만 적용
# 이 키워드가 없으면 시장동향에서도 제거 (비부동산 기사 차단)
RE_MARKET_REQUIRED = re.compile(
    r'아파트|부동산|주택|전세|월세|매매|집값|전셋값|매물|거래|'
    r'오피스텔|빌라|다세대|상가|토지|공시가|실거래|'
    r'임대|분양|입주|미분양|역세권|복합단지|용적률|'
    r'건설사|시행사|공사비|분양가|HUG|LH|SH|'
    r'관리처분|이주비|수주|인허가|사업승인|정비구역'
)

# ── 중복 제거용 상수 ──────────────────────────────────────────────────────────
STOPWORDS = {
    "은","는","이","가","을","를","의","에","도","와","과","하고","으로","로",
    "에서","까지","부터","이다","합니다","입니다","했다","한다","됩니다","됐다",
    "및","등","것","안","돼","않다","이라고","라며","라고","하며","있다","없다",
    "하다","된다","한","더","또","위해","대해",
}
LOC_ENTITIES = {
    "수도권","서울","강남","강북","부산","경기","인천","대구","광주","대전",
    "울산","세종","경남","해운대","수영","사하","동래","기장","연제","금정",
}
ORG_ENTITIES = {"국세청","한국부동산원","국토부","금융위","금감원","LH","SH","HUG"}

CAT_LIMITS = {
    "청약":    12,
    "재건축":  12,
    "공급개발": 10,
    "세제":    10,
    "정책":    10,
    "부산경남": 15,
    "시장동향": 15,
}

SOURCE_LIMITS = {
    "건설타임즈":  6,
    "주택경제신문": 6,
    "경남도민일보": 4,
}


# ── 날짜 유틸 ─────────────────────────────────────────────────────────────────
def extract_date_from_url(url):
    for pattern in [
        r'/(\d{4})/(\d{2})/(\d{2})/',
        r'key=(\d{4})(\d{2})(\d{2})\.',
        r'code=(\d{4})(\d{2})(\d{2})',
    ]:
        m = re.search(pattern, url)
        if m:
            try:
                return datetime(
                    int(m.group(1)), int(m.group(2)), int(m.group(3)),
                    0, 0, tzinfo=KST
                )
            except Exception:
                pass
    return None

def get_best_pub_dt(entry):
    pub = entry.get("published_parsed")
    if pub:
        return datetime(*pub[:6], tzinfo=timezone.utc).astimezone(KST)
    return extract_date_from_url(getattr(entry, 'link', ''))

def is_recent(pub_dt, now_kst):
    """어제~오늘 기사. 날짜 불명 → 포함."""
    if pub_dt is None:
        return True
    yesterday = (now_kst - timedelta(days=1)).date()
    return pub_dt.date() >= yesterday


# ══════════════════════════════════════════════════════════════════════════════
# 비부동산 제거 함수
# ══════════════════════════════════════════════════════════════════════════════
def is_estate_related(title: str) -> bool:
    """
    부동산 기사 여부 판단.
    조건: RE_ESTATE 포함 AND RE_EXCLUDE 미포함
    → 둘 다 통과해야 True
    """
    if RE_EXCLUDE.search(title):   # 제외어 있으면 즉시 False
        return False
    return bool(RE_ESTATE.search(title))  # 부동산 키워드 있어야 True

def is_market_valid(title: str) -> bool:
    """시장동향 2차 필터 — 부동산 핵심어 필수"""
    if RE_EXCLUDE.search(title):
        return False
    return bool(RE_MARKET_REQUIRED.search(title))


# ══════════════════════════════════════════════════════════════════════════════
# 중복 제거 함수 (3단계, 비용 없음)
# ══════════════════════════════════════════════════════════════════════════════
def normalize(title: str) -> str:
    """제목 정규화 — 불필요한 기호·날짜·매체명 제거"""
    title = re.split(r'\s[-|]\s', title)[0].strip()   # '- 매일경제' 등 제거
    title = re.sub(r'^\[.*?\]\s*', '', title)           # [속보] 등 제거
    title = re.sub(r'\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}', '', title)  # 날짜 제거
    title = re.sub(r'[^\w\s]', ' ', title)              # 특수문자 제거
    title = re.sub(r'(?<!\w)[\u4e00-\u9fff](?!\w)', '', title)  # 한자 제거
    return re.sub(r'\s+', ' ', title).strip()

def keywords(title: str) -> set:
    return {w for w in normalize(title).split() if w not in STOPWORDS and len(w) >= 2}

def extract_entities(title: str) -> set:
    """숫자단위·지명·기관명 추출 — 중복 판별 정밀도 향상"""
    t = re.sub(r'[^\w\s]', ' ', str(title))
    ents = set()
    for m in re.finditer(r'\d+\.?\d*\s*(?:억|만|건|%|개월|층|평|채|명|가구)', t):
        ents.add(m.group().strip())
    for loc in LOC_ENTITIES:
        if loc in t: ents.add(loc)
    for org in ORG_ENTITIES:
        if org in t: ents.add(org)
    return ents

def is_duplicate(new_title: str, seen: list) -> bool:
    """
    3단계 중복 판별 (비용 없음, 빠름):
    1단계: 문자열 유사도 0.72 이상  → 같은 기사 (제목 일부만 달라도 잡힘)
    2단계: 키워드 자카드 0.55 이상  → 같은 주제 다른 표현
    3단계: 핵심 엔티티 2개 이상 겹침 → 같은 단지·지역·금액
    """
    nn = normalize(new_title)
    kn = keywords(new_title)
    en = extract_entities(new_title)
    for s in seen:
        ns = normalize(s)
        # 1단계: 문자열 유사도
        if SequenceMatcher(None, nn, ns).ratio() >= 0.72:
            return True
        # 2단계: 키워드 자카드
        ks = keywords(s)
        u  = len(kn | ks)
        if u and len(kn & ks) / u >= 0.55:
            return True
        # 3단계: 엔티티 겹침
        es = extract_entities(s)
        if en and es and len(en & es) >= 2:
            return True
    return False


# ── 카테고리 분류 ─────────────────────────────────────────────────────────────
def classify(title: str) -> str:
    """★ 순서 중요: 좁은 범위 → 넓은 범위"""
    t = normalize(title)
    if any(k in t for k in ["청약", "무순위", "청약통장", "특별공급", "일반공급"]):
        return "청약"
    if any(k in t for k in ["재건축", "재개발", "정비사업", "가로주택", "리모델링"]):
        return "재건축"
    if any(k in t for k in ["종부세", "취득세", "양도세", "재산세", "세금", "세제",
                              "비과세", "감면", "절세", "공시가"]):
        return "세제"
    if any(k in t for k in ["대출", "금리", "정책", "규제", "완화", "DSR", "LTV",
                              "DTI", "주담대", "담보대출", "전세대출", "임대차",
                              "계약갱신", "전월세상한"]):
        return "정책"
    if any(k in t for k in ["신도시", "공공주택", "착공", "준공", "용적률",
                              "복합개발", "도시개발", "역세권", "택지", "입주물량"]):
        return "공급개발"
    if any(k in t for k in [
        "부산", "해운대", "수영구", "동래", "센텀", "광안", "명지",
        "에코델타", "오시리아", "기장", "사하", "사상", "연제", "금정",
        "북항", "부산진", "영도", "강서구", "창원", "김해", "양산",
        "밀양", "진주", "거제", "통영", "경남", "울산",
    ]):
        return "부산경남"
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
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
        for entry in feed.entries:
            pub_dt = get_best_pub_dt(entry)
            if not is_recent(pub_dt, now_kst):
                continue
            title = (entry.title or "").strip()
            if not title:
                continue
            # ★ 전용(True)/일반(False) 피드 모두 동일하게 필터 적용
            if not is_estate_related(title):
                continue
            src = name
            if hasattr(entry, 'source') and hasattr(entry.source, 'title'):
                src = entry.source.title
            items.append((pub_dt, title, entry.link, src))
        print(f"  OK [RSS/{name}] {len(items)}건")
    except Exception as e:
        print(f"  ER [RSS/{name}] {type(e).__name__}: {str(e)[:50]}")
    return items


# ── B-1. 부산일보 스크래핑 ───────────────────────────────────────────────────
def scrape_busan(now_kst):
    items = []
    seen  = set()
    for url in ["https://www.busan.com/economy/",
                "https://www.busan.com/newsList/realestate"]:
        try:
            s    = make_session("https://www.busan.com/")
            resp = s.get(url, timeout=10)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, 'html.parser')
            for el in soup.select('p.title, .title a, h4 a, h3 a'):
                a = el if el.name == 'a' else el.find('a', href=True)
                if not a:
                    continue
                title = a.get_text(strip=True)
                href  = a.get('href', '')
                if not title or len(title) < 10 or not href:
                    continue
                if not is_estate_related(title):
                    continue
                link = urljoin("https://www.busan.com", href)
                if link in seen:
                    continue
                seen.add(link)
                pub_dt = extract_date_from_url(link)
                if not is_recent(pub_dt, now_kst):
                    continue
                items.append((pub_dt, title, link, "부산일보"))
        except Exception as e:
            print(f"  ER [부산일보] {type(e).__name__}: {str(e)[:50]}")
    print(f"  OK [부산일보] {len(items)}건")
    return items


# ── B-2. 국제신문 스크래핑 ───────────────────────────────────────────────────
def scrape_kookje(now_kst):
    items = []
    seen  = set()
    for url in [
        "https://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0220",
        "https://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0200",
    ]:
        try:
            s    = make_session("https://www.kookje.co.kr/")
            resp = s.get(url, timeout=10)
            if resp.status_code != 200:
                continue
            resp.encoding = 'euc-kr'   # ★ 국제신문은 EUC-KR 인코딩
            soup = BeautifulSoup(resp.text, 'html.parser')
            for sel in [
                'ol.tabcontent li a',
                'ol#hitlist1 li a', 'ol#hitlist2 li a',
                'ol#hitlist3 li a', 'ol#hitlist4 li a', 'ol#hitlist5 li a',
                'dt a', 'h2 a', 'h3.tit a',
            ]:
                for a in soup.select(sel):
                    title = a.get_text(strip=True)
                    href  = a.get('href', '')
                    if not title or len(title) < 10:
                        continue
                    if 'newsbody.asp' not in href:
                        continue
                    if not is_estate_related(title):
                        continue
                    link = urljoin("https://www.kookje.co.kr", href)
                    if link in seen:
                        continue
                    seen.add(link)
                    pub_dt = extract_date_from_url(link)
                    if not is_recent(pub_dt, now_kst):
                        continue
                    items.append((pub_dt, title, link, "국제신문"))
        except Exception as e:
            print(f"  ER [국제신문] {type(e).__name__}: {str(e)[:50]}")
    print(f"  OK [국제신문] {len(items)}건")
    return items


# ── B-3. 네이버 부동산 스크래핑 ──────────────────────────────────────────────
def scrape_naver_land(now_kst):
    items = []
    seen  = set()
    for url, base in [
        ("https://land.naver.com/news/",  "https://land.naver.com"),
        ("https://fin.land.naver.com/news", "https://fin.land.naver.com"),
    ]:
        try:
            s    = make_session(base + "/")
            resp = s.get(url, timeout=10)
            if resp.status_code != 200:
                print(f"  ER [네이버부동산] HTTP {resp.status_code}")
                continue
            soup = BeautifulSoup(resp.text, 'html.parser')
            cnt  = 0
            for sel in [
                'ul.category_list li a', 'ul#land_news_list li a',
                'li.main_news a', 'li.main_article_beta a',
                'li.news_headline a', 'li.news_breaking a',
                'a[class*="NewsList_link"]', 'a[class*="CardNews_link"]',
                'div[class*="AllNews_article"] a',
            ]:
                for a in soup.select(sel):
                    title = a.get_text(strip=True)
                    href  = a.get('href', '')
                    if not title or len(title) < 10 or not href.startswith('http'):
                        continue
                    if not is_estate_related(title) or href in seen:
                        continue
                    seen.add(href)
                    pub_dt = extract_date_from_url(href)
                    items.append((pub_dt, title, href, "네이버부동산"))
                    cnt += 1
            print(f"  OK [네이버({base.split('/')[2]})] {cnt}건")
        except Exception as e:
            print(f"  ER [네이버부동산] {type(e).__name__}: {str(e)[:50]}")
    return items


# ── C. Google News RSS ───────────────────────────────────────────────────────
def fetch_google(now_kst):
    items = []
    for q in GOOGLE_QUERIES:
        try:
            url  = f"https://news.google.com/rss/search?q={quote_plus(q)}&hl=ko&gl=KR&ceid=KR:ko"
            resp = requests.get(url, headers=HEADERS, timeout=10)
            feed = feedparser.parse(resp.content)
            cnt  = 0
            for entry in feed.entries:
                pub_dt = get_best_pub_dt(entry)
                if not is_recent(pub_dt, now_kst):
                    continue
                title = (entry.title or "").strip()
                if not title or not is_estate_related(title):
                    continue
                src  = "뉴스"
                if hasattr(entry, 'source') and hasattr(entry.source, 'title'):
                    src = entry.source.title
                link = entry.link
                # 링크로 매체명 보정
                if "busan.com"    in link: src = "부산일보"
                if "kookje.co.kr" in link: src = "국제신문"
                if "land.naver.com" in link or "fin.land.naver.com" in link:
                    src = "네이버부동산"
                items.append((pub_dt, title, link, src))
                cnt += 1
            print(f"  OK [Google/{q}] {cnt}건")
        except Exception as e:
            print(f"  ER [Google/{q}] {type(e).__name__}: {str(e)[:50]}")
    return items


# ── 메인 수집 ─────────────────────────────────────────────────────────────────
def get_clean_news():
    cats    = ["청약", "재건축", "공급개발", "세제", "정책", "부산경남", "시장동향"]
    results = {c: [] for c in cats}
    seen    = []   # 중복 판별용 제목 목록
    src_cnt = {}   # 매체별 수집 건수
    now_kst = datetime.now(KST)
    print(f"[실행시각] {now_kst.strftime('%Y-%m-%d %H:%M KST')}")
    all_entries = []

    print("\n[A] RSS 피드")
    for name, url, eo in RSS_FEEDS:
        all_entries.extend(fetch_rss(name, url, eo, now_kst))

    print("\n[B] 스크래핑 (부산일보/국제신문/네이버부동산)")
    all_entries.extend(scrape_busan(now_kst))
    all_entries.extend(scrape_kookje(now_kst))
    all_entries.extend(scrape_naver_land(now_kst))

    print("\n[C] Google News RSS")
    all_entries.extend(fetch_google(now_kst))

    print(f"\n수집 합계(필터전): {len(all_entries)}건")

    # 최신순 정렬
    all_entries.sort(
        key=lambda x: x[0] or datetime.max.replace(tzinfo=KST),
        reverse=True
    )

    total = dup = nonre = 0
    for pub_dt, title, link, src in all_entries:
        total += 1

        # ① 중복 제거 (3단계 유사도)
        if is_duplicate(title, seen):
            dup += 1
            continue

        # ② 카테고리 분류
        cat = classify(title)

        # ③ 시장동향 2차 필터
        if cat == "시장동향" and not is_market_valid(title):
            nonre += 1
            continue

        # ④ 매체별 한도
        if src in SOURCE_LIMITS and src_cnt.get(src, 0) >= SOURCE_LIMITS[src]:
            continue

        # ⑤ 카테고리별 한도
        if len(results[cat]) >= CAT_LIMITS[cat]:
            continue

        pub_str = pub_dt.strftime("%m/%d %H:%M") if pub_dt else ""
        results[cat].append({
            "title":   normalize(title),
            "link":    link,
            "src":     src,
            "pub_str": pub_str,
        })
        seen.append(title)
        src_cnt[src] = src_cnt.get(src, 0) + 1

    kept = total - dup - nonre
    print(f"\n[결과] 전체 {total}건 | 중복제거 {dup}건 | 비부동산제외 {nonre}건 | 최종 {kept}건")
    for cat in cats:
        print(f"  [{cat}] {len(results[cat])}건")
    print("\n[매체별]")
    for k, v in sorted(src_cnt.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}건")
    return results

def market_text(value):

    value = float(value)

    if value > 0:
        return f"{value:.2f}% 상승"

    elif value < 0:
        return f"{abs(value):.2f}% 하락"

    return "0.00% 보합"
def get_latest_kb_date():

    url = (
        "https://api.kbland.kr/land-extra/market-conditions/ref-date"
        "?거래유형=1&주기=1"
    )

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://kbland.kr",
        "Referer": "https://kbland.kr/",
        "webservice": "1",
    }

    r = requests.get(
        url,
        headers=headers,
        timeout=20
    )

    r.raise_for_status()

    data = r.json()

    latest = data["dataBody"]["data"][0]

    print("[KB 최신 기준일]", latest)

    return latest
    
# ── HTML 생성 ─────────────────────────────────────────────────────────────────
def get_market_brief():

    try:

        latest = get_latest_kb_date()

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://kbland.kr",
            "Referer": "https://kbland.kr/",
            "webservice": "1",
        }

        url = (
            "https://api.kbland.kr/land-extra/market-conditions/sales"
            f"?기준년월일={latest}"
            "&법정동코드=0000000000"
        )

        r = requests.get(
            url,
            headers=headers,
            timeout=20
        )

        print("[KB STATUS]", r.status_code)

        data = r.json()

        print(
            "[KB DATA DATE]",
            data["dataBody"]["data"]["기준년월일"]
        )

        summary = data["dataBody"]["data"]["시장요약"]
        print("[KB SUMMARY]")
        print(summary)
        change = summary["대표지역변동률"]
        weeks = summary["대표지역변동률연속주수"]
        trend = summary["대표지역변동률연속상태"]

        seller = summary["매도자많음응답"]
        buyer = summary["매수자많음응답"]

        all_market = data["dataBody"]["data"]["전체시황"]

        seoul = next(
            x["변동률"]
            for x in all_market
            if x["지역명"] == "서울"
        )

        busan = next(
            x["변동률"]
            for x in all_market
            if x["지역명"] == "부산"
        )

        return (
            f"전국 아파트 매매가격은 {change}% {trend}했습니다. "
            f"{weeks}주 연속 {trend}세를 유지했습니다. "
            f"서울은 {market_text(seoul)}, "
            f"부산은 {market_text(busan)}입니다. "
            f"매도자많음 {seller}%, "
            f"매수자많음 {buyer}%입니다."
        )

    except Exception as e:

        print("[KB ERROR]", repr(e))

        return "KB 시황 정보를 불러오지 못했습니다."

def interleave_by_source(items):

    groups = {}

    for item in items:
        groups.setdefault(item["src"], []).append(item)

    result = []

    while groups:
        for src in list(groups.keys()):
            result.append(groups[src].pop(0))

            if not groups[src]:
                del groups[src]

    return result


def build_html(data):
    today       = datetime.now(KST).strftime("%Y년 %m월 %d일")
    update_time = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    total_news  = sum(len(v) for v in data.values())

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>부동산 뉴스 브리핑 {today}</title>
<style>
body{{font-family:'Malgun Gothic',sans-serif;max-width:1100px;margin:auto;padding:20px;line-height:1.7;background:#f8f9fa}}
h1{{color:#1f4fa3;border-bottom:3px solid #1f4fa3;padding-bottom:8px}}
h2{{background:#f2f6ff;padding:8px 12px;border-left:5px solid #1f4fa3;margin-top:24px}}
.sources{{background:#fff;padding:10px;border-radius:6px;margin-bottom:12px;font-size:13px}}
.sources a{{color:#1f4fa3;text-decoration:none;margin:0 4px}}
.sources a:hover{{text-decoration:underline}}
.briefing{{background:#fff3cd;padding:12px;border-radius:6px;border-left:4px solid #ffc107;margin:12px 0;font-weight:bold}}
.news-item{{background:#fff;padding:9px 14px;margin:5px 0;border-radius:4px;border-left:3px solid #dee2e6}}
.news-item a{{text-decoration:none;color:#222;font-size:14px;line-height:1.5}}
.news-item a:hover{{color:#1f4fa3;text-decoration:underline}}
.news-meta{{font-size:12px;color:#888;margin-top:2px}}
.empty{{color:#999;font-style:italic;padding:6px}}
.cnt{{font-size:12px;color:#666;font-weight:normal;margin-left:6px}}
</style>
</head>
<body>
<h1>부동산 뉴스 브리핑 ({today})</h1>
<p style="color:#666;font-size:13px">업데이트: {update_time} | 총 {total_news}건</p>
<div class="sources"><b>뉴스매체:</b> """
    html += " | ".join(f'<a href="{u}" target="_blank">{n}</a>' for n, u in SOURCES.items())
    html += f'</div>\n<div class="briefing">{get_market_brief()}</div>\n'

    labels = {
        "청약":    "[청약]",
        "재건축":  "[재건축·재개발]",
        "공급개발": "[공급·개발]",
        "세제":    "[세제]",
        "정책":    "[정책·규제]",
        "부산경남": "[부산·경남]",
        "시장동향": "[시장동향]",
    }
    for cat, lst in data.items():
        html += f'<h2>{labels.get(cat,cat)}<span class="cnt">({len(lst)}건)</span></h2>\n'
        if not lst:
            html += '<p class="empty">최근 24시간 내 수집된 기사가 없습니다.</p>\n'
            continue
        display = interleave_by_source(lst) if cat == "시장동향" else lst
        for n in display:
            print(n)
            html += '<div class="news-item">'
            html += f'<a href="{n["link"]}" target="_blank">{n["title"]}</a>'
            html += f'<div class="news-meta"><b>{n["src"]}</b>'
            if n["pub_str"]:
                html += f' · {n["pub_str"]}'
            html += '</div></div>\n'

    html += f"<p style='text-align:right;color:#bbb;font-size:11px'>총 {total_news}건 · {today}</p>\n"
    html += "</body>\n</html>"
    return html


if __name__ == "__main__":
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    data = get_clean_news()
    with open(output_path, "w", encoding="utf-8-sig") as f:
        f.write(build_html(data))
    print(f"\n[완료] {output_path}")
    for cat, lst in data.items():
        print(f"  [{cat}] {len(lst)}건")
           

