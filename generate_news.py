"""
부동산 뉴스 브리핑 - 멀티소스 수집 + 3단계 중복 제거
────────────────────────────────────────────────────────
수집 경로:
  1. 각 매체 직접 RSS  (연합뉴스·매일경제·한국경제·머니투데이 등)
  2. Google News RSS   (위 RSS에서 못 잡은 매체 보완)

설치:
  pip install feedparser requests
"""

import feedparser
import requests
from urllib.parse import quote_plus
from difflib import SequenceMatcher
from datetime import datetime, timezone, timedelta
import re

# ── 한국 시간대 ───────────────────────────────────────────────────────────────
KST = timezone(timedelta(hours=9))

# ── 매체별 직접 RSS 피드 ──────────────────────────────────────────────────────
# 형식: (매체명, RSS_URL, 부동산 전용 여부)
DIRECT_RSS = [
    # 전국 경제지
    ("연합뉴스",    "https://www.yna.co.kr/economy/real-estate/rss.xml",          True),
    ("매일경제",    "https://www.mk.co.kr/rss/50200030/",                          True),
    ("한국경제",    "https://www.hankyung.com/feed/realestate",                    True),
    ("머니투데이",  "https://news.mt.co.kr/mtview/rss/estate.xml",                 True),
    ("이데일리",    "https://www.edaily.co.kr/rss/realestate.xml",                 True),
    ("서울경제",    "https://www.sedaily.com/Rss/RealEstate",                      True),
    ("헤럴드경제",  "https://biz.heraldcorp.com/rss/realestate.xml",               True),
    ("뉴시스",      "https://www.newsis.com/rss/realestate.xml",                   True),
    ("아주경제",    "https://www.ajunews.com/rss/realestate.xml",                  True),
    ("파이낸셜뉴스","https://www.fnnews.com/rss/fn_realestate_news.xml",           True),
    ("조선일보",    "https://www.chosun.com/arc/outboundfeeds/rss/category/economy/real_estate/", True),
    ("동아일보",    "https://rss.donga.com/economy.xml",                           False),  # 경제 전체
    # 부산/지역
    ("부산일보",    "https://www.busan.com/rss/rss_article.jsp?sec_cd=1010",       False),
    ("국제신문",    "https://www.kookje.co.kr/news2011/rss/rss_0200.xml",          False),
    # 네이버 뉴스 (부동산 섹션)
    ("네이버뉴스",  "https://rss.news.naver.com/cs/rss/estate.xml",                True),
]

# ── Google News RSS 보완 쿼리 ────────────────────────────────────────────────
GOOGLE_QUERIES = [
    "부동산 청약",
    "아파트 재건축 재개발",
    "부동산 세금 종부세 취득세",
    "부동산 정책 대출 금리",
    "부동산 시장 동향 매매",
    "부동산 부산",              # 부산 지역 특화
    "아파트 분양 입주",
    "전세 월세 임대차",
]

# ── 링크 표시용 매체 목록 ─────────────────────────────────────────────────────
SOURCES = {
    "조선일보":    "https://www.chosun.com/economy/real_estate/",
    "중앙일보":    "https://www.joongang.co.kr/realestate",
    "동아일보":    "https://www.donga.com/news/Economy/Realestate",
    "한겨레":      "https://www.hani.co.kr/arti/economy/property/",
    "매일경제":    "https://www.mk.co.kr/news/realestate/",
    "한국경제":    "https://www.hankyung.com/realestate",
    "머니투데이":  "https://news.mt.co.kr/estate/",
    "서울경제":    "https://www.sedaily.com/News/RealeState",
    "이데일리":    "https://www.edaily.co.kr/news/realestate",
    "연합뉴스":    "https://www.yna.co.kr/economy/real-estate/",
    "부산일보":    "https://www.busan.com/economy/",
    "국제신문":    "http://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0200",
    "네이버부동산": "https://land.naver.com/news/",
}

# ── 공통 HTTP 헤더 (봇 차단 우회) ────────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

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

def is_recent(entry, cutoff: datetime) -> bool:
    pub_dt = get_pub_dt(entry)
    if pub_dt is None:
        return True   # 날짜 없으면 포함
    return pub_dt >= cutoff

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

