# news_filter.py
import re
from difflib import SequenceMatcher

from modules.news_config import (
    RE_ESTATE,
    RE_EXCLUDE,
    RE_MARKET_REQUIRED,
    STOPWORDS,
    LOC_ENTITIES,
    ORG_ENTITIES,
)

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



