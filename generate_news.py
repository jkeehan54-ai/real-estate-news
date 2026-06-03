"""
부동산 뉴스 브리핑 - 멀티소스 + 24시간 필터 + 3단계 중복 제거
────────────────────────────────────────────────────────────────
수집 경로:
  1. 작동 확인된 매체 직접 RSS 13개
  2. Google News RSS 보완 5개 쿼리

날짜 판단 우선순위:
  1순위: URL 경로 /YYYY/MM/DD/ 추출  (가장 신뢰)
  2순위: RSS published_parsed UTC→KST
  없으면: 포함 처리

설치: pip install feedparser requests
"""

import feedparser
import requests
from urllib.parse import quote_plus
from difflib import SequenceMatcher
from datetime import datetime, timezone, timedelta
import re
import os

KST = timezone(timedelta(hours=9))

# ── 링크 표시 매체 ────────────────────────────────────────────────────────────
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
    "부산일보":    "https://www.busan.com/economy/",
    "국제신문":    "http://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0200",
    "주택경제신문": "https://www.arunews.com/",
    "건설타임즈":  "https://www.constimes.co.kr/",
}

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

# ── 테스트로 작동 확인된 RSS 피드 ─────────────────────────────────────────────
# (매체명, URL, 부동산전용여부)
# 부동산전용=True  → 키워드 필터 없이 전부 수집
# 부동산전용=False → 부동산 키워드 포함 기사만 수집
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
]

# Google News 보완 쿼리
GOOGLE_QUERIES = [
    "부동산 청약 분양",
    "아파트 재건축 재개발",
    "부동산 세금 종부세 취득세",
    "부동산 정책 대출 금리",
    "부동산 시장 매매 전세",
]

# 부동산 관련 키워드 (전체 피드 필터용)
RE_ESTATE = re.compile(
    r'아파트|부동산|청약|재건축|재개발|전세|월세|임대|분양|주택|매매|'
    r'PF|건설|LH|SH|HUG|준공|착공|입주|종부세|취득세|양도세|재산세|'
    r'임대료|전셋값|집값|매물|갭투자|오피스텔|빌라|다세대|공동주택'
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
    "수도권","서울","강남","강북","강동","강서","부산","경기","인천","대구",
    "광주","대전","울산","세종","제주","경남","경북","전남","전북","충남",
    "충북","강원","용산","마포","송파","성동","노원","은평","영등포",
    "해운대","수영","사하","동래","기장","연제","금정","사상",
}
ORG_ENTITIES = {
    "국세청","당근부동산","한국부동산원","법원","국토부","금융위","금감원",
    "LH","SH","HUG","주택도시보증공사",
}

# ── 날짜 유틸 ─────────────────────────────────────────────────────────────────
def extract_date_from_url(url: str) -> datetime | None:
    """URL 경로 /YYYY/MM/DD/ 에서 날짜 추출 → KST 06:00 기준"""
    m = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', url)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
                            6, 0, tzinfo=KST)
        except ValueError:
            return None
    return None

def get_best_pub_dt(entry) -> datetime | None:
    """1순위: URL 날짜 / 2순위: published_parsed"""
    url_dt = extract_date_from_url(getattr(entry, 'link', ''))
    if url_dt:
        return url_dt
    pub = entry.get("published_parsed")
    if pub:
        return datetime(*pub[:6], tzinfo=timezone.utc).astimezone(KST)
    return None

def is_within_24h(entry, now_kst: datetime) -> bool:
    pub_dt = get_best_pub_dt(entry)
    if pub_dt is None:
        return True                                      # 날짜 불명 → 포함
    return (now_kst - pub_dt).total_seconds() <= 86400  # 24시간

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

# ── RSS 피드에서 entry 수집 ───────────────────────────────────────────────────
def fetch_rss(name: str, url: str, estate_only: bool,
              now_kst: datetime) -> list:
    """(pub_dt, title, link, src_name) 리스트"""
    items = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
        for entry in feed.entries:
            if not is_within_24h(entry, now_kst):
                continue
            title = (entry.title or "").strip()
            if not title:
                continue
            if not estate_only and not RE_ESTATE.search(title):
                continue
            src = (entry.source.title
                   if hasattr(entry, 'source') and hasattr(entry.source, 'title')
                   else name)
            pub_dt = get_best_pub_dt(entry)
            items.append((pub_dt, title, entry.link, src))
        print(f"  ✅ [{name}] {len(items)}건")
    except Exception as e:
        print(f"  ❌ [{name}] {type(e).__name__}: {str(e)[:50]}")
    return items

