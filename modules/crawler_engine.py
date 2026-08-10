# modules/crawler_engine.py
# ============================================================
# BRN 2.0 Crawler Engine
# Sprint 1-2
# 기존 news_pipeline.py 호환 버전
# ============================================================

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from modules.config import (
    HTTP_TIMEOUT,
    USER_AGENT,
)

from modules.exceptions import (
    CrawlerError,
    HTMLParseError,
)

from modules.logger import main_logger

from modules.utils import clean_text


# ============================================================
# SESSION
# ============================================================

_SESSION = requests.Session()

_SESSION.headers.update(
    {
        "User-Agent": USER_AGENT,
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,*/*;q=0.8"
        ),
        "Accept-Language": (
            "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
        ),
    }
)


# ============================================================
# BASE ENGINE
# ============================================================

class CrawlerEngine:
    """
    BRN 기본 HTML Crawler
    """

    def __init__(
        self,
        timeout: int = HTTP_TIMEOUT,
    ):

        self.timeout = timeout

    # --------------------------------------------------------
    # REQUEST
    # --------------------------------------------------------

    def get(
        self,
        url: str,
    ) -> BeautifulSoup:

        if not url:
            raise CrawlerError(
                "Crawler URL이 없습니다."
            )

        try:

            response = _SESSION.get(
                url,
                timeout=self.timeout,
            )

            response.raise_for_status()

        except Exception as exc:

            raise CrawlerError(
                f"페이지 요청 실패: {url}",
                cause=exc,
            ) from exc

        try:

            return BeautifulSoup(
                response.content,
                "html.parser",
            )

        except Exception as exc:

            raise HTMLParseError(
                f"HTML 파싱 실패: {url}",
                cause=exc,
            ) from exc

    # --------------------------------------------------------
    # CRAWL
    # --------------------------------------------------------

    def crawl(
        self,
        url: str,
        parser: Callable,
        now_kst: datetime | None = None,
    ) -> list:

        soup = self.get(
            url
        )

        try:

            result = parser(
                soup,
                now_kst,
            )

        except TypeError:

            result = parser(
                soup
            )

        main_logger.info(
            "[Crawler] %s -> %d건",
            url,
            len(result),
        )

        return result

    # --------------------------------------------------------
    # ARTICLE
    # --------------------------------------------------------

    @staticmethod
    def article(
        pub_dt: datetime | None,
        title: str,
        link: str,
        source: str,
    ) -> tuple:

        return (
            pub_dt,
            clean_text(title),
            link,
            source,
        )


# ============================================================
# DATE PARSER
# ============================================================

def _parse_datetime(
    value: Any,
    now_kst: datetime | None = None,
) -> datetime | None:

    if isinstance(
        value,
        datetime,
    ):

        if (
            value.tzinfo is None
            and now_kst is not None
        ):

            return value.replace(
                tzinfo=now_kst.tzinfo
            )

        return value

    if not value:
        return now_kst

    value = str(value).strip()

    formats = [

        "%Y-%m-%d %H:%M:%S",

        "%Y-%m-%d %H:%M",

        "%Y.%m.%d %H:%M:%S",

        "%Y.%m.%d %H:%M",

        "%Y-%m-%d",

        "%Y.%m.%d",

        "%m/%d %H:%M",

    ]

    for fmt in formats:

        try:

            dt = datetime.strptime(
                value,
                fmt,
            )

            if dt.tzinfo is None:

                if now_kst is not None:
                    dt = dt.replace(
                        tzinfo=now_kst.tzinfo
                    )

            return dt

        except ValueError:
            continue

    return now_kst


# ============================================================
# LINK
# ============================================================

def _absolute_url(
    base_url: str,
    href: str | None,
) -> str:

    if not href:
        return ""

    return urljoin(
        base_url,
        href,
    )


# ============================================================
# GENERIC ARTICLE EXTRACTION
# ============================================================

def _extract_title(
    tag,
) -> str:

    if tag is None:
        return ""

    return clean_text(
        tag.get_text(
            " ",
            strip=True,
        )
    )


def _extract_links(
    soup: BeautifulSoup,
    base_url: str,
    source: str,
    keyword: str | None = None,
    now_kst: datetime | None = None,
) -> list:

    result = []

    seen = set()

    for tag in soup.select("a"):

        title = _extract_title(
            tag
        )

        href = tag.get(
            "href"
        )

        if not title:
            continue

        if not href:
            continue

        link = _absolute_url(
            base_url,
            href,
        )

        if not link:
            continue

        if keyword:

            if keyword.lower() not in link.lower():

                continue

        if link in seen:
            continue

        seen.add(link)

        result.append(
            CrawlerEngine.article(
                now_kst,
                title,
                link,
                source,
            )
        )

    return result


# ============================================================
# BUSAN ILBO
# ============================================================

def parse_busan(
    soup: BeautifulSoup,
    now_kst: datetime | None = None,
) -> list:

    result = []

    base_url = (
        "https://www.busan.com/"
    )

    seen = set()

    # --------------------------------------------------------
    # 우선 일반 기사 링크
    # --------------------------------------------------------

    selectors = [

        "a[href*='/news/']",

        "a[href*='/article/']",

        "a[href*='newsView']",

    ]

    for selector in selectors:

        for tag in soup.select(
            selector
        ):

            title = _extract_title(
                tag
            )

            href = tag.get(
                "href"
            )

            if not title or not href:
                continue

            link = _absolute_url(
                base_url,
                href,
            )

            if not link:
                continue

            if link in seen:
                continue

            seen.add(link)

            result.append(
                CrawlerEngine.article(
                    now_kst,
                    title,
                    link,
                    "부산일보",
                )
            )

    return result


# ============================================================
# KOOKJE SHINMUN
# ============================================================

def parse_kookje(
    soup: BeautifulSoup,
    now_kst: datetime | None = None,
) -> list:

    result = []

    base_url = (
        "https://www.kookje.co.kr/"
    )

    seen = set()

    selectors = [

        "a[href*='/news/']",

        "a[href*='/article/']",

        "a[href*='news_']",

    ]

    for selector in selectors:

        for tag in soup.select(
            selector
        ):

            title = _extract_title(
                tag
            )

            href = tag.get(
                "href"
            )

            if not title or not href:
                continue

            link = _absolute_url(
                base_url,
                href,
            )

            if not link:
                continue

            if link in seen:
                continue

            seen.add(link)

            result.append(
                CrawlerEngine.article(
                    now_kst,
                    title,
                    link,
                    "국제신문",
                )
            )

    return result


# ============================================================
# NAVER LAND
# ============================================================

def parse_naver_land(
    soup: BeautifulSoup,
    now_kst: datetime | None = None,
) -> list:

    result = []

    base_url = (
        "https://land.naver.com/"
    )

    seen = set()

    selectors = [

        "a[href*='news']",

        "a[href*='article']",

    ]

    for selector in selectors:

        for tag in soup.select(
            selector
        ):

            title = _extract_title(
                tag
            )

            href = tag.get(
                "href"
            )

            if not title or not href:
                continue

            link = _absolute_url(
                base_url,
                href,
            )

            if not link:
                continue

            if link in seen:
                continue

            seen.add(link)

            result.append(
                CrawlerEngine.article(
                    now_kst,
                    title,
                    link,
                    "네이버부동산",
                )
            )

    return result


# ============================================================
# ENGINE
# ============================================================

_engine = CrawlerEngine()


# ============================================================
# BUSAN
# ============================================================

def scrape_busan(
    now_kst: datetime | None = None,
) -> list:

    url = (
        "https://www.busan.com/"
    )

    try:

        result = _engine.crawl(
            url,
            parse_busan,
            now_kst,
        )

        main_logger.info(
            "[부산일보] %d건",
            len(result),
        )

        return result

    except Exception as exc:

        main_logger.exception(
            "[부산일보] 수집 실패: %s",
            exc,
        )

        return []


# ============================================================
# KOOKJE
# ============================================================

def scrape_kookje(
    now_kst: datetime | None = None,
) -> list:

    url = (
        "https://www.kookje.co.kr/"
    )

    try:

        result = _engine.crawl(
            url,
            parse_kookje,
            now_kst,
        )

        main_logger.info(
            "[국제신문] %d건",
            len(result),
        )

        return result

    except Exception as exc:

        main_logger.exception(
            "[국제신문] 수집 실패: %s",
            exc,
        )

        return []


# ============================================================
# NAVER LAND
# ============================================================

def scrape_naver_land(
    now_kst: datetime | None = None,
) -> list:

    url = (
        "https://land.naver.com/"
    )

    try:

        result = _engine.crawl(
            url,
            parse_naver_land,
            now_kst,
        )

        main_logger.info(
            "[네이버부동산] %d건",
            len(result),
        )

        return result

    except Exception as exc:

        main_logger.exception(
            "[네이버부동산] 수집 실패: %s",
            exc,
        )

        return []


# ============================================================
# CRAWL ALL
# ============================================================

def crawl_all(
    now_kst: datetime | None = None,
) -> list:

    result = []

    result.extend(
        scrape_busan(
            now_kst
        )
    )

    result.extend(
        scrape_kookje(
            now_kst
        )
    )

    result.extend(
        scrape_naver_land(
            now_kst
        )
    )

    return result


# ============================================================
# HEALTH CHECK
# ============================================================

def health_check() -> dict:

    result = {}

    crawlers = {

        "부산일보": scrape_busan,

        "국제신문": scrape_kookje,

        "네이버부동산":
            scrape_naver_land,

    }

    for name, crawler in crawlers.items():

        try:

            items = crawler()

            result[name] = {

                "success": True,

                "count": len(items),

            }

        except Exception as exc:

            result[name] = {

                "success": False,

                "count": 0,

                "error": str(exc),

            }

    return result


# ============================================================
# EXPORT
# ============================================================

__all__ = [

    "CrawlerEngine",

    "parse_busan",

    "parse_kookje",

    "parse_naver_land",

    "scrape_busan",

    "scrape_kookje",

    "scrape_naver_land",

    "crawl_all",

    "health_check",

]
