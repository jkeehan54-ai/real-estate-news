# modules/utils.py
# ============================================================
# BRN 2.0 Utility Functions
# Sprint 1-1
# ============================================================

from __future__ import annotations

import hashlib
import json
import random
import re
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

from .config import TIMEZONE


# ============================================================
# DATETIME
# ============================================================

def now() -> datetime:
    """
    현재 KST 시간
    """
    return datetime.now(TIMEZONE)


def today() -> str:
    """
    YYYY-MM-DD
    """
    return now().strftime("%Y-%m-%d")


def timestamp() -> str:
    """
    YYYYMMDD_HHMMSS
    """
    return now().strftime("%Y%m%d_%H%M%S")


def unix_timestamp() -> int:
    """
    Unix Timestamp
    """
    return int(time.time())


# ============================================================
# STRING
# ============================================================

_SPACE_RE = re.compile(r"\s+")
_TAG_RE = re.compile(r"<[^>]+>")


def clean_text(
    text: str | None,
) -> str:
    """
    HTML 제거 + 공백 정리
    """

    if not text:
        return ""

    text = _TAG_RE.sub(
        " ",
        text,
    )

    text = text.replace(
        "&nbsp;",
        " ",
    )

    text = text.replace(
        "&amp;",
        "&",
    )

    text = text.replace(
        "&quot;",
        '"',
    )

    text = text.replace(
        "&lt;",
        "<",
    )

    text = text.replace(
        "&gt;",
        ">",
    )

    text = _SPACE_RE.sub(
        " ",
        text,
    )

    return text.strip()


def normalize_space(
    text: str,
) -> str:

    return _SPACE_RE.sub(
        " ",
        text,
    ).strip()


def shorten(
    text: str,
    length: int = 120,
) -> str:

    text = clean_text(text)

    if len(text) <= length:
        return text

    return (
        text[: length - 3]
        + "..."
    )


def safe_str(
    value: Any,
) -> str:
    """
    어떤 객체라도 안전하게 문자열로 변환
    """

    try:
        return str(value)

    except Exception:
        return ""


def is_blank(
    value: Any,
) -> bool:
    """
    None 또는 공백 문자열 여부
    """

    if value is None:
        return True

    return safe_str(value).strip() == ""


def coalesce(
    *values: Any,
) -> Any:
    """
    첫 번째 유효한 값 반환
    """

    for value in values:

        if value is not None:
            return value

    return None


# ============================================================
# URL
# ============================================================

def domain(
    url: str,
) -> str:

    try:

        return urlparse(
            url
        ).netloc.lower()

    except Exception:

        return ""


def filename(
    path: str | Path,
) -> str:

    return Path(path).name


# ============================================================
# PATH
# ============================================================

def resolve(
    path: str | Path,
) -> Path:
    """
    절대경로 반환
    """

    return Path(
        path
    ).expanduser().resolve()


def ensure_dir(
    path: str | Path,
) -> Path:
    """
    디렉터리가 없으면 생성
    """

    path = Path(path)

    path.mkdir(
        parents=True,
        exist_ok=True,
    )

    return path