# ── Google News RSS 수집 ──────────────────────────────────────────────────────
def fetch_google(now_kst: datetime) -> list:
    items = []
    for q in GOOGLE_QUERIES:
        try:
            url  = f"https://news.google.com/rss/search?q={quote_plus(q)}&hl=ko&gl=KR&ceid=KR:ko"
            resp = requests.get(url, headers=HEADERS, timeout=8)
            feed = feedparser.parse(resp.content)
            cnt  = 0
            for entry in feed.entries:
                if not is_within_24h(entry, now_kst):
                    continue
                title = (entry.title or "").strip()
                if not title:
                    continue
                src = (entry.source.title
                       if hasattr(entry, 'source') and hasattr(entry.source, 'title')
                       else "뉴스")
                pub_dt = get_best_pub_dt(entry)
                items.append((pub_dt, title, entry.link, src))
                cnt += 1
            print(f"  ✅ [Google·{q}] {cnt}건")
        except Exception as e:
            print(f"  ❌ [Google·{q}] {type(e).__name__}: {str(e)[:50]}")
    return items

# ── 메인 수집 함수 ────────────────────────────────────────────────────────────
def get_clean_news() -> dict:
    categories = ["청약", "재건축", "세제", "정책", "부산·경남", "시장동향"]
    results    = {c: [] for c in categories}
    seen_raw   = []
    now_kst    = datetime.now(KST)

    all_entries: list[tuple] = []

    print("\n[1단계] 매체 직접 RSS 수집")
    for name, url, estate_only in RSS_FEEDS:
        all_entries.extend(fetch_rss(name, url, estate_only, now_kst))

    print("\n[2단계] Google News RSS 보완")
    all_entries.extend(fetch_google(now_kst))

    # 최신순 정렬
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
            if pub_dt:
                url_dt = extract_date_from_url(link)
                pub_str = url_dt.strftime("%m/%d") if url_dt else pub_dt.strftime("%m/%d %H:%M")
            else:
                pub_str = ""
            results[cat].append({
                "title":   normalize(title),
                "link":    link,
                "src":     src,
                "pub_str": pub_str,
            })
            seen_raw.append(title)

    kept = total - dropped
    print(f"\n[결과] 전체 {total}건 | 중복제거 {dropped}건 | 최종 {kept}건")
    return results

# ── HTML 생성 ─────────────────────────────────────────────────────────────────
def build_html(data: dict) -> str:
    today = datetime.now(KST).strftime("%Y년 %m월 %d일")
    html  = f"<h1>🏠 부동산 뉴스 브리핑 ({today})</h1>\n"
    html += " | ".join(
        f'<a href="{u}" target="_blank">{n}</a>' for n, u in SOURCES.items()
    )
    html += "\n<h2>오늘의 핵심 브리핑</h2>"
    html += "<p>전국 아파트 매매가격 0.05% 상승, 38주 연속 상승세 유지. 매수우위지수는 62.9%로 매도자 우위입니다.</p>"

    icons = {"청약":"🏗","재건축":"🔨","세제":"💰","정책":"📋","부산·경남":"🌊","시장동향":"📈"}
    for cat, lst in data.items():
        html += f"<h2>[{icons.get(cat,'')} {cat}]</h2>"
        if lst:
            html += "".join(
                f"<p>"
                f"<a href='{n['link']}' target='_blank'>{n['title']}</a>"
                f" | <b>{n['src']}</b>"
                + (f" <small style='color:#aaa'>({n['pub_str']})</small>" if n['pub_str'] else "")
                + "</p>"
                for n in lst
            )
        else:
            html += "<p>최근 24시간 내 수집된 기사가 없습니다.</p>"
    return html

# ── 실행 ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # 실행되는 파일(generate_news.py)이 있는 폴더에 index.html을 강제 생성
    base_path = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(base_path, "index.html")
    
    data = get_clean_news()
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(build_html(data))
    print(f"파일이 저장되었습니다: {output_path}")
    print(f"[완료] 카테고리별 수집 결과:")
    for cat, lst in data.items():
        print(f"  [{cat}] {len(lst)}건")
