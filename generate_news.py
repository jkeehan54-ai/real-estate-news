import feedparser
from urllib.parse import quote_plus
from difflib import SequenceMatcher
from datetime import datetime, timezone, timedelta
import re

# ── 한국 시간대 (KST = UTC+9) ─────────────────────────────────────────────────
KST = timezone(timedelta(hours=9))

# ── 13개 매체 ─────────────────────────────────────────────────────────────────
SOURCES = {
    "조선일보": "https://www.chosun.com/economy/real_estate/",
    "중앙일보": "https://www.joongang.co.kr/realestate",
    "동아일보": "https://www.donga.com/news/Economy/Realestate",
    "한겨레": "https://www.hani.co.kr/arti/economy/property/",
    "매일경제": "https://www.mk.co.kr/news/realestate/",
    "한국경제": "https://www.hankyung.com/realestate",
    "부산일보": "https://www.busan.com/economy/",
    "국제신문": "http://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0200",
    "네이버부동산": "https://land.naver.com/news/",
    "한국부동산원": "https://www.reb.or.kr/reb/main.do",
    "KB부동산": "https://kbland.kr/today",
    "머니투데이": "https://news.mt.co.kr/estate/",
    "연합뉴스": "https://www.yna.co.kr/economy/real-estate/",
}

# ── 설정 및 유틸 함수 ──────────────────────────────────────────────────────────
STOPWORDS = {"은","는","이","가","을","를","의","에","도","와","과","하고","으로","로","에서","까지","부터","이다","합니다","입니다","했다","한다","됩니다","됐다","및","등","것","안","돼","안돼","반드시","이제","탈출","공화국","않다","이라고","라며","했으며","라고","하며","대해","위해","한다","있다","없다","하다","된다","한","더","또","위","아래","앞","뒤","속","간","전","후"}
LOC_ENTITIES = {"수도권","서울","강남","강북","강동","강서","부산","경기","인천","대구","광주","대전","울산","세종","제주","경남","경북","전남","전북","충남","충북","강원","용산","마포","송파","성동","노원","은평","영등포"}
ORG_ENTITIES = {"국세청","당근부동산","한국부동산원","법원","국토부","금융위","금감원","LH","SH","HUG","주택도시보증공사"}

def normalize(title: str) -> str:
    title = re.split(r'\s[-|]\s', title)[0].strip()
    title = re.sub(r'^\[.*?\]\s*', '', title)
    title = re.sub(r'\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}', '', title)
    title = re.sub(r'[^\w\s]', ' ', title)
    title = re.sub(r'(?<!\w)[一-龥](?!\w)', '', title)
    return re.sub(r'\s+', ' ', title).strip()

def keywords(title: str) -> set:
    return {w for w in normalize(title).split() if w not in STOPWORDS and len(w) >= 2}

def extract_entities(title: str) -> set:
    t = re.sub(r'[^\w\s]', ' ', title)
    ents = set()
    for m in re.finditer(r'\d+\.?\d*\s*(?:억|만|천|백|건|%|개월|곳|층|평|㎡|채|명|가구|세대)', t):
        ents.add(m.group().strip())
    for loc in LOC_ENTITIES:
        if loc in t: ents.add(loc)
    for org in ORG_ENTITIES:
        if org in t: ents.add(org)
    return ents

def is_duplicate(new_raw: str, seen_raw: list, sim_thr=0.65, kw_thr=0.45, ent_thr=2) -> bool:
    norm_new, kw_new, ent_new = normalize(new_raw), keywords(new_raw), extract_entities(new_raw)
    for seen in seen_raw:
        norm_s = normalize(seen)
        if SequenceMatcher(None, norm_new, norm_s).ratio() >= sim_thr: return True
        kw_s = keywords(seen)
        union = len(kw_new | kw_s)
        if union and len(kw_new & kw_s) / union >= kw_thr: return True
        ent_s = extract_entities(seen)
        if ent_new and ent_s and len(ent_new & ent_s) >= ent_thr: return True
    return False

# ── 뉴스 수집 (오늘 날짜 필터링) ─────────────────────────────────────────────
def get_clean_news() -> dict:
    results = {"청약": [], "재건축": [], "세제": [], "정책": [], "시장동향": []}
    seen_raw = []
    today = datetime.now(KST).date()
    
    queries = ["부동산 청약", "아파트 재건축 재개발", "부동산 세금 종부세", "부동산 정책 대출", "부동산 시장 동향"]
    for q in queries:
        url = f"https://news.google.com/rss/search?q={quote_plus(q)}&hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(url)
        for entry in feed.entries:
            pub_dt = None
            if 'published_parsed' in entry:
                pub_dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).astimezone(KST).date()
            
            # [날짜 필터] 오늘 날짜가 아니면 제외
            if pub_dt and pub_dt != today: continue
            
            if is_duplicate(entry.title, seen_raw): continue
            
            t = normalize(entry.title).lower()
            if any(k in t for k in ["분양","청약"]): cat = "청약"
            elif any(k in t for k in ["재건축","재개발"]): cat = "재건축"
            elif any(k in t for k in ["세금","종부세","취득세"]): cat = "세제"
            elif any(k in t for k in ["정부","대출","금리","정책"]): cat = "정책"
            else: cat = "시장동향"

            if len(results[cat]) < 10:
                results[cat].append({
                    "title": normalize(entry.title),
                    "link": entry.link,
                    "src": entry.source.title if hasattr(entry, "source") else "뉴스"
                })
                seen_raw.append(entry.title)
    return results

# ── HTML 생성 ─────────────────────────────────────────────────────────────────
def build_html(data: dict) -> str:
    today_str = datetime.now(KST).strftime("%Y년 %m월 %d일")
    html = f"<h1>🏠 부동산 뉴스 브리핑 ({today_str})</h1>\n"
    html += " | ".join(f'<a href="{u}" target="_blank">{n}</a>' for n, u in SOURCES.items())
    html += "\n<h2>오늘의 핵심 브리핑</h2><p>실시간 부동산 시장 주요 뉴스입니다.</p>"
    for cat, lst in data.items():
        html += f"<h2>[{cat}]</h2>"
        html += "".join(f"<p><a href='{n['link']}' target='_blank'>{n['title']}</a> | {n['src']}</p>" for n in lst) if lst else "<p>오늘 수집된 기사가 없습니다.</p>"
    return html

if __name__ == "__main__":
    data = get_clean_news()
    with open("index.html", "w", encoding="utf-8") as f: f.write(build_html(data))
    print("[완료] index.html이 성공적으로 생성되었습니다.")
