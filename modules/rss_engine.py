# modules/rss_engine.py
# ============================================================
# BRN 2.0 RSS Engine
# Sprint 1-2
# 기존 news_pipeline.py 호환 버전
# ============================================================

from __future__ import annotations

from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any

import feedparser
import requests

from modules.config import (
    RSS_TIMEOUT,
    USER_AGENT,
)

from modules.logger import rss_logger

from modules.exceptions import (
    RSSFetchError,
    RSSParseError,
)


# ============================================================
# SESSION
# ============================================================

_SESSION = requests.Session()

_SESSION.headers.update(
    {
        "User-Agent": USER_AGENT,
        "Accept": (
            "application/rss+xml, "
            "application/atom+xml, "
            "application/xml, "
            "text/xml, "
            "*/*;q=0.8"
        ),
    }
)


# ============================================================
# DATETIME
# ============================================================

def _parse_datetime(
    entry: Any,
    now_kst: datetime | None = None,
) -> datetime | None:
    """
    RSS entry의 발행일을 datetime으로 변환한다.

    우선순위:
        published_parsed
        updated_parsed
        published
        updated
    """

    # --------------------------------------------------------
    # feedparser 구조화 시간
    # --------------------------------------------------------

    for field_name in (
        "published_parsed",
        "updated_parsed",
        "created_parsed",
    ):

        value = getattr(
            entry,
            field_name,
            None,
        )

        if value is None:
            continue

        try:

            dt = datetime(
                value.tm_year,
                value.tm_mon,
                value.tm_mday,
                value.tm_hour,
                value.tm_min,
                value.tm_sec,
            )

            if dt.tzinfo is None:

                if now_kst is not None:
                    dt = dt.replace(
                        tzinfo=now_kst.tzinfo
                    )

            return dt

        except Exception:
            continue

    # --------------------------------------------------------
    # 문자열 날짜
    # --------------------------------------------------------

    for field_name in (
        "published",
        "updated",
        "created",
    ):

        value = getattr(
            entry,
            field_name,
            None,
        )

        if not value:
            continue

        value = str(value).strip()

        # RFC 822 / RFC 2822
        try:

            dt = parsedate_to_datetime(
                value
            )

            if dt.tzinfo is None:

                if now_kst is not None:
                    dt = dt.replace(
                        tzinfo=now_kst.tzinfo
                    )

            return dt

        except Exception:
            pass

        # ISO 8601
        try:

            normalized = value.replace(
                "Z",
                "+00:00",
            )

            dt = datetime.fromisoformat(
                normalized
            )

            if dt.tzinfo is None:

                if now_kst is not None:
                    dt = dt.replace(
                        tzinfo=now_kst.tzinfo
                    )

            return dt

        except Exception:
            pass

    return None


# ============================================================
# TEXT
# ============================================================

def _clean_text(
    value: Any,
) -> str:

    if value is None:
        return ""

    text = str(value)

    replacements = {
        "\r": " ",
        "\n": " ",
        "\t": " ",
        "&nbsp;": " ",
        "&amp;": "&",
        "&quot;": '"',
        "&#39;": "'",
    }

    for old, new in replacements.items():

        text = text.replace(
            old,
            new,
        )

    return " ".join(
        text.split()
    ).strip()


# ============================================================
# URL
# ============================================================

def _get_link(
    entry: Any,
) -> str:

    link = getattr(
        entry,
        "link",
        "",
    )

    if link:
        return str(link).strip()

    links = getattr(
        entry,
        "links",
        [],
    )

    for item in links:

        if not isinstance(
            item,
            dict,
        ):
            continue

        href = item.get(
            "href"
        )

        if href:
            return str(
                href
            ).strip()

    return ""


# ============================================================
# ENTRY PARSE
# ============================================================

def _parse_entry(
    entry: Any,
    source: str,
    now_kst: datetime | None = None,
) -> tuple[
    datetime | None,
    str,
    str,
    str,
] | None:
    """
    BRN 기존 news_pipeline.py가 사용하는
    다음 구조로 반환한다.

        (
            pub_dt,
            title,
            link,
            source,
        )
    """

    title = _clean_text(
        getattr(
            entry,
            "title",
            "",
        )
    )

    if not title:
        return None

    link = _get_link(
        entry
    )

    if not link:
        return None

    pub_dt = _parse_datetime(
        entry,
        now_kst,
    )

    return (
        pub_dt,
        title,
        link,
        source,
    )


# ============================================================
# ENCODING
# ============================================================

