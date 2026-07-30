# modules/rss_engine.py
# ============================================================
# BRN 2.0 RSS Engine
# Sprint 1-2
# Part 1 / 3
# ============================================================

from __future__ import annotations

from datetime import datetime
from typing import Any

import feedparser
import requests

from .config import (
    RSS_FEEDS,
    RSS_TIMEOUT,
    USER_AGENT,
)
from .exceptions import RSSFetchError
from .logger import rss_logger
from .utils import clean_text

# ============================================================
# RSS ENGINE
# ============================================================

class RSSEngine:
    """
    RSS 수집 엔진
    """

    def __init__(self):

        self.session = requests.Session()

        self.session.headers.update({

            "User-Agent": USER_AGENT,

        })

    # --------------------------------------------------------

    def fetch_all(self) -> list[dict]:

        news = []

        for source, url in RSS_FEEDS.items():

            if not url:

                continue

            try:

                items = self.fetch(source, url)

                news.extend(items)

            except Exception as exc:

                rss_logger.exception(

                    "%s : %s",

                    source,

                    exc,

                )

        return news

    # --------------------------------------------------------

    def fetch(
        self,
        source: str,
        url: str,
    ) -> list[dict]:

        rss_logger.info(

            "[RSS] %s",

            source,

        )

        try:

            response = self.session.get(

                url,

                timeout=RSS_TIMEOUT,

            )

            response.raise_for_status()

        except Exception as exc:

            raise RSSFetchError(

                f"{source} RSS 다운로드 실패",

                cause=exc,

            ) from exc

        feed = feedparser.parse(

            response.content

        )

        result = []

        for entry in feed.entries:

            article = self._parse_entry(

                source,

                entry,

            )

            if article:

                result.append(article)

        rss_logger.info(

            "%s : %d건",

            source,

            len(result),

        )

        return result

    # --------------------------------------------------------

    def _parse_entry(
        self,
        source: str,
        entry: Any,
    ) -> dict | None:

        title = clean_text(

            getattr(entry, "title", "")

        )

        if not title:

            return None

        link = getattr(

            entry,

            "link",

            "",

        )

        summary = clean_text(

            getattr(

                entry,

                "summary",

                "",

            )

        )

        published = self._published(entry)

        return {

            "source": source,

            "title": title,

            "summary": summary,

            "link": link,

            "published": published,

        }

    # --------------------------------------------------------

    def _published(
        self,
        entry: Any,
    ) -> str:

        value = getattr(

            entry,

            "published",

            "",

        )

        if value:

            return value

        value = getattr(

            entry,

            "updated",

            "",

        )

        if value:

            return value

        return datetime.now().isoformat()


# ============================================================
# modules/rss_engine.py
# BRN 2.0 RSS Engine
# Sprint 1-2
# Part 2 / 3
# ============================================================

    # --------------------------------------------------------
    # FETCH SELECTED SOURCES
    # --------------------------------------------------------

    def fetch_sources(
        self,
        sources: list[str],
    ) -> list[dict]:

        news: list[dict] = []

        for source in sources:

            url = RSS_FEEDS.get(source)

            if not url:
                continue

            try:

                news.extend(
                    self.fetch(
                        source,
                        url,
                    )
                )

            except Exception as exc:

                rss_logger.exception(
                    "[RSS] %s : %s",
                    source,
                    exc,
                )

        return news

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    def validate_article(
        self,
        article: dict,
    ) -> bool:

        if not article.get("title"):
            return False

        if not article.get("link"):
            return False

        return True

    # --------------------------------------------------------
    # NORMALIZE
    # --------------------------------------------------------

    def normalize(
        self,
        article: dict,
    ) -> dict:

        return {

            "title": clean_text(
                article.get("title", "")
            ),

            "summary": clean_text(
                article.get("summary", "")
            ),

            "link": article.get(
                "link",
                "",
            ),

            "source": article.get(
                "source",
                "",
            ),

            "published": article.get(
                "published",
                "",
            ),

            "category": article.get(
                "category",
                "",
            ),

        }

    # --------------------------------------------------------
    # REMOVE DUPLICATE LINK
    # --------------------------------------------------------

    def remove_duplicates(
        self,
        news: list[dict],
    ) -> list[dict]:

        result = []

        seen = set()

        for item in news:

            link = item.get("link")

            if not link:
                continue

            if link in seen:
                continue

            seen.add(link)

            result.append(item)

        return result

    # --------------------------------------------------------
    # SORT
    # --------------------------------------------------------

    def sort(
        self,
        news: list[dict],
    ) -> list[dict]:

        return sorted(

            news,

            key=lambda x: (
                x.get("published", ""),
                x.get("title", ""),
            ),

            reverse=True,

        )

    # --------------------------------------------------------
    # PROCESS
    # --------------------------------------------------------

    def process(
        self,
        news: list[dict],
    ) -> list[dict]:

        result = []

        for article in news:

            if not self.validate_article(article):
                continue

            result.append(
                self.normalize(article)
            )

        result = self.remove_duplicates(result)

        result = self.sort(result)

        rss_logger.info(
            "[RSS] Total : %d",
            len(result),
        )

        return result


# ============================================================
# modules/rss_engine.py
# BRN 2.0 RSS Engine
# Sprint 1-2
# Part 3 / 3
# ============================================================

    # --------------------------------------------------------
    # RUN
    # --------------------------------------------------------

    def run(self) -> list[dict]:
        """
        RSS 전체 실행
        """

        news = self.fetch_all()

        news = self.process(news)

        return news

    # --------------------------------------------------------
    # ITERATOR
    # --------------------------------------------------------

    def __iter__(self):

        return iter(self.fetch_all())

    # --------------------------------------------------------
    # LENGTH
    # --------------------------------------------------------

    def __len__(self):

        return len(self.fetch_all())

    # --------------------------------------------------------
    # STRING
    # --------------------------------------------------------

    def __repr__(self):

        return (
            f"RSSEngine("
            f"sources={len(RSS_FEEDS)})"
        )


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================

_engine = RSSEngine()


def fetch_rss() -> list[dict]:
    """
    전체 RSS 수집
    """
    return _engine.run()


def fetch_source(source: str) -> list[dict]:
    """
    단일 RSS 수집
    """

    url = RSS_FEEDS.get(source)

    if not url:
        return []

    return _engine.fetch(source, url)


def fetch_sources(
    sources: list[str],
) -> list[dict]:
    """
    지정 RSS 수집
    """

    return _engine.fetch_sources(sources)


# ============================================================
# EXPORT
# ============================================================

__all__ = [

    "RSSEngine",

    "fetch_rss",

    "fetch_source",

    "fetch_sources",

]


