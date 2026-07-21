# history_engine.py


"""
BRN History Engine

Dashboard와 Report를 일일 Snapshot으로 저장한다.
"""

from __future__ import annotations

import json

from datetime import datetime
from pathlib import Path


class HistoryEngine:
    """
    BRN History 관리
    """

    def __init__(
        self,
        history_dir: str = "history",
    ):

        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    def snapshot_name(
        self,
        region: str,
        created_at: datetime | None = None,
    ) -> str:

        created_at = created_at or datetime.now()

        return (
            f"{created_at.strftime('%Y%m%d')}"
            f"_{region}.json"
        )

    def save_dashboard(
        self,
        dashboard: dict,
    ) -> Path:

        path = self.history_dir / self.snapshot_name(
            dashboard["region"],
        )

        data = {
            "type": "dashboard",
            "saved_at": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "dashboard": dashboard,
        }

        with open(
            path,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=4,
            )

        return path

    def save_report(
        self,
        report: dict,
    ) -> Path:

        region = report["dashboard"]["region"]

        path = self.history_dir / self.snapshot_name(
            region,
        )

        with open(
            path,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                report,
                f,
                ensure_ascii=False,
                indent=4,
            )

        return path

    def load(
        self,
        filename: str,
    ) -> dict:

        path = self.history_dir / filename

        with open(
            path,
            encoding="utf-8",
        ) as f:

            return json.load(f)

    def list_history(
        self,
        region: str | None = None,
    ) -> list[Path]:

        files = sorted(
            self.history_dir.glob("*.json")
        )

        if region is None:

            return files

        return [
            f
            for f in files
            if f.stem.endswith(region)
        ]

    def latest(
        self,
        region: str = "전국",
    ) -> dict | None:

        files = self.list_history(region)

        if not files:

            return None

        with open(
            files[-1],
            encoding="utf-8",
        ) as f:

            return json.load(f)
