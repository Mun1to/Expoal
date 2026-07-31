"""Aislamiento de los tests respecto a los datos reales del usuario.

CRÍTICO: settings.py e history.py escriben en el directorio de datos de quien
ejecuta la app (%LOCALAPPDATA%\\Expoal). Sin esta fixture, correr los tests le
cambiaría a alguien sus ajustes de verdad, que es la peor sorpresa posible.
"""
from __future__ import annotations

import pytest

from expoal import config


@pytest.fixture(autouse=True)
def datos_aislados(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "SETTINGS_FILE", tmp_path / "settings.json")
    monkeypatch.setattr(config, "HISTORY_FILE", tmp_path / "history.json")
    return tmp_path
