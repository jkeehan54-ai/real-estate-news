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