def ensure_parent(
    path: str | Path,
) -> Path:
    """
    부모 디렉터리 생성
    """

    path = Path(path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    return path


def file_exists(
    path: str | Path,
) -> bool:

    return Path(path).exists()


def remove_file(
    path: str | Path,
) -> None:

    path = Path(path)

    if path.exists():
        path.unlink()


def file_size(
    path: str | Path,
) -> int:

    path = Path(path)

    if not path.exists():
        return 0

    return path.stat().st_size


# ============================================================
# HASH
# ============================================================

def md5(
    value: str,
) -> str:

    return hashlib.md5(
        value.encode("utf-8")
    ).hexdigest()


def sha1(
    value: str,
) -> str:

    return hashlib.sha1(
        value.encode("utf-8")
    ).hexdigest()


def sha256(
    value: str,
) -> str:

    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


# ============================================================
# JSON
# ============================================================

def load_json(
    path: str | Path,
    default: Any = None,
) -> Any:

    path = Path(path)

    if not path.exists():
        return default

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as fp:

        return json.load(fp)


def save_json(
    path: str | Path,
    data: Any,
) -> None:

    path = Path(path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as fp:

        json.dump(
            data,
            fp,
            ensure_ascii=False,
            indent=2,
        )


# ============================================================
# LIST
# ============================================================

def unique(
    items: Iterable[Any],
) -> list[Any]:
    """
    순서를 유지한 중복 제거
    """

    return list(
        dict.fromkeys(items)
    )


def chunk(
    items: list[Any],
    size: int,
) -> list[list[Any]]:
    """
    리스트 분할
    """

    if size <= 0:
        raise ValueError(
            "size must be > 0"
        )

    return [
        items[i:i + size]
        for i in range(
            0,
            len(items),
            size,
        )
    ]


def flatten(
    items: Iterable[Iterable[Any]],
) -> list[Any]:

    result = []

    for group in items:

        result.extend(group)

    return result


# ============================================================
# DICTIONARY
# ============================================================

def merge_dict(
    left: dict,
    right: dict,
) -> dict:

    result = left.copy()

    result.update(right)

    return result


def remove_none(
    data: dict,
) -> dict:

    return {
        key: value
        for key, value in data.items()
        if value is not None
    }


# ============================================================
# NUMBER
# ============================================================

def clamp(
    value: float,
    minimum: float,
    maximum: float,
) -> float:

    return max(
        minimum,
        min(
            maximum,
            value,
        ),
    )


def percentage(
    value: float,
    digits: int = 2,
) -> str:

    return (
        f"{value:.{digits}f}%"
    )


def safe_int(
    value: Any,
    default: int = 0,
) -> int:

    try:
        return int(value)

    except Exception:
        return default


def safe_float(
    value: Any,
    default: float = 0.0,
) -> float:

    try:
        return float(value)

    except Exception:
        return default


# ============================================================
# BOOLEAN
# ============================================================

def to_bool(
    value: Any,
) -> bool:

    if isinstance(
        value,
        bool,
    ):
        return value

    if value is None:
        return False

    value = (
        str(value)
        .strip()
        .lower()
    )

    return value in {
        "1",
        "true",
        "yes",
        "y",
        "on",
    }


# ============================================================
# RANDOM
# ============================================================

def random_sleep(
    minimum: float = 0.5,
    maximum: float = 1.5,
) -> None:

    time.sleep(
        random.uniform(
            minimum,
            maximum,
        )
    )


# ============================================================
# DEBUG
# ============================================================

def dump(
    data: Any,
) -> None:
    """
    디버그 출력
    """

    print(data)


def dump_json(
    data: Any,
) -> None:
    """
    JSON Pretty Print
    """

    print(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        )
    )


def print_exception(
    exc: Exception,
) -> None:
    """
    Stack Trace 출력
    """

    traceback.print_exception(
        exc
    )


# ============================================================
# RETRY
# ============================================================

def retry(
    func,
    *,
    retries: int = 3,
    delay: float = 1.0,
):
    """
    간단한 재시도 실행
    """

    last_exception = None

    for _ in range(
        max(1, retries)
    ):

        try:

            return func()

        except Exception as exc:

            last_exception = exc

            if _ < retries - 1:

                time.sleep(
                    delay
                )

    if last_exception is not None:

        raise last_exception

    return None


# ============================================================
# EXPORT
# ============================================================

__all__ = [

    # Date
    "now",
    "today",
    "timestamp",
    "unix_timestamp",

    # Text
    "clean_text",
    "normalize_space",
    "shorten",
    "safe_str",
    "is_blank",
    "coalesce",

    # URL
    "domain",
    "filename",

    # Path
    "resolve",
    "ensure_dir",
    "ensure_parent",
    "file_exists",
    "remove_file",
    "file_size",

    # Hash
    "md5",
    "sha1",
    "sha256",

    # JSON
    "load_json",
    "save_json",

    # List
    "unique",
    "chunk",
    "flatten",

    # Dictionary
    "merge_dict",
    "remove_none",

    # Number
    "clamp",
    "percentage",
    "safe_int",
    "safe_float",

    # Boolean
    "to_bool",

    # Random
    "random_sleep",

    # Debug
    "dump",
    "dump_json",
    "print_exception",

    # Retry
    "retry",

]
