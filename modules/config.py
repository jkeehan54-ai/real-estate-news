# modules/config.py
# ============================================================
# BRN 2.0 Configuration
# Sprint 1-1
# Part 1 / 3
# ============================================================

from __future__ import annotations

import os
from pathlib import Path
from zoneinfo import ZoneInfo

# ============================================================
# PROJECT
# ============================================================

PROJECT_NAME = "BRN"
PROJECT_TITLE = "BRN 2.0"
PROJECT_VERSION = "2.0.0"

AUTHOR = "BRN Engine"
LICENSE = "MIT"

TIMEZONE = ZoneInfo("Asia/Seoul")
LOCALE = "ko_KR"

DEBUG = False

# ============================================================
# ROOT PATH
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

MODULE_DIR = ROOT_DIR / "modules"

DATA_DIR = ROOT_DIR / "data"

CACHE_DIR = ROOT_DIR / "cache"

LOG_DIR = ROOT_DIR / "logs"

REPORT_DIR = ROOT_DIR / "reports"

HISTORY_DIR = ROOT_DIR / "history"

HTML_DIR = ROOT_DIR / "html"

STATIC_DIR = ROOT_DIR / "static"

TEMPLATE_DIR = ROOT_DIR / "templates"

RESOURCE_DIR = ROOT_DIR / "resources"

BACKUP_DIR = ROOT_DIR / "backup"

EXPORT_DIR = ROOT_DIR / "export"

# ============================================================
# FILES
# ============================================================

CONFIG_FILE = ROOT_DIR / "config.json"

INDEX_HTML = ROOT_DIR / "index.html"

RSS_CACHE = CACHE_DIR / "rss_cache.json"

GOOGLE_CACHE = CACHE_DIR / "google_cache.json"

ARTICLE_CACHE = CACHE_DIR / "article_cache.json"

DUPLICATE_CACHE = CACHE_DIR / "duplicate_cache.json"

HISTORY_DB = HISTORY_DIR / "history.db"

MARKET_DB = DATA_DIR / "market.db"

REPORT_JSON = REPORT_DIR / "daily_report.json"

REPORT_HTML = REPORT_DIR / "daily_report.html"

REPORT_MD = REPORT_DIR / "daily_report.md"

DASHBOARD_JSON = REPORT_DIR / "dashboard.json"

INDICATOR_JSON = REPORT_DIR / "indicator.json"

MARKET_JSON = DATA_DIR / "market_data.json"

REB_JSON = DATA_DIR / "reb_market.json"

KB_JSON = DATA_DIR / "kb_market.json"

FEATURE_JSON = DATA_DIR / "feature_flags.json"

# ============================================================
# ENVIRONMENT
# ============================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID", "")

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")

NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")

REB_API_KEY = os.getenv("REB_API_KEY", "")

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK", "")

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK", "")

# ============================================================
# NEWS
# ============================================================

NEWS_LIMIT = 150

CATEGORY_LIMIT = 25

SOURCE_LIMIT = 10

GOOGLE_LIMIT = 20

RSS_TIMEOUT = 15

HTTP_TIMEOUT = 20

PLAYWRIGHT_TIMEOUT = 30000

USER_AGENT = (
    "Mozilla/5.0 "
    "(Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/138.0 Safari/537.36"
)

ENABLE_GOOGLE = True

ENABLE_RSS = True

ENABLE_NAVER = True

ENABLE_PLAYWRIGHT = True

ENABLE_DUPLICATE_FILTER = True

ENABLE_SUMMARIZATION = True

ENABLE_MARKET_DATA = True

ENABLE_AI = False

# ============================================================
# RSS FEEDS
# ============================================================

RSS_FEEDS = {

    "연합뉴스":
        "https://www.yna.co.kr/rss/economy.xml",

    "뉴시스":
        "https://www.newsis.com/RSS/economy.xml",

    "서울경제":
        "https://www.sedaily.com/rss/News.xml",

    "매일경제":
        "https://www.mk.co.kr/rss/30100041/",

    "한국경제":
        "https://www.hankyung.com/feed/realestate",

    "머니투데이":
        "https://news.mt.co.kr/mtview.php?no=rss",

    "파이낸셜뉴스":
        "https://www.fnnews.com/rss/fn_realestate.xml",

    "헤럴드경제":
        "https://biz.heraldcorp.com/rss",

    "아시아경제":
        "https://www.asiae.co.kr/rss/",

    "이데일리":
        "https://www.edaily.co.kr/rss/rss.xml",

    "부산일보":
        None,

    "국제신문":
        None,

    "네이버부동산":
        None,
}

# ============================================================
# CATEGORY
# ============================================================

CATEGORY_ORDER = [

    "정책",

    "시장동향",

    "청약",

    "공급개발",

    "재건축",

    "세제",

    "부산경남",

]

