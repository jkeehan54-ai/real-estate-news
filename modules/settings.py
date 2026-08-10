# modules/settings.py
# ============================================================
# BRN 2.0 Settings
# Sprint 1-1
# Part 1 / 3
# ============================================================

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any

from .config import (
    CONFIG_FILE,
    PROJECT_NAME,
    PROJECT_VERSION,
    DEBUG,
)

# ============================================================
# DEFAULT SETTINGS
# ============================================================

@dataclass
class Settings:

    # --------------------------------------------------------
    # PROJECT
    # --------------------------------------------------------

    project_name: str = PROJECT_NAME

    version: str = PROJECT_VERSION

    debug: bool = DEBUG

    # --------------------------------------------------------
    # NEWS
    # --------------------------------------------------------

    news_limit: int = 150

    category_limit: int = 25

    source_limit: int = 10

    enable_rss: bool = True

    enable_google: bool = True

    enable_naver: bool = True

    enable_playwright: bool = True

    enable_duplicate_filter: bool = True

    # --------------------------------------------------------
    # MARKET
    # --------------------------------------------------------

    enable_market: bool = True

    enable_kb: bool = True

    enable_reb: bool = True

    # --------------------------------------------------------
    # REPORT
    # --------------------------------------------------------

    enable_dashboard: bool = True

    enable_report: bool = True

    enable_history: bool = True

    # --------------------------------------------------------
    # AI
    # --------------------------------------------------------

    enable_ai: bool = False

    ai_provider: str = "OpenAI"

    ai_model: str = "gpt-5.5"

    # --------------------------------------------------------
    # HTML
    # --------------------------------------------------------

    html_theme: str = "light"

    html_language: str = "ko"

    html_show_source: bool = True

    html_show_date: bool = True

    html_show_footer: bool = True

    # --------------------------------------------------------
    # LOG
    # --------------------------------------------------------

    log_level: str = "INFO"

    # --------------------------------------------------------
    # USER
    # --------------------------------------------------------

    extra: dict[str, Any] = field(
        default_factory=dict
    )

    # ========================================================
    # SAVE
    # ========================================================

    def save(
        self,
        path: str | Path = CONFIG_FILE,
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
                asdict(self),
                fp,
                ensure_ascii=False,
                indent=2,
            )



# ============================================================
# modules/settings.py
# BRN 2.0 Settings
# Sprint 1-1
# Part 2 / 3
# ============================================================

    # ========================================================
    # LOAD
    # ========================================================

    @classmethod
    def load(
        cls,
        path: str | Path = CONFIG_FILE,
    ) -> "Settings":

        path = Path(path)

        if not path.exists():

            settings = cls()

            settings.save(path)

            return settings

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as fp:

            data = json.load(fp)

        settings = cls()

        for key, value in data.items():

            if hasattr(settings, key):

                setattr(
                    settings,
                    key,
                    value,
                )

        return settings

    # ========================================================
    # UPDATE
    # ========================================================

    def update(
        self,
        **kwargs,
    ) -> None:

        for key, value in kwargs.items():

            if hasattr(self, key):

                setattr(
                    self,
                    key,
                    value,
                )

    # ========================================================
    # GET
    # ========================================================

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:

        return getattr(
            self,
            key,
            default,
        )

    # ========================================================
    # SET
    # ========================================================

    def set(
        self,
        key: str,
        value: Any,
    ) -> None:

        if hasattr(self, key):

            setattr(
                self,
                key,
                value,
            )

        else:

            self.extra[key] = value

    # ========================================================
    # RESET
    # ========================================================

    def reset(self) -> None:

        defaults = Settings()

        self.__dict__.update(
            defaults.__dict__
        )

    # ========================================================
    # EXPORT
    # ========================================================

    def to_dict(self) -> dict[str, Any]:

        return asdict(self)

    # ========================================================
    # IMPORT
    # ========================================================

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "Settings":

        settings = cls()

        for key, value in data.items():

            if hasattr(
                settings,
                key,
            ):

                setattr(
                    settings,
                    key,
                    value,
                )

            else:

                settings.extra[key] = value

        return settings


# ============================================================
# modules/settings.py
# BRN 2.0 Settings
# Sprint 1-1
# Part 3 / 3
# ============================================================

    # ========================================================
    # ENVIRONMENT
    # ========================================================

    def load_environment(self) -> None:
        """
        환경변수에서 설정을 읽어온다.
        """

        env_map = {
            "OPENAI_API_KEY": "openai_api_key",
            "GOOGLE_API_KEY": "google_api_key",
            "GOOGLE_CSE_ID": "google_cse_id",
            "NAVER_CLIENT_ID": "naver_client_id",
            "NAVER_CLIENT_SECRET": "naver_client_secret",
            "REB_API_KEY": "reb_api_key",
        }

        for env_name, attr_name in env_map.items():

            value = os.getenv(env_name)

            if value:

                self.extra[attr_name] = value

    # ========================================================
    # VALIDATION
    # ========================================================

    def validate(self) -> bool:
        """
        기본 설정 검증
        """

        if self.news_limit <= 0:
            return False

        if self.category_limit <= 0:
            return False

        if self.source_limit <= 0:
            return False

        if self.ai_provider == "":
            return False

        return True

    # ========================================================
    # STRING
    # ========================================================

    def __repr__(self) -> str:

        return (
            f"Settings("
            f"project='{self.project_name}', "
            f"version='{self.version}', "
            f"debug={self.debug})"
        )

    def __str__(self) -> str:

        return (
            f"{self.project_name} "
            f"{self.version}"
        )


# ============================================================
# SINGLETON
# ============================================================

settings = Settings.load()

settings.load_environment()


# ============================================================
# EXPORT
# ============================================================

__all__ = [

    "Settings",

    "settings",

]




