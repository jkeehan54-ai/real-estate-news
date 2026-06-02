import feedparser
from urllib.parse import quote_plus
from difflib import SequenceMatcher
from datetime import datetime, timezone, timedelta
import re

# ── 한국 시간대 ───────────────────────────────────────────────────────────────
KST = timezone(timedelta(hours=9))

# (SOURCES, STOPWORDS, LOC_ENTITIES, ORG_ENTITIES, normalize, keywords, extract_entities, is_duplicate 함수는 이전과 동일하게 유지)
# ... (상단 설정 및 함수 부분은 그대로 두세요) ...

# ── 뉴스 수집 ─────────────────────────────────────────────────────────────────
def get_clean_news() -> dict:
    results = {"청약": [], "재건축": [], "세제": [], "정책": [], "시장동향": []}
    seen_raw = []
    today = datetime.now(KST).date() # 오늘 날짜

    queries = ["부동산 청약", "아파트 재건축 재개발", "부동산 세금 종부세", "부동산 정책 대출", "부동산 시장 동향"]

    for q in queries:
        url = f"https://news.google.com/rss/search?q={quote_plus(q)}&hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(url)
        for entry in feed.entries:
            # 날짜 파싱 (KST 기준)
            pub_dt = None
            if 'published_parsed' in entry:
                pub_dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).astimezone(KST).date()
            
            # [수정] 오늘 날짜인 경우에만 통과 (날짜 정보가 없는 경우 최신으로 간주하여 포함)
            if pub_dt and pub_dt != today:
                continue
            
            raw = entry.title
            if is_duplicate(raw, seen_raw): continue

            t = normalize(raw).lower()
            if any(k in t for k in ["분양","청약"]): cat = "청약"
            elif any(k in t for k in ["재건축","재개발"]): cat = "재건축"
            elif any(k in t for k in ["세금","종부세","취득세"]): cat = "세제"
            elif any(k in t for k in ["정부","대출","금리","정책"]): cat = "정책"
            else: cat = "시장동향"

            if len(results[cat]) < 10:
                results[cat].append({
                    "title": normalize(raw),
                    "link": entry.link,
                    "src": entry.source.title if hasattr(entry, "source") else "뉴스"
                })
                seen_raw.append(raw)
    return results

# ── HTML 생성 ─────────────────────────────────────────────────────────────────
# (build_html 함수 및 __main__ 실행 부분은 이전과 동일하게 유지하세요)