CATEGORY_LIMITS = {

    "정책": 20,

    "시장동향": 30,

    "청약": 20,

    "공급개발": 20,

    "재건축": 20,

    "세제": 15,

    "부산경남": 20,

}


# ============================================================
# modules/config.py
# BRN 2.0 Configuration
# Part 2 / 3
# ============================================================

# ============================================================
# SOURCE LIMIT
# ============================================================

SOURCE_LIMITS = {

    "연합뉴스": 10,
    "뉴시스": 10,
    "서울경제": 10,
    "매일경제": 10,
    "한국경제": 10,
    "머니투데이": 10,
    "파이낸셜뉴스": 10,
    "헤럴드경제": 10,
    "아시아경제": 10,
    "이데일리": 10,
    "부산일보": 15,
    "국제신문": 15,
    "네이버부동산": 20,

}

# ============================================================
# DUPLICATE FILTER
# ============================================================

TITLE_SIMILARITY = 0.90

EVENT_SIMILARITY = 0.85

MIN_REAL_ESTATE_SCORE = 3

REMOVE_DUPLICATE_LINK = True

REMOVE_DUPLICATE_TITLE = True

REMOVE_DUPLICATE_EVENT = True

# ============================================================
# CACHE
# ============================================================

CACHE_ENABLED = True

CACHE_EXPIRE_HOURS = 12

CACHE_MAX_ITEMS = 10000

CACHE_COMPRESS = True

# ============================================================
# HTML
# ============================================================

HTML_TITLE = "부동산 뉴스 브리핑"

HTML_LANGUAGE = "ko"

HTML_ENCODING = "utf-8"

HTML_THEME = "light"

HTML_SHOW_SOURCE = True

HTML_SHOW_DATE = True

HTML_SHOW_CATEGORY = True

HTML_SHOW_AI_SUMMARY = True

HTML_SHOW_MARKET = True

HTML_SHOW_FOOTER = True

HTML_SHOW_VERSION = True

HTML_AUTO_REFRESH = False

HTML_REFRESH_SECONDS = 600

# ============================================================
# DASHBOARD
# ============================================================

DASHBOARD_ENABLE = True

DASHBOARD_HISTORY_DAYS = 365

DASHBOARD_DEFAULT_RANGE = 30

DASHBOARD_SAVE_JSON = True

DASHBOARD_SAVE_HTML = True

DASHBOARD_SAVE_IMAGE = False

# ============================================================
# REPORT
# ============================================================

REPORT_ENABLE = True

REPORT_SAVE_HTML = True

REPORT_SAVE_JSON = True

REPORT_SAVE_MD = True

REPORT_SAVE_PDF = False

REPORT_INCLUDE_NEWS = True

REPORT_INCLUDE_MARKET = True

REPORT_INCLUDE_AI = True

REPORT_INCLUDE_FORECAST = True

# ============================================================
# HISTORY
# ============================================================

HISTORY_ENABLE = True

HISTORY_SAVE_DAILY = True

HISTORY_SAVE_MONTHLY = True

HISTORY_RETENTION_DAYS = 3650

HISTORY_DB_ENABLE = True

# ============================================================
# MARKET
# ============================================================

MARKET_ENABLE = True

KB_ENABLE = True

REB_ENABLE = True

BANK_ENABLE = False

MARKET_TIMEOUT = 20

MARKET_CACHE_MINUTES = 180

# ============================================================
# AI
# ============================================================

AI_ENABLE = False

AI_PROVIDER = "OpenAI"

AI_MODEL = "gpt-5.5"

AI_TEMPERATURE = 0.3

AI_MAX_TOKENS = 4000

AI_TIMEOUT = 120

AI_RETRY = 2

# ============================================================
# LOGGING
# ============================================================

LOG_ENABLE = True

LOG_LEVEL = "INFO"

LOG_ROTATION = "10 MB"

LOG_RETENTION = "30 days"

LOG_ENCODING = "utf-8"

LOG_CONSOLE = True

LOG_FILE = True

# ============================================================
# SCHEDULER
# ============================================================

SCHEDULE_ENABLE = True

RUN_HOUR = 7

RUN_MINUTE = 0

RUN_SECOND = 0

RUN_TIMEZONE = "Asia/Seoul"

# ============================================================
# EXPORT
# ============================================================

EXPORT_HTML = True

EXPORT_JSON = True

EXPORT_CSV = True

EXPORT_XLSX = False

EXPORT_SQLITE = False

# ============================================================
# FEATURE FLAGS
# ============================================================

FEATURE_FLAGS = {

    "dashboard": True,

    "history": True,

    "indicator": True,

    "forecast": True,

    "report": True,

    "market": True,

    "rss": True,

    "google": True,

    "crawler": True,

    "duplicate_filter": True,

    "html_builder": True,

    "cache": True,

    "logging": True,

    "statistics": True,

    "ranking": True,

    "keyword_analysis": True,

    "sentiment_analysis": False,

    "ai_summary": False,

    "telegram": False,

    "slack": False,

    "discord": False,

    "email": False,

}