# ── RSS 파싱 (requests로 헤더 포함 요청) ──────────────────────────────────────
def fetch_rss(url: str, source_name: str) -> list:
    """(pub_dt, entry, source_name) 튜플 리스트 반환"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
        items = []
        for entry in feed.entries:
            # source 필드가 없는 직접 RSS는 매체명을 직접 주입
            if not hasattr(entry, 'source') or not hasattr(entry.source, 'title'):
                entry['source'] = feedparser.FeedParserDict({'title': source_name})
            items.append((get_pub_dt(entry), entry))
        print(f"  ✅ {source_name}: {len(items)}건")
        return items
    except Exception as e:
        print(f"  ❌ {source_name}: {type(e).__name__} - {str(e)[:50]}")
        return []

# ── 카테고리 분류 ─────────────────────────────────────────────────────────────
def classify(title: str) -> str:
    t = normalize(title).lower()
    if   any(k in t for k in ["분양","청약"]):              return "청약"
    elif any(k in t for k in ["재건축","재개발"]):           return "재건축"
    elif any(k in t for k in ["세금","종부세","취득세","양도세","재산세"]):
                                                            return "세제"
    elif any(k in t for k in ["정부","대출","금리","정책","규제","완화"]):
                                                            return "정책"
    elif any(k in t for k in ["부산","경남","울산","해운대","사하","동래",
                               "북구","사상","강서","기장"]):
                                                            return "부산"
    return "시장동향"

# ── 메인 수집 함수 ────────────────────────────────────────────────────────────
def get_clean_news() -> dict:
    results  = {"청약":[],"재건축":[],"세제":[],"정책":[],"부산":[],"시장동향":[]}
    seen_raw = []
    now_kst  = datetime.now(KST)
    cutoff   = now_kst.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(hours=6)

    all_entries: list[tuple] = []

    # ① 매체 직접 RSS 수집
    print("\n[1단계] 매체 직접 RSS 수집")
    for name, url, _ in DIRECT_RSS:
        all_entries.extend(fetch_rss(url, name))

    # ② Google News RSS 보완 수집
    print("\n[2단계] Google News RSS 보완 수집")
    for q in GOOGLE_QUERIES:
        url  = f"https://news.google.com/rss/search?q={quote_plus(q)}&hl=ko&gl=KR&ceid=KR:ko"
        items = fetch_rss(url, f"Google({q})")
        all_entries.extend(items)

    # ③ 최신순 정렬 (날짜 없는 기사는 맨 앞)
    all_entries.sort(
        key=lambda x: x[0] or datetime.max.replace(tzinfo=KST),
        reverse=True
    )

    total = skipped = dropped = 0
    for pub_dt, entry in all_entries:
        total += 1
        raw = entry.title

        # 날짜 필터
        if pub_dt and pub_dt < cutoff:
            skipped += 1
            continue

        # 부동산 관련 기사인지 1차 확인 (직접 RSS는 이미 부동산 섹션)
        # Google RSS 결과는 키워드 필터 불필요 (쿼리 자체가 부동산)

        # 3단계 중복 제거
        if is_duplicate(raw, seen_raw):
            dropped += 1
            continue

        cat = classify(raw)

        if len(results[cat]) < 12:
            src = (entry.source.title
                   if hasattr(entry, "source") and hasattr(entry.source, "title")
                   else "뉴스")
            pub_str = pub_dt.strftime("%m/%d %H:%M") if pub_dt else ""
            results[cat].append({
                "title":  normalize(raw),
                "link":   entry.link,
                "src":    src,
                "pub_dt": pub_str,
            })
            seen_raw.append(raw)

    kept = total - skipped - dropped
    print(f"\n[결과] 전체 {total}건 | 날짜필터 -{skipped}건 | 중복제거 -{dropped}건 | 최종 {kept}건")
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

    cat_labels = {
        "청약":    "🏗 청약",
        "재건축":  "🔨 재건축·재개발",
        "세제":    "💰 세제",
        "정책":    "📋 정책·규제",
        "부산":    "🌊 부산·경남",
        "시장동향":"📈 시장동향",
    }

    for cat, lst in data.items():
        html += f"<h2>[{cat_labels.get(cat, cat)}]</h2>"
        if lst:
            html += "".join(
                f"<p>"
                f"<a href='{n['link']}' target='_blank'>{n['title']}</a>"
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
        print(f"  [{cat}] {len(lst)}건")
