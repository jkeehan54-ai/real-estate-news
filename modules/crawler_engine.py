# modules/crawler_engine.py
# ============================================================
# BRN 2.0 Crawler Engine
# Sprint 1-2
#
# 기존 news_pipeline.py 호환
#
# 반환 형식:
#     (
#         pub_dt,
#         title,
#         link,
#         source,
#     )
#
# 주요 복구
#   1. 부산일보
#   2. 국제신문
#   3. 네이버부동산
#   4. GitHub Actions timeout 대응
#   5. 기존 now_kst 인자 호환
# ============================================================

from __future__ import annotations

from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any
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
            "text/html,"
            "application/xhtml+xml,"
            "application/xml;q=0.9,"
            "*/*;q=0.8"
        ),
        "Accept-Language": (
            "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
        ),
        "Cache-Control": "no-cache",
    }
)


# ============================================================
# REQUEST TIMEOUT
# ============================================================

CRAWLER_TIMEOUT = min(
    int(HTTP_TIMEOUT),
    15,
)


# ============================================================
# COMMON
# ============================================================

def _request(
    url: str,
    *,
    timeout: int = CRAWLER_TIMEOUT,
) -> requests.Response:

    response = _SESSION.get(
        url,
        timeout=timeout,
        allow_redirects=True,
    )

    response.raise_for_status()

    return response


def _soup(
    response: requests.Response,
) -> BeautifulSoup:

    try:

        return BeautifulSoup(
            response.content,
            "html.parser",
        )

    except Exception as exc:

        raise HTMLParseError(
            "HTML 파싱 실패",
            cause=exc,
        ) from exc


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


