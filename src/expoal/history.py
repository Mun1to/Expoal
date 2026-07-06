"""Historial de descargas persistido en JSON dentro del directorio de datos del usuario."""
from __future__ import annotations

import json
import threading
from pathlib import Path

MAX_ENTRIES = 200


class History:
    def __init__(self, path: Path):
        self._path = path
        self._lock = threading.Lock()
        self._entries: list[dict] = self._load()

    def _load(self) -> list[dict]:
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (OSError, ValueError):
            return []

    def add(self, entry: dict) -> None:
        with self._lock:
            self._entries.insert(0, entry)
            del self._entries[MAX_ENTRIES:]
            self._save()

    def entries(self) -> list[dict]:
        with self._lock:
            return list(self._entries)

    def clear(self) -> None:
        with self._lock:
            self._entries = []
            self._save()

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(self._entries, ensure_ascii=False, indent=2), encoding="utf-8"
        )
