"""
부동산 뉴스 브리핑 - 24시간 필터 + 3단계 중복 제거
────────────────────────────────────────────────────
날짜 판단 우선순위:
  1순위: 기사 URL 경로의 /YYYY/MM/DD/ 패턴  ← 가장 신뢰도 높음
  2순위: RSS published_parsed (UTC→KST 변환)
  3순위: 날짜 불명 → 포함 처리

설치: pip install feedparser requests
"""

import feedparser
import requests
from urllib.parse import quote_plus
from difflib import SequenceMatcher
from datetime import datetime, timezone, timedelta
import re

KST = timezone(timedelta(hours=9))

# ── 13개 매체 ─────────────────────────────────────────────────────────────────
SOURCES = {
    "조선일보":    "https://www.chosun.com/economy/real_estate/",
    "중앙일보":    "https://www.joongang.co.kr/realestate",
    "동아일보":    "https://www.donga.com/news/Economy/Realestate",
    "한겨레":      "https://www.hani.co.kr/arti/economy/property/",
    "매일경제":    "https://www.mk.co.kr/news/realestate/",
    "한국경제":    "https://www.hankyung.com/realestate",
    "부산일보":    "https://www.busan.com/economy/",
    "국제신문":    "http://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0200",
    "네이버부동산": "https://land.naver.com/news/",
    "한국부동산원": "https://www.reb.or.kr/reb/main.do",
    "KB부동산":    "https://kbland.kr/today",
    "머니투데이":  "https://news.mt.co.kr/estate/",
    "연합뉴스":    "https://www.yna.co.kr/economy/real-estate/",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
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
    "수도권","서울","강남","강북","강동","강서","부산","경기","인천","대구",
    "광주","대전","울산","세종","제주","경남","경북","전남","전북","충남",
    "충북","강원","용산","마포","송파","성동","노원","은평","영등포",
}
ORG_ENTITIES = {
    "국세청","당근부동산","한국부동산원","법원","국토부","금융위","금감원",
    "LH","SH","HUG","주택도시보증공사",
}

# ── 날짜 추출 (2단계 우선순위) ────────────────────────────────────────────────
def extract_date_from_url(url: str) -> datetime | None:
    """
    URL 경로의 /YYYY/MM/DD/ 패턴에서 날짜 추출.
    조선일보·동아일보·한겨레 등 날짜 경로 포함 매체에 유효.
    시각 정보가 없으므로 해당일 06:00 KST로 설정 (보수적 기준).
    """
    m = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', url)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return datetime(y, mo, d, 6, 0, tzinfo=KST)
        except ValueError:
            return None
    return None

def get_best_pub_dt(entry) -> datetime | None:
    """
    1순위: URL에서 날짜 추출
    2순위: published_parsed (UTC→KST)
    없으면: None
    """
    # 1순위: URL 날짜
    url_dt = extract_date_from_url(getattr(entry, 'link', ''))
    if url_dt:
        return url_dt

    # 2순위: published_parsed
    pub = entry.get("published_parsed")
    if pub:
        return datetime(*pub[:6], tzinfo=timezone.utc).astimezone(KST)

    return None

def is_within_24h(entry, now_kst: datetime) -> bool:
    """
    발행일 기준 24시간 이내 → True.
    날짜 판단 불가 → True (포함 처리).
    """
    pub_dt = get_best_pub_dt(entry)
    if pub_dt is None:
        return True
    return (now_kst - pub_dt).total_seconds() <= 86400   # 24h

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

# ── 뉴스 수집 ─────────────────────────────────────────────────────────────────
def get_clean_news() -> dict:
    results  = {"청약": [], "재건축": [], "세제": [], "정책": [], "시장동향": []}
    seen_raw = []
    now_kst  = datetime.now(KST)

    queries = [
        "부동산 청약",
        "아파트 재건축 재개발",
        "부동산 세금 종부세",
        "부동산 정책 대출",
        "부동산 시장 동향",
    ]

    # 모든 entry 수집
    all_entries = []
    for q in queries:
        url  = f"https://news.google.com/rss/search?q={quote_plus(q)}&hl=ko&gl=KR&ceid=KR:ko"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=8)
            feed = feedparser.parse(resp.content)
        except Exception:
            feed = feedparser.parse(url)   # fallback
        for entry in feed.entries:
            pub_dt = get_best_pub_dt(entry)
            all_entries.append((pub_dt, entry))

    # 최신순 정렬
    all_entries.sort(
        key=lambda x: x[0] or datetime.max.replace(tzinfo=KST),
        reverse=True
    )

    total = skipped = dropped = 0
    for pub_dt, entry in all_entries:
        total += 1

        # 24시간 필터 (URL 날짜 우선 사용)
        if not is_within_24h(entry, now_kst):
            skipped += 1
            continue

        raw = entry.title
        if is_duplicate(raw, seen_raw):
            dropped += 1
            continue

        t = normalize(raw).lower()
        if   any(k in t for k in ["분양","청약"]):              cat = "청약"
        elif any(k in t for k in ["재건축","재개발"]):           cat = "재건축"
        elif any(k in t for k in ["세금","종부세","취득세"]):     cat = "세제"
        elif any(k in t for k in ["정부","대출","금리","정책"]):  cat = "정책"
        else:                                                   cat = "시장동향"

        if len(results[cat]) < 10:
            src = (entry.source.title
                   if hasattr(entry, "source") and hasattr(entry.source, "title")
                   else "뉴스")
            # 표시 시각: URL 날짜면 날짜만, published면 시각 포함
            url_dt = extract_date_from_url(getattr(entry, 'link', ''))
            if url_dt:
                pub_str = url_dt.strftime("%m/%d")
            elif pub_dt:
                pub_str = pub_dt.strftime("%m/%d %H:%M")
            else:
                pub_str = ""

            results[cat].append({
                "title":   normalize(raw),
                "link":    entry.link,
                "src":     src,
                "pub_str": pub_str,
            })
            seen_raw.append(raw)

    kept = total - skipped - dropped
    print(f"[완료] 전체 {total}건 | 24h 제외 {skipped}건 | 중복 제거 {dropped}건 | 최종 {kept}건")
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

    for cat, lst in data.items():
        html += f"<h2>[{cat}]</h2>"
        if lst:
            html += "".join(
                f"<p>"
                f"<a href='{n['link']}' target='_blank'>{n['title']}</a>"
                f" | {n['src']}"
                + (f" <small style='color:#aaa'>({n['pub_str']})</small>" if n['pub_str'] else "")
                + "</p>"
                for n in lst
            )
        else:
            html += "<p>최근 24시간 내 수집된 기사가 없습니다.</p>"
    return html

if __name__ == "__main__":
    data = get_clean_news()
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(build_html(data))
    print("[완료] index.html 생성 완료")
