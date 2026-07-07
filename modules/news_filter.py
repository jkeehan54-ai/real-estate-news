# modules/news_filter.py

import re
from difflib import SequenceMatcher


def normalize(title: str) -> str:
    """기사 제목 정규화"""
    title = re.split(r"\s[-|]\s", title)[0].strip()
    title = re.sub(r"^\[.*?\]\s*", "", title)
    title = re.sub(r"\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}", "", title)
    title = re.sub(r"[^\w\s]", " ", title)
    title = re.sub(r"(?<!\w)[\u4e00-\u9fff](?!\w)", "", title)
    return re.sub(r"\s+", " ", title).strip()


def keywords(title: str, stopwords: set) -> set:
    """제목에서 핵심 키워드 추출"""
    return {
        word
        for word in normalize(title).split()
        if len(word) >= 2 and word not in stopwords
    }


def extract_entities(title: str,
                     locations: set,
                     organizations: set) -> set:
    """숫자·지역·기관명 추출"""

    text = re.sub(r"[^\w\s]", " ", str(title))

    entities = set()

    for m in re.finditer(
        r"\d+\.?\d*\s*(?:억|만|건|%|개월|층|평|채|명|가구)",
        text,
    ):
        entities.add(m.group().strip())

    for loc in locations:
        if loc in text:
            entities.add(loc)

    for org in organizations:
        if org in text:
            entities.add(org)

    return entities

def is_duplicate(
    new_title: str,
    seen_titles: list,
    stopwords: set,
    locations: set,
    organizations: set,
) -> bool:
    """
    3단계 중복 판별

    1. 문자열 유사도
    2. 키워드 자카드
    3. 엔티티 비교
    """

    new_normal = normalize(new_title)
    new_keywords = keywords(new_title, stopwords)
    new_entities = extract_entities(
        new_title,
        locations,
        organizations,
    )

    for title in seen_titles:

        old_normal = normalize(title)

        if SequenceMatcher(
            None,
            new_normal,
            old_normal,
        ).ratio() >= 0.72:
            return True

        old_keywords = keywords(
            title,
            stopwords,
        )

        union = len(new_keywords | old_keywords)

        if union:

            score = len(
                new_keywords & old_keywords
            ) / union

            if score >= 0.55:
                return True

        old_entities = extract_entities(
            title,
            locations,
            organizations,
        )

        if (
            new_entities
            and old_entities
            and len(new_entities & old_entities) >= 2
        ):
            return True

    return False


def is_estate_related(title, re_estate, re_exclude):
    """
    부동산 기사 여부
    """

    if re_exclude.search(title):
        return False

    return bool(re_estate.search(title))


def is_market_valid(
    title,
    re_market_required,
    re_exclude,
):
    """
    시장동향 기사 2차 검증
    """

    if re_exclude.search(title):
        return False

    return bool(
        re_market_required.search(title)
    )


def classify(title: str) -> str:
    """
    기사 카테고리 분류
    """

    t = normalize(title)

    if any(
        k in t
        for k in [
            "청약",
            "무순위",
            "청약통장",
            "특별공급",
            "일반공급",
        ]
    ):
        return "청약"

    if any(
        k in t
        for k in [
            "재건축",
            "재개발",
            "정비사업",
            "가로주택",
            "리모델링",
        ]
    ):
        return "재건축"

    if any(
        k in t
        for k in [
            "종부세",
            "취득세",
            "양도세",
            "재산세",
            "세금",
            "세제",
            "공시가",
        ]
    ):
        return "세제"

    if any(
        k in t
        for k in [
            "대출",
            "금리",
            "정책",
            "규제",
            "완화",
            "DSR",
            "LTV",
            "DTI",
            "주담대",
            "전세대출",
        ]
    ):
        return "정책"

    if any(
        k in t
        for k in [
            "신도시",
            "공공주택",
            "착공",
            "준공",
            "용적률",
            "복합개발",
            "도시개발",
            "택지",
        ]
    ):
        return "공급개발"

    if any(
        k in t
        for k in [
            "부산",
            "해운대",
            "수영구",
            "동래",
            "센텀",
            "광안",
            "명지",
            "에코델타",
            "오시리아",
            "기장",
            "창원",
            "김해",
            "양산",
            "경남",
            "울산",
        ]
    ):
        return "부산경남"

    return "시장동향"
