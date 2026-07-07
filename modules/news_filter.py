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