# ============================================================
# modules/config.py
# BRN 2.0 Configuration
# Part 3 / 3
# ============================================================

from dataclasses import dataclass, field
from typing import Any


# ============================================================
# CONFIG CLASS
# ============================================================

@dataclass(slots=True)
class Config:
    """
    BRN Global Configuration
    """

    project_name: str = PROJECT_NAME
    project_title: str = PROJECT_TITLE
    version: str = PROJECT_VERSION

    root_dir: Path = ROOT_DIR
    module_dir: Path = MODULE_DIR
    data_dir: Path = DATA_DIR
    cache_dir: Path = CACHE_DIR
    log_dir: Path = LOG_DIR
    report_dir: Path = REPORT_DIR
    history_dir: Path = HISTORY_DIR

    debug: bool = DEBUG

    timezone: Any = TIMEZONE

    news_limit: int = NEWS_LIMIT
    category_limit: int = CATEGORY_LIMIT
    source_limit: int = SOURCE_LIMIT

    rss_timeout: int = RSS_TIMEOUT
    http_timeout: int = HTTP_TIMEOUT
    playwright_timeout: int = PLAYWRIGHT_TIMEOUT

    html_title: str = HTML_TITLE

    ai_enable: bool = AI_ENABLE
    ai_provider: str = AI_PROVIDER
    ai_model: str = AI_MODEL

    dashboard_enable: bool = DASHBOARD_ENABLE
    report_enable: bool = REPORT_ENABLE
    history_enable: bool = HISTORY_ENABLE

    feature_flags: dict = field(
        default_factory=lambda: FEATURE_FLAGS.copy()
    )

    category_order: list = field(
        default_factory=lambda: CATEGORY_ORDER.copy()
    )

    category_limits: dict = field(
        default_factory=lambda: CATEGORY_LIMITS.copy()
    )

    source_limits: dict = field(
        default_factory=lambda: SOURCE_LIMITS.copy()
    )

    rss_feeds: dict = field(
        default_factory=lambda: RSS_FEEDS.copy()
    )

    def ensure_directories(self) -> None:
        """
        프로젝트 디렉터리 생성
        """

        directories = [

            self.cache_dir,
            self.log_dir,
            self.report_dir,
            self.history_dir,
            DATA_DIR,
            HTML_DIR,
            STATIC_DIR,
            TEMPLATE_DIR,
            RESOURCE_DIR,
            BACKUP_DIR,
            EXPORT_DIR,

        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    @property
    def openai_api_key(self) -> str:
        return OPENAI_API_KEY

    @property
    def reb_api_key(self) -> str:
        return REB_API_KEY

    @property
    def google_api_key(self) -> str:
        return GOOGLE_API_KEY

    @property
    def google_cse_id(self) -> str:
        return GOOGLE_CSE_ID

    @property
    def naver_client_id(self) -> str:
        return NAVER_CLIENT_ID

    @property
    def naver_client_secret(self) -> str:
        return NAVER_CLIENT_SECRET

    @property
    def slack_webhook(self) -> str:
        return SLACK_WEBHOOK

    @property
    def discord_webhook(self) -> str:
        return DISCORD_WEBHOOK

    def is_feature_enabled(self, feature: str) -> bool:
        return self.feature_flags.get(feature, False)

    def enable_feature(self, feature: str) -> None:
        self.feature_flags[feature] = True

    def disable_feature(self, feature: str) -> None:
        self.feature_flags[feature] = False

    def to_dict(self) -> dict:

        return {

            "project_name": self.project_name,
            "project_title": self.project_title,
            "version": self.version,
            "news_limit": self.news_limit,
            "category_limit": self.category_limit,
            "source_limit": self.source_limit,
            "dashboard_enable": self.dashboard_enable,
            "report_enable": self.report_enable,
            "history_enable": self.history_enable,
            "ai_enable": self.ai_enable,
            "ai_provider": self.ai_provider,
            "ai_model": self.ai_model,
            "timezone": str(self.timezone),
            "debug": self.debug,

        }


# ============================================================
# SINGLETON
# ============================================================

config = Config()

config.ensure_directories()


# ============================================================
# EXPORT
# ============================================================

__all__ = [

    "Config",
    "config",

    "PROJECT_NAME",
    "PROJECT_TITLE",
    "PROJECT_VERSION",

    "ROOT_DIR",
    "MODULE_DIR",
    "DATA_DIR",
    "CACHE_DIR",
    "LOG_DIR",
    "REPORT_DIR",
    "HISTORY_DIR",

    "RSS_FEEDS",
    "CATEGORY_ORDER",
    "CATEGORY_LIMITS",
    "SOURCE_LIMITS",

    "FEATURE_FLAGS",

    "INDEX_HTML",
    "REPORT_JSON",
    "REPORT_HTML",
    "REPORT_MD",

]
