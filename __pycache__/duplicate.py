"""
duplicate.py
-----------------------------------------
제목 정규화 및 중복 기사 제거 모듈
BRN v2.0
"""

import re
from difflib import SequenceMatcher


# ────────────────────────────────────────
# 불용어
# ────────────────────────────────────────

STOPWORDS = {
    "은","는","이","가","을","를","의","에","도","와","과",
    "하고","으로","로","에서","까지","부터","이다","합니다",
    "입니다","했다","한다","됩니다","됐다","및","등","것",
    "안","돼","않다","이라고","라며","라고","하며","있다",
    "없다","하다","된다","한","더","또","위해","대해",
}


# ────────────────────────────────────────
# 지역명
# ────────────────────────────────────────

LOC_ENTITIES = {
    "수도권",
    "서울",
    "강남",
    "강북",
    "경기",
    "인천",
    "부산",
    "대구",
    "광주",
    "대전",
    "울산",
    "세종",
    "경남",
    "해운대",
    "수영",
    "사하",
    "동래",
    "기장",
    "연제",
    "금정",
}


# ────────────────────────────────────────
# 기관명
# ────────────────────────────────────────

ORG_ENTITIES = {
    "국세청",
    "한국부동산원",
    "국토부",
    "금융위",
    "금감원",
    "LH",
    "SH",
    "HUG",
}


# ────────────────────────────────────────
# 제목 정규화
# ────────────────────────────────────────

def normalize(title: str) -> str:

    title = re.split(r"\s[-|]\s", title)[0].strip()

    title = re.sub(r"^\[.*?\]\s*", "", title)

    title = re.sub(
        r"\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}",
        "",
        title,
    )

    title = re.sub(r"[^\w\s]", " ", title)

    title = re.sub(
        r"(?<!\w)[\u4e00-\u9fff](?!\w)",
        "",
        title,
    )

    title = re.sub(r"\s+", " ", title)

    return title.strip()


# ────────────────────────────────────────
# 키워드 추출
# ────────────────────────────────────────

def keywords(title: str) -> set:

    return {
        w
        for w in normalize(title).split()
        if w not in STOPWORDS
        and len(w) >= 2
    }


# ────────────────────────────────────────
# 엔티티 추출
# ────────────────────────────────────────

def extract_entities(title: str) -> set:

    t = re.sub(r"[^\w\s]", " ", str(title))

    ents = set()

    for m in re.finditer(
        r"\d+\.?\d*\s*(?:억|만|건|%|개월|층|평|채|명|가구)",
        t,
    ):
        ents.add(m.group().strip())

    for loc in LOC_ENTITIES:
        if loc in t:
            ents.add(loc)

    for org in ORG_ENTITIES:
        if org in t:
            ents.add(org)

    return ents


# ────────────────────────────────────────
# 중복 기사 판단
# ────────────────────────────────────────

def is_duplicate(new_title: str, seen_titles: list) -> bool:

    nn = normalize(new_title)

    kn = keywords(new_title)

    en = extract_entities(new_title)

    for old in seen_titles:

        no = normalize(old)

        # 1단계 문자열 유사도
        if SequenceMatcher(None, nn, no).ratio() >= 0.72:
            return True

        # 2단계 키워드 자카드
        ko = keywords(old)

        union = len(kn | ko)

        if union and len(kn & ko) / union >= 0.55:
            return True

        # 3단계 엔티티 비교
        eo = extract_entities(old)

        if en and eo and len(en & eo) >= 2:
            return True

    return False
