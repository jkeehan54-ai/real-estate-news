# modules/crawler_engine.py
# ============================================================
# BRN 2.0 Crawler Engine
# Sprint 1-2
# Part 1 / 3
# ============================================================

from __future__ import annotations

from typing import Callable

import requests
from bs4 import BeautifulSoup

from .config import (
    HTTP_TIMEOUT,
    USER_AGENT,
)
from .exceptions import CrawlerError
from .logger import main_logger
from .utils import clean_text

# ============================================================
# BASE CRAWLER
# ============================================================

class CrawlerEngine:
    """
    BRN HTML Crawler
    """

    def __init__(self):

        self.session = requests.Session()

        self.session.headers.update({

            "User-Agent": USER_AGENT,

        })

    # --------------------------------------------------------

    def get(
        self,
        url: str,
    ) -> BeautifulSoup:

        try:

            response = self.session.get(

                url,

                timeout=HTTP_TIMEOUT,

            )

            response.raise_for_status()

        except Exception as exc:

            raise CrawlerError(

                f"페이지 요청 실패 : {url}",

                cause=exc,

            ) from exc

        return BeautifulSoup(

            response.text,

            "html.parser",

        )

    # --------------------------------------------------------

    def crawl(
        self,
        url: str,
        parser: Callable,
    ) -> list[dict]:

        soup = self.get(url)

        result = parser(soup)

        main_logger.info(

            "[Crawler] %s -> %d",

            url,

            len(result),

        )

        return result

    # --------------------------------------------------------

    @staticmethod
    def article(
        title: str,
        link: str,
        source: str,
        summary: str = "",
        category: str = "",
    ) -> dict:

        return {

            "title": clean_text(title),

            "summary": clean_text(summary),

            "link": link,

            "source": source,

            "category": category,

        }


# ============================================================
# BUSAN ILBO
# ============================================================

def parse_busan(
    soup: BeautifulSoup,
) -> list[dict]:

    news = []

    for tag in soup.select("a"):

        title = clean_text(

            tag.get_text()

        )

        href = tag.get("href")

        if not title:

            continue

        if not href:

            continue

        if "/news/" not in href:

            continue

        if href.startswith("/"):

            href = (

                "https://www.busan.com"

                + href

            )

        news.append(

            CrawlerEngine.article(

                title,

                href,

                "부산일보",

                "",

                "부산경남",

            )

        )

    return news


# ============================================================
# modules/crawler_engine.py
# BRN 2.0 Crawler Engine
# Sprint 1-2
# Part 2 / 3
# ============================================================

# ============================================================
# KOOKJE SHINMUN
# ============================================================

def parse_kookje(
    soup: BeautifulSoup,
) -> list[dict]:

    news = []

    for tag in soup.select("a"):

        title = clean_text(
            tag.get_text()
        )

        href = tag.get("href")

        if not title:
            continue

        if not href:
            continue

        if "/news" not in href:
            continue

        if href.startswith("/"):

            href = (
                "https://www.kookje.co.kr"
                + href
            )

        news.append(

            CrawlerEngine.article(

                title,

                href,

                "국제신문",

                "",

                "부산경남",

            )

        )

    return news


# ============================================================
# NAVER LAND
# ============================================================

def parse_naver_land(
    soup: BeautifulSoup,
) -> list[dict]:

    news = []

    for tag in soup.select("a"):

        title = clean_text(
            tag.get_text()
        )

        href = tag.get("href")

        if not title:
            continue

        if not href:
            continue

        if "land.naver.com" not in href:
            continue

        news.append(

            CrawlerEngine.article(

                title,

                href,

                "네이버부동산",

                "",

                "시장동향",

            )

        )

    return news


# ============================================================
# SCRAPER
# ============================================================

_engine = CrawlerEngine()


def scrape_busan() -> list[dict]:

    url = (
        "https://www.busan.com/"
    )

    return _engine.crawl(
        url,
        parse_busan,
    )


def scrape_kookje() -> list[dict]:

    url = (
        "https://www.kookje.co.kr/"
    )

    return _engine.crawl(
        url,
        parse_kookje,
    )


def scrape_naver_land() -> list[dict]:

    url = (
        "https://land.naver.com/"
    )

    return _engine.crawl(
        url,
        parse_naver_land,
    )


# ============================================================
# modules/crawler_engine.py
# BRN 2.0 Crawler Engine
# Sprint 1-2
# Part 3 / 3
# ============================================================

# ============================================================
# RUN ALL
# ============================================================

def crawl_all() -> list[dict]:
    """
    모든 크롤러 실행
    """

    news = []

    crawlers = (

        scrape_busan,

        scrape_kookje,

        scrape_naver_land,

    )

    for crawler in crawlers:

        try:

            news.extend(
                crawler()
            )

        except Exception as exc:

            main_logger.exception(

                "[Crawler] %s",

                exc,

            )

    return news


# ============================================================
# HEALTH CHECK
# ============================================================

def health_check() -> dict:

    result = {}

    tests = {

        "부산일보": scrape_busan,

        "국제신문": scrape_kookje,

        "네이버부동산": scrape_naver_land,

    }

    for name, func in tests.items():

        try:

            count = len(func())

            result[name] = {

                "success": True,

                "count": count,

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

    "crawl_all",

    "health_check",

    "scrape_busan",

    "scrape_kookje",

    "scrape_naver_land",

]

