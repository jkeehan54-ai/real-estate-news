# timeline_engine.py


"""
BRN Timeline Engine

History를 읽어서 Timeline을 생성한다.
"""

from __future__ import annotations

import json

from pathlib import Path


class TimelineEngine:

    def __init__(
        self,
        history_dir: str = "history",
    ):

        self.history_dir = Path(history_dir)

    def load(
        self,
        region: str = "전국",
    ) -> list[dict]:

        timeline = []

        if not self.history_dir.exists():

            return timeline

        files = sorted(
            self.history_dir.glob(f"*_{region}.json")
        )

        for file in files:

            with open(
                file,
                encoding="utf-8",
            ) as f:

                data = json.load(f)

            dashboard = data["dashboard"]

            timeline.append(
                {
                    "date": data["created_at"],
                    "brn_index": dashboard["brn_index"],
                    "health": dashboard["health"],
                    "leading": dashboard["leading"],
                    "risk": dashboard["risk"],
                }
            )

        return timeline

    def latest(
        self,
        region: str = "전국",
    ) -> dict | None:

        timeline = self.load(region)

        if not timeline:

            return None

        return timeline[-1]

    def previous(
        self,
        region: str = "전국",
    ) -> dict | None:

        timeline = self.load(region)

        if len(timeline) < 2:

            return None

        return timeline[-2]

    def trend(
        self,
        region: str = "전국",
    ) -> float:

        latest = self.latest(region)

        previous = self.previous(region)

        if latest is None:

            return 0.0

        if previous is None:

            return 0.0

        return round(
            latest["brn_index"] -
            previous["brn_index"],
            2,
        )
