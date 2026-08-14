# modules/exceptions.py
# ============================================================
# BRN 2.0 Exception Definitions
# Sprint 1-1
# Part 1 / 2
# ============================================================

from __future__ import annotations

from typing import Any, Optional


# ============================================================
# BASE EXCEPTION
# ============================================================

class BRNError(Exception):
    """
    BRN Base Exception
    """

    default_message = "BRN Error"

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        cause: Exception | None = None,
        data: Any = None,
    ):

        self.message = message or self.default_message
        self.cause = cause
        self.data = data

        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f"(message={self.message!r})"
        )


# ============================================================
# CONFIGURATION
# ============================================================

class ConfigurationError(BRNError):
    default_message = "Configuration Error"


class EnvironmentError(BRNError):
    default_message = "Environment Variable Error"


class ValidationError(BRNError):
    default_message = "Validation Error"


# ============================================================
# NETWORK
# ============================================================

class NetworkError(BRNError):
    default_message = "Network Error"


class TimeoutError(BRNError):
    default_message = "Request Timeout"


class DownloadError(BRNError):
    default_message = "Download Error"


# ============================================================
# RSS
# ============================================================

class RSSFetchError(BRNError):
    default_message = "RSS Fetch Error"


class RSSParseError(BRNError):
    default_message = "RSS Parse Error"


# ============================================================
# CRAWLER
# ============================================================

class CrawlerError(BRNError):
    default_message = "Crawler Error"


class PlaywrightError(BRNError):
    default_message = "Playwright Error"


class HTMLParseError(BRNError):
    default_message = "HTML Parse Error"


# ============================================================
# NEWS
# ============================================================

class NewsError(BRNError):
    default_message = "News Error"


class DuplicateFilterError(BRNError):
    default_message = "Duplicate Filter Error"


class ClassificationError(BRNError):
    default_message = "News Classification Error"


# ============================================================
# MARKET
# ============================================================

class MarketDataError(BRNError):
    default_message = "Market Data Error"


class KBMarketError(BRNError):
    default_message = "KB Market Error"


class REBMarketError(BRNError):
    default_message = "REB Market Error"


class InterestRateError(BRNError):
    default_message = "Interest Rate Error"


# ============================================================
# DASHBOARD
# ============================================================

class DashboardError(BRNError):
    default_message = "Dashboard Error"


class IndicatorError(BRNError):
    default_message = "Indicator Error"


class ForecastError(BRNError):
    default_message = "Forecast Error"


class SignalError(BRNError):
    default_message = "Market Signal Error"


# ============================================================
# REPORT
# ============================================================

class ReportError(BRNError):
    default_message = "Report Error"


class HTMLBuildError(BRNError):
    default_message = "HTML Build Error"


class ExportError(BRNError):
    default_message = "Export Error"


# ============================================================
# modules/exceptions.py
# BRN 2.0 Exception Definitions
# Sprint 1-1
# Part 2 / 2
# ============================================================

# ============================================================
# HISTORY
# ============================================================

class HistoryError(BRNError):
    default_message = "History Error"


class SnapshotError(BRNError):
    default_message = "Snapshot Error"


class DatabaseError(BRNError):
    default_message = "Database Error"


# ============================================================
# CACHE
# ============================================================

class CacheError(BRNError):
    default_message = "Cache Error"


class CacheReadError(CacheError):
    default_message = "Cache Read Error"


class CacheWriteError(CacheError):
    default_message = "Cache Write Error"


class CacheExpiredError(CacheError):
    default_message = "Cache Expired"


# ============================================================
# AI
# ============================================================

class AIEngineError(BRNError):
    default_message = "AI Engine Error"


class AIConnectionError(AIEngineError):
    default_message = "AI Connection Error"


class AIResponseError(AIEngineError):
    default_message = "AI Response Error"


# ============================================================
# FILE
# ============================================================

class FileError(BRNError):
    default_message = "File Error"


class FileNotFoundBRNError(FileError):
    default_message = "File Not Found"


class FileReadError(FileError):
    default_message = "File Read Error"


class FileWriteError(FileError):
    default_message = "File Write Error"


class JSONError(FileError):
    default_message = "JSON Error"


class CSVError(FileError):
    default_message = "CSV Error"


# ============================================================
# SECURITY
# ============================================================

class AuthenticationError(BRNError):
    default_message = "Authentication Error"


class AuthorizationError(BRNError):
    default_message = "Authorization Error"


# ============================================================
# UNKNOWN
# ============================================================

class UnknownBRNError(BRNError):
    default_message = "Unknown BRN Error"


# ============================================================
# EXPORT
# ============================================================

__all__ = [

    # Base
    "BRNError",

    # Configuration
    "ConfigurationError",
    "EnvironmentError",
    "ValidationError",

    # Network
    "NetworkError",
    "TimeoutError",
    "DownloadError",

    # RSS
    "RSSFetchError",
    "RSSParseError",

    # Crawler
    "CrawlerError",
    "PlaywrightError",
    "HTMLParseError",

    # News
    "NewsError",
    "DuplicateFilterError",
    "ClassificationError",

    # Market
    "MarketDataError",
    "KBMarketError",
    "REBMarketError",
    "InterestRateError",

    # Dashboard
    "DashboardError",
    "IndicatorError",
    "ForecastError",
    "SignalError",

    # Report
    "ReportError",
    "HTMLBuildError",
    "ExportError",

    # History
    "HistoryError",
    "SnapshotError",
    "DatabaseError",

    # Cache
    "CacheError",
    "CacheReadError",
    "CacheWriteError",
    "CacheExpiredError",

    # AI
    "AIEngineError",
    "AIConnectionError",
    "AIResponseError",

    # File
    "FileError",
    "FileNotFoundBRNError",
    "FileReadError",
    "FileWriteError",
    "JSONError",
    "CSVError",

    # Security
    "AuthenticationError",
    "AuthorizationError",

    # Unknown
    "UnknownBRNError",

]




