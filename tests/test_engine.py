"""Motor actualizable: qué versión de yt-dlp se considera "la más nueva"."""
from __future__ import annotations

from expoal import engine


def _wheel(version: str, yanked: bool = False) -> dict:
    return {
        "filename": f"yt_dlp-{version}-py3-none-any.whl",
        "url": f"https://files.pythonhosted.org/x/yt_dlp-{version}-py3-none-any.whl",
        "digests": {"sha256": "0" * 64},
        "yanked": yanked,
    }


def test_la_nightly_de_pypi_es_la_misma_version_que_la_instalada():
    # PyPI la llama "2026.8.18.122307.dev0" y ella misma, ya instalada, dice
    # "2026.08.18.122307". Si el "dev0" contara, el aviso de motor nuevo no se
    # iría nunca por mucho que se pulsara el botón.
    assert engine._as_tuple("2026.8.18.122307.dev0") == engine._as_tuple("2026.08.18.122307")
    assert engine._as_tuple("2026.7.4") == engine._as_tuple("2026.07.04")
    assert engine._as_tuple("2026.7.4") < engine._as_tuple("2026.8.18.122307.dev0")


def test_se_coge_lo_mas_nuevo_aunque_sea_de_prueba():
    # "info.version" es solo la última ESTABLE, y cuando YouTube rompe algo el
    # arreglo vive en la nightly durante semanas: por ahí no se llega a él.
    data = {
        "info": {"version": "2026.7.4"},
        "releases": {
            "2026.7.4": [_wheel("2026.7.4")],
            "2026.8.18.122307.dev0": [_wheel("2026.8.18.122307.dev0")],
        },
    }
    latest, wheel = engine._newest_wheel(data)
    assert latest == "2026.8.18.122307.dev0"
    assert wheel["url"].endswith("2026.8.18.122307.dev0-py3-none-any.whl")
    assert engine.is_prerelease(latest) is True
    assert engine.is_prerelease("2026.7.4") is False


def test_lo_retirado_y_lo_que_no_trae_wheel_no_cuenta():
    data = {
        "info": {"version": "2026.7.4"},
        "releases": {
            "2026.7.4": [_wheel("2026.7.4")],
            "2026.8.1": [_wheel("2026.8.1", yanked=True)],       # retirada por PyPI
            "2026.8.2": [{"filename": "yt_dlp-2026.8.2.tar.gz"}],  # sin wheel
        },
    }
    assert engine._newest_wheel(data)[0] == "2026.7.4"
