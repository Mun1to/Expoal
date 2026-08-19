"""Auto-update: lo que decide si un instalador descargado se llega a ejecutar.

Es el módulo que corre un .exe en el equipo de alguien, así que su
comprobación de integridad es lo único que separa "actualizar" de "ejecutar
lo que sea que haya llegado".
"""
from __future__ import annotations

import hashlib

import pytest

from expoal import updater


@pytest.fixture()
def descarga(tmp_path, monkeypatch):
    """Una actualización lista para instalar, con el archivo ya en disco."""
    archivo = tmp_path / "Expoal-9.9.9-setup.exe"
    archivo.write_bytes(b"instalador de mentira")
    monkeypatch.setattr(updater, "check_for_update", lambda force=False: {
        "update_available": True, "version": "9.9.9",
        "installer_url": "https://github.com/x/y/releases/download/v9.9.9/Expoal-9.9.9-setup.exe",
        "checksums_url": "https://github.com/x/y/releases/download/v9.9.9/SHA256SUMS.txt",
        "can_auto_install": True,
    })
    monkeypatch.setattr(updater, "_download", lambda url, dst: dst.write_bytes(archivo.read_bytes()))
    monkeypatch.setattr(updater.tempfile, "gettempdir", lambda: str(tmp_path))
    monkeypatch.setattr(updater, "running_appimage", lambda: None)
    monkeypatch.setattr(updater, "_update_windows", lambda dst: {"ok": True, "instalado": str(dst)})
    return archivo


def test_un_checksum_correcto_deja_instalar(descarga, monkeypatch):
    bueno = hashlib.sha256(descarga.read_bytes()).hexdigest()
    monkeypatch.setattr(updater, "_expected_sha256", lambda url, name: bueno)
    assert updater.apply_update()["ok"] is True


def test_un_checksum_distinto_aborta(descarga, monkeypatch):
    monkeypatch.setattr(updater, "_expected_sha256", lambda url, name: "0" * 64)
    result = updater.apply_update()
    assert result["ok"] is False and "checksum" in result["error"]


def test_si_el_checksum_no_se_puede_leer_NO_se_instala(descarga, monkeypatch):
    # El fallo que arregla: `_expected_sha256` devuelve None ante cualquier
    # tropiezo (red, timeout, el nombre del asset cambiado), y eso valía lo
    # mismo que "este release no publica checksums". Resultado: la comprobación
    # se apagaba sola, en silencio, y se lanzaba el instalador igual.
    monkeypatch.setattr(updater, "_expected_sha256", lambda url, name: None)
    result = updater.apply_update()
    assert result["ok"] is False
    assert "checksum" in result["error"]


def test_el_archivo_sin_verificar_no_se_queda_en_disco(descarga, monkeypatch, tmp_path):
    monkeypatch.setattr(updater, "_expected_sha256", lambda url, name: None)
    updater.apply_update()
    assert not (tmp_path / "descargado" / "Expoal-9.9.9-setup.exe").exists()


# --- Comparación de versiones ---

@pytest.mark.parametrize("texto,esperado", [
    ("2.5.3", (2, 5, 3)),
    ("v2.5.3", (2, 5, 3)),
    ("2.5", (2, 5, 0)),
    ("2", (2, 0, 0)),
    ("2.5.3-beta", (2, 5, 3)),
    ("", (0, 0, 0)),
])
def test_la_version_se_lee_venga_como_venga(texto, esperado):
    # El nombre del tag lo escribe una persona: no puede tumbar el aviso.
    assert updater._parse_version(texto) == esperado
