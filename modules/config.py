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
