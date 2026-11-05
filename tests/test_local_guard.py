"""El filtro de cabeceras Host y Origin: solo la propia interfaz local puede usar la API."""
from __future__ import annotations

import asyncio

import pytest

from expoal import server

PORT = 8710


def _call(method: str, path: str, headers: dict[str, str]) -> int:
    """Llama a la app ASGI directamente, sin red y sin dependencias extra."""
    raw = [(k.lower().encode(), v.encode()) for k, v in headers.items()]
    scope = {
        "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
        "method": method, "path": path, "raw_path": path.encode(), "query_string": b"",
        "headers": raw, "client": ("127.0.0.1", 50000), "server": ("127.0.0.1", PORT),
        "scheme": "http", "root_path": "",
    }
    status: list[int] = []

    async def receive():
        return {"type": "http.request", "body": b"{}", "more_body": False}

    async def send(message):
        if message["type"] == "http.response.start":
            status.append(message["status"])

    asyncio.run(server.app(scope, receive, send))
    return status[0]


@pytest.fixture(autouse=True)
def puerto_servido(monkeypatch):
    monkeypatch.setattr(server, "SERVED_PORT", PORT, raising=False)


@pytest.mark.parametrize("host", ["127.0.0.1:8710", "localhost:8710"])
def test_la_interfaz_local_pasa(host):
    assert _call("GET", "/api/config", {"Host": host}) == 200
    origin = f"http://{host}"
    assert _call("GET", "/api/config", {"Host": host, "Origin": origin}) == 200


@pytest.mark.parametrize("host", [
    "dominio-ajeno.example:8710", "dominio-ajeno.example", "127.0.0.1", "127.0.0.1:9999",
    "localhost.example:8710", "",
])
def test_un_host_ajeno_se_rechaza_tambien_en_lecturas(host):
    assert _call("GET", "/api/history", {"Host": host}) == 403


@pytest.mark.parametrize("origin", [
    "http://127.0.0.1:9999", "http://localhost:9999", "https://127.0.0.1:8710",
    "http://evil.example:8710", "null",
])
@pytest.mark.parametrize("method", ["GET", "POST"])
def test_un_origin_de_otro_puerto_o_esquema_se_rechaza(origin, method):
    assert _call(method, "/api/config", {"Host": "127.0.0.1:8710", "Origin": origin}) == 403


def test_sin_puerto_conocido_se_rechaza_todo(monkeypatch):
    monkeypatch.setattr(server, "SERVED_PORT", None, raising=False)
    assert _call("GET", "/api/config", {"Host": "127.0.0.1:8710"}) == 403
