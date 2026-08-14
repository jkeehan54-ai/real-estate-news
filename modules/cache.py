# modules/cache.py
# ============================================================
# BRN 2.0 Cache Engine
# Sprint 1-1
# Part 1 / 3
# ============================================================

from __future__ import annotations

import json
import pickle
import time
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any

from .config import (
    CACHE_DIR,
    CACHE_ENABLED,
    CACHE_EXPIRE_HOURS,
)
from .exceptions import CacheReadError
from .exceptions import CacheWriteError

# ============================================================
# CACHE PATH
# ============================================================

CACHE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

# ============================================================
# CACHE ITEM
# ============================================================

@dataclass(slots=True)
class CacheItem:

    key: str

    value: Any

    created: float

    expire: float

    @property
    def expired(self) -> bool:

        return time.time() >= self.expire


# ============================================================
# CACHE
# ============================================================

class Cache:

    """
    Memory + File Cache
    """

    def __init__(
        self,
        cache_dir: Path = CACHE_DIR,
        expire_hours: int = CACHE_EXPIRE_HOURS,
    ):

        self.cache_dir = Path(cache_dir)

        self.cache_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.expire = expire_hours * 3600

        self.memory: dict[str, CacheItem] = {}

        self.lock = Lock()

    # --------------------------------------------------------

    def _path(
        self,
        key: str,
    ) -> Path:

        safe = (
            key.replace("/", "_")
               .replace("\\", "_")
               .replace(":", "_")
               .replace("?", "_")
               .replace("&", "_")
               .replace("=", "_")
        )

        return self.cache_dir / f"{safe}.cache"

    # --------------------------------------------------------

    def exists(
        self,
        key: str,
    ) -> bool:

        if key in self.memory:

            return not self.memory[key].expired

        return self._path(key).exists()

    # --------------------------------------------------------

    def clear_memory(self):

        self.memory.clear()

    # --------------------------------------------------------

    def clear_files(self):

        for file in self.cache_dir.glob("*.cache"):

            try:
                file.unlink()

            except Exception:
                pass

    # --------------------------------------------------------

    def clear(self):

        self.clear_memory()

        self.clear_files()

    # --------------------------------------------------------

    def delete(
        self,
        key: str,
    ):

        self.memory.pop(key, None)

        file = self._path(key)

        if file.exists():

            file.unlink()


# ============================================================
# modules/cache.py
# BRN 2.0 Cache Engine
# Sprint 1-1
# Part 2 / 3
# ============================================================

    # --------------------------------------------------------
    # SET
    # --------------------------------------------------------

    def set(
        self,
        key: str,
        value: Any,
    ) -> None:

        if not CACHE_ENABLED:
            return

        item = CacheItem(
            key=key,
            value=value,
            created=time.time(),
            expire=time.time() + self.expire,
        )

        with self.lock:

            self.memory[key] = item

            try:

                with open(
                    self._path(key),
                    "wb",
                ) as fp:

                    pickle.dump(
                        item,
                        fp,
                        protocol=pickle.HIGHEST_PROTOCOL,
                    )

            except Exception as exc:

                raise CacheWriteError(
                    f"Cache write failed: {key}",
                    cause=exc,
                ) from exc

    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:

        if not CACHE_ENABLED:
            return default

        item = self.memory.get(key)

        if item is not None:

            if item.expired:

                self.delete(key)

                return default

            return item.value

        path = self._path(key)

        if not path.exists():

            return default

        try:

            with open(path, "rb") as fp:

                item = pickle.load(fp)

        except Exception as exc:

            raise CacheReadError(
                f"Cache read failed: {key}",
                cause=exc,
            ) from exc

        if item.expired:

            self.delete(key)

            return default

        self.memory[key] = item

        return item.value

    # --------------------------------------------------------
    # TOUCH
    # --------------------------------------------------------

    def touch(
        self,
        key: str,
    ) -> bool:

        item = self.memory.get(key)

        if item is None:

            value = self.get(key)

            if value is None:

                return False

            item = self.memory.get(key)

        if item is None:

            return False

        item.expire = time.time() + self.expire

        self.set(
            key,
            item.value,
        )

        return True

    # --------------------------------------------------------
    # SAVE JSON
    # --------------------------------------------------------

    def save_json(
        self,
        key: str,
        value: Any,
    ) -> None:

        path = self.cache_dir / f"{key}.json"

        try:

            with open(
                path,
                "w",
                encoding="utf-8",
            ) as fp:

                json.dump(
                    value,
                    fp,
                    ensure_ascii=False,
                    indent=2,
                )

        except Exception as exc:

            raise CacheWriteError(
                f"JSON cache write failed: {key}",
                cause=exc,
            ) from exc

    # --------------------------------------------------------
    # LOAD JSON
    # --------------------------------------------------------

    def load_json(
        self,
        key: str,
        default: Any = None,
    ) -> Any:

        path = self.cache_dir / f"{key}.json"

        if not path.exists():

            return default

        try:

            with open(
                path,
                "r",
                encoding="utf-8",
            ) as fp:

                return json.load(fp)

        except Exception as exc:

            raise CacheReadError(
                f"JSON cache read failed: {key}",
                cause=exc,
            ) from exc



# ============================================================
# modules/cache.py
# BRN 2.0 Cache Engine
# Sprint 1-1
# Part 3 / 3
# ============================================================

    # --------------------------------------------------------
    # STATS
    # --------------------------------------------------------

    def stats(self) -> dict[str, Any]:

        file_count = len(
            list(
                self.cache_dir.glob("*.cache")
            )
        )

        json_count = len(
            list(
                self.cache_dir.glob("*.json")
            )
        )

        memory_count = len(self.memory)

        return {

            "enabled": CACHE_ENABLED,

            "memory_items": memory_count,

            "cache_files": file_count,

            "json_files": json_count,

            "expire_hours": self.expire / 3600,

            "cache_dir": str(self.cache_dir),

        }

    # --------------------------------------------------------
    # CLEANUP
    # --------------------------------------------------------

    def cleanup(self) -> int:

        removed = 0

        for path in self.cache_dir.glob("*.cache"):

            try:

                with open(path, "rb") as fp:

                    item = pickle.load(fp)

                if item.expired:

                    path.unlink()

                    removed += 1

            except Exception:

                try:

                    path.unlink()

                    removed += 1

                except Exception:
                    pass

        expired = [

            key
            for key, item
            in self.memory.items()
            if item.expired

        ]

        for key in expired:

            self.memory.pop(
                key,
                None,
            )

        return removed

    # --------------------------------------------------------
    # MAGIC METHODS
    # --------------------------------------------------------

    def __contains__(
        self,
        key: str,
    ) -> bool:

        return self.exists(key)

    def __getitem__(
        self,
        key: str,
    ) -> Any:

        value = self.get(key)

        if value is None:

            raise KeyError(key)

        return value

    def __setitem__(
        self,
        key: str,
        value: Any,
    ) -> None:

        self.set(
            key,
            value,
        )

    def __delitem__(
        self,
        key: str,
    ) -> None:

        self.delete(key)

    def __len__(self) -> int:

        return len(self.memory)

    def __repr__(self) -> str:

        return (

            f"Cache("

            f"memory={len(self.memory)}, "

            f"dir='{self.cache_dir}')"

        )


# ============================================================
# SINGLETON
# ============================================================

cache = Cache()


# ============================================================
# EXPORT
# ============================================================

__all__ = [

    "Cache",

    "CacheItem",

    "cache",

]