def _title(
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


def _article(
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
# DATE
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

    text = str(
        value
    ).strip()

    # --------------------------------------------------------
    # RFC 822
    # --------------------------------------------------------

    try:

        dt = parsedate_to_datetime(
            text
        )

        if (
            dt.tzinfo is None
            and now_kst is not None
        ):

            dt = dt.replace(
                tzinfo=now_kst.tzinfo
            )

        return dt

    except Exception:
        pass

    # --------------------------------------------------------
    # ISO
    # --------------------------------------------------------

    try:

        dt = datetime.fromisoformat(
            text.replace(
                "Z",
                "+00:00",
            )
        )

        if (
            dt.tzinfo is None
            and now_kst is not None
        ):

            dt = dt.replace(
                tzinfo=now_kst.tzinfo
            )

        return dt

    except Exception:
        pass

    # --------------------------------------------------------
    # 일반 한국 날짜
    # --------------------------------------------------------

    formats = [

        "%Y-%m-%d %H:%M:%S",

        "%Y-%m-%d %H:%M",

        "%Y.%m.%d %H:%M:%S",

        "%Y.%m.%d %H:%M",

        "%Y/%m/%d %H:%M:%S",

        "%Y/%m/%d %H:%M",

        "%Y년 %m월 %d일 %H:%M",

    ]

    for fmt in formats:

        try:

            dt = datetime.strptime(
                text,
                fmt,
            )

            if (
                dt.tzinfo is None
                and now_kst is not None
            ):

                dt = dt.replace(
                    tzinfo=now_kst.tzinfo
                )

            return dt

        except ValueError:
            continue

    return now_kst


# ============================================================
# DATE FROM TAG
# ============================================================

def _find_date(
    tag,
    now_kst: datetime | None = None,
) -> datetime | None:

    if tag is None:
        return now_kst

    # --------------------------------------------------------
    # time 태그
    # --------------------------------------------------------

    time_tag = tag.find(
        "time"
    )

    if time_tag:

        value = (
            time_tag.get(
                "datetime"
            )
            or time_tag.get_text(
                " ",
                strip=True,
            )
        )

        dt = _parse_datetime(
            value,
            now_kst,
        )

        if dt:
            return dt

    # --------------------------------------------------------
    # data attributes
    # --------------------------------------------------------

    for attr in (
        "data-date",
        "data-datetime",
        "data-published",
        "data-publish",
    ):

        value = tag.get(
            attr
        )

        if value:

            dt = _parse_datetime(
                value,
                now_kst,
            )

            if dt:
                return dt

    return now_kst


# ============================================================
# BASE CRAWLER
# ============================================================

class CrawlerEngine:

    def __init__(
        self,
        timeout: int = CRAWLER_TIMEOUT,
    ):

        self.timeout = timeout

# ============================================================
# CRAWLER ENGINE INSTANCE
# ============================================================

_engine = CrawlerEngine()



    def get(
        self,
        url: str,
    ) -> BeautifulSoup:

        try:

            response = _request(
                url,
                timeout=self.timeout,
            )

            return _soup(
                response
            )

        except Exception as exc:

            raise CrawlerError(
                f"페이지 요청 실패: {url}",
                cause=exc,
            ) from exc

    def crawl(
        self,
        url: str,
        parser,
        now_kst: datetime | None = None,
    ) -> list:

        soup = self.get(
            url
        )

        try:

            return parser(
                soup,
                now_kst,
            )

        except TypeError:

            return parser(
                soup
            )


# ============================================================
# BUSAN ILBO
# ============================================================

BUSAN_URLS = [

    "https://www.busan.com/",

    "https://mobile.busan.com/",

]


def _is_busan_article(
    href: str,
) -> bool:

    if not href:
        return False

    lower = href.lower()

    return (
        "/view/" in lower
        or "view.php" in lower
    )


def _parse_busan(
    soup: BeautifulSoup,
    now_kst: datetime | None = None,
) -> list:

    result = []

    seen = set()

    for tag in soup.select(
        "a[href]"
    ):

        href = tag.get(
            "href"
        )

        if not _is_busan_article(
            href
        ):
            continue

        title = _title(
            tag
        )

        if not title:
            continue

        # 너무 짧은 메뉴명 방지
        if len(title) < 8:
            continue

        link = _absolute_url(
            "https://mobile.busan.com/",
            href,
        )

        if not link:
            continue

        if link in seen:
            continue

        seen.add(
            link
        )

        # ----------------------------------------------------
        # 링크 주변에서 날짜 탐색
        # ----------------------------------------------------

        container = (
            tag.parent
            or tag
        )

        pub_dt = _find_date(
            container,
            now_kst,
        )

        result.append(
            _article(
                pub_dt,
                title,
                link,
                "부산일보",
            )
        )

    return result


def scrape_busan(
    now_kst: datetime | None = None,
) -> list:

    """
    부산일보

    1차:
        www.busan.com

    실패 시:
        mobile.busan.com

    GitHub Actions에서
    www.busan.com timeout이 발생해도
    전체 Pipeline이 중단되지 않는다.
    """

    for url in BUSAN_URLS:

        try:

            main_logger.info(
                "[부산일보] 접속: %s",
                url,
            )

            soup = _engine.get(
                url
            )

            result = _parse_busan(
                soup,
                now_kst,
            )

            if result:

                main_logger.info(
                    "[부산일보] %d건",
                    len(result),
                )

                return result

            main_logger.warning(
                "[부산일보] %s: 기사 0건",
                url,
            )

        except Exception as exc:

            main_logger.warning(
                "[부산일보] 접속 실패: %s",
                exc,
            )

    main_logger.error(
        "[부산일보] 모든 접속 경로 실패"
    )

    return []


# ============================================================
# KOOKJE SHINMUN
# ============================================================

KOOKJE_URLS = [

    # news_config.py의 기존 부동산 바로가기
    "http://www.kookje.co.kr/news2011/asp/sub_main.htm?code=0220",

    # 경제/부동산 관련 목록
    "https://www.kookje.co.kr/news2011/asp/list.asp?code=0210",

    # 전체 경제 영역 fallback
    "https://www.kookje.co.kr/news2011/asp/list.asp?code=0200",

    # 홈페이지 fallback
    "https://www.kookje.co.kr/",

]


def _is_kookje_article(
    href: str,
) -> bool:

    if not href:
        return False

    lower = href.lower()

    return (
        "newsbody.asp" in lower
        or "news_print.asp" in lower
    )


def _parse_kookje(
    soup: BeautifulSoup,
    now_kst: datetime | None = None,
) -> list:

    result = []

    seen = set()

    for tag in soup.select(
        "a[href]"
    ):

        href = tag.get(
            "href"
        )

        if not _is_kookje_article(
            href
        ):
            continue

        title = _title(
            tag
        )

        if not title:
            continue

        if len(title) < 8:
            continue

        link = _absolute_url(
            "https://www.kookje.co.kr/",
            href,
        )

        if not link:
            continue

        if link in seen:
            continue

        seen.add(
            link
        )

        container = (
            tag.parent
            or tag
        )

        pub_dt = _find_date(
            container,
            now_kst,
        )

        result.append(
            _article(
                pub_dt,
                title,
                link,
                "국제신문",
            )
        )

    return result


def scrape_kookje(
    now_kst: datetime | None = None,
) -> list:

    for url in KOOKJE_URLS:

        try:

            main_logger.info(
                "[국제신문] 접속: %s",
                url,
            )

            soup = _engine.get(
                url
            )

            result = _parse_kookje(
                soup,
                now_kst,
            )

            if result:

                main_logger.info(
                    "[국제신문] %d건",
                    len(result),
                )

                return result

            main_logger.warning(
                "[국제신문] %s: 기사 0건",
                url,
            )

        except Exception as exc:

            main_logger.warning(
                "[국제신문] 접속 실패: %s",
                exc,
            )

    main_logger.error(
        "[국제신문] 모든 접속 경로 실패"
    )

    return []


# ============================================================
# NAVER LAND
# ============================================================

NAVER_LAND_URLS = [

    "https://land.naver.com/news/",

    "https://land.naver.com/",

]


def _is_naver_article(
    href: str,
) -> bool:

    if not href:
        return False

    lower = href.lower()

    return (
        "land.naver.com/news" in lower
        or "/news/article/" in lower
    )


def _parse_naver_land(
    soup: BeautifulSoup,
    now_kst: datetime | None = None,
) -> list:

    result = []

    seen = set()

    for tag in soup.select(
        "a[href]"
    ):

        href = tag.get(
            "href"
        )

        if not _is_naver_article(
            href
        ):
            continue

        title = _title(
            tag
        )

        if not title:
            continue

        if len(title) < 8:
            continue

        link = _absolute_url(
            "https://land.naver.com/",
            href,
        )

        if not link:
            continue

        if link in seen:
            continue

        seen.add(
            link
        )

        pub_dt = _find_date(
            tag.parent,
            now_kst,
        )

        result.append(
            _article(
                pub_dt,
                title,
                link,
                "네이버부동산",
            )
        )

    return result


def scrape_naver_land(
    now_kst: datetime | None = None,
) -> list:

    for url in NAVER_LAND_URLS:

        try:

            soup = _engine.get(
                url
            )

            result = _parse_naver_land(
                soup,
                now_kst,
            )

            if result:

                main_logger.info(
                    "[네이버부동산] %d건",
                    len(result),
                )

                return result

        except Exception as exc:

            main_logger.warning(
                "[네이버부동산] 접속 실패: %s",
                exc,
            )

    main_logger.warning(
        "[네이버부동산] 수집 결과 0건"
    )

    return []


# ============================================================
# ALL
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

    tests = {

        "부산일보":
            scrape_busan,

        "국제신문":
            scrape_kookje,

        "네이버부동산":
            scrape_naver_land,

    }

    for name, func in tests.items():

        try:

            items = func()

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

    "scrape_busan",

    "scrape_kookje",

    "scrape_naver_land",

    "crawl_all",

    "health_check",

]