def _decode_content(
    response: requests.Response,
    encoding_override: Any = None,
) -> bytes:

    content = response.content

    if encoding_override:

        encoding = str(
            encoding_override
        ).strip()

        if encoding:

            try:

                text = content.decode(
                    encoding,
                    errors="replace",
                )

                return text.encode(
                    "utf-8"
                )

            except Exception:

                pass

    return content


# ============================================================
# FETCH RSS
# ============================================================

def fetch_rss(
    name: str,
    url: str,
    eo: Any = None,
    now_kst: datetime | None = None,
) -> list[
    tuple[
        datetime | None,
        str,
        str,
        str,
    ]
]:
    """
    기존 news_pipeline.py 호환 RSS 수집 함수.

    호출 형식:

        fetch_rss(
            name,
            url,
            eo,
            now_kst,
        )

    반환:

        [
            (
                pub_dt,
                title,
                link,
                source,
            ),
            ...
        ]
    """

    result = []

    if not url:

        rss_logger.warning(
            "[RSS] %s : URL 없음",
            name,
        )

        return result

    rss_logger.info(
        "[RSS] %s 시작",
        name,
    )

    try:

        response = _SESSION.get(
            url,
            timeout=RSS_TIMEOUT,
        )

        response.raise_for_status()

    except Exception as exc:

        rss_logger.error(
            "[RSS] %s 요청 실패: %s",
            name,
            exc,
        )

        raise RSSFetchError(
            f"{name} RSS 다운로드 실패",
            cause=exc,
        ) from exc

    # --------------------------------------------------------
    # RSS 파싱
    # --------------------------------------------------------

    try:

        content = _decode_content(
            response,
            eo,
        )

        feed = feedparser.parse(
            content
        )

    except Exception as exc:

        rss_logger.error(
            "[RSS] %s 파싱 실패: %s",
            name,
            exc,
        )

        raise RSSParseError(
            f"{name} RSS 파싱 실패",
            cause=exc,
        ) from exc

    # --------------------------------------------------------
    # feedparser 오류 확인
    # --------------------------------------------------------

    bozo = getattr(
        feed,
        "bozo",
        False,
    )

    if bozo:

        bozo_exception = getattr(
            feed,
            "bozo_exception",
            None,
        )

        rss_logger.warning(
            "[RSS] %s 비정상 RSS: %s",
            name,
            bozo_exception,
        )

    # --------------------------------------------------------
    # ENTRY
    # --------------------------------------------------------

    entries = getattr(
        feed,
        "entries",
        [],
    )

    for entry in entries:

        try:

            item = _parse_entry(
                entry,
                name,
                now_kst,
            )

            if item is None:
                continue

            result.append(
                item
            )

        except Exception as exc:

            rss_logger.warning(
                "[RSS] %s 기사 파싱 실패: %s",
                name,
                exc,
            )

            continue

    # --------------------------------------------------------
    # 결과
    # --------------------------------------------------------

    rss_logger.info(
        "[RSS] %s 완료: %d건",
        name,
        len(result),
    )

    return result


# ============================================================
# MULTI FETCH
# ============================================================

def fetch_many(
    feeds: list,
    now_kst: datetime | None = None,
) -> list:

    all_entries = []

    for feed in feeds:

        if not feed:
            continue

        try:

            name = feed[0]

            url = feed[1]

            eo = (
                feed[2]
                if len(feed) > 2
                else None
            )

            all_entries.extend(
                fetch_rss(
                    name,
                    url,
                    eo,
                    now_kst,
                )
            )

        except Exception as exc:

            rss_logger.exception(
                "[RSS] 피드 처리 실패: %s",
                exc,
            )

    return all_entries


# ============================================================
# ENGINE
# ============================================================

class RSSEngine:
    """
    BRN RSS Engine

    기존 BRN 1.x 인터페이스와
    BRN 2.0 구조를 연결한다.
    """

    def fetch(
        self,
        name: str,
        url: str,
        eo: Any = None,
        now_kst: datetime | None = None,
    ) -> list:

        return fetch_rss(
            name,
            url,
            eo,
            now_kst,
        )

    def fetch_many(
        self,
        feeds: list,
        now_kst: datetime | None = None,
    ) -> list:

        return fetch_many(
            feeds,
            now_kst,
        )


# ============================================================
# SINGLETON
# ============================================================

_engine = RSSEngine()


# ============================================================
# EXPORT
# ============================================================

__all__ = [
    "RSSEngine",
    "fetch_rss",
    "fetch_many",
]
