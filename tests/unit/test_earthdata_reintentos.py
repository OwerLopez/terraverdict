"""Cliente IMERG: reintentos ante límite de tasa de GES DISC, sin red."""

from __future__ import annotations

from types import SimpleNamespace

from terraverdict.ingest.earthdata import pedir_con_reintentos


def _servidor(codigos: list[int]):
    llamadas = []

    def get(url: str) -> SimpleNamespace:
        llamadas.append(url)
        return SimpleNamespace(status_code=codigos[min(len(llamadas) - 1, len(codigos) - 1)])

    return get, llamadas


def test_401_transitorio_se_reintenta_con_espera_exponencial() -> None:
    get, llamadas = _servidor([401, 429, 200])
    esperas: list[float] = []
    r = pedir_con_reintentos(get, "u", dormir=esperas.append)
    assert r.status_code == 200 and len(llamadas) == 3 and esperas == [2.0, 4.0]


def test_403_licencia_no_se_reintenta() -> None:
    get, llamadas = _servidor([403])
    assert pedir_con_reintentos(get, "u", dormir=lambda _: None).status_code == 403
    assert len(llamadas) == 1


def test_reintentos_acotados() -> None:
    get, llamadas = _servidor([401])
    assert pedir_con_reintentos(get, "u", intentos=4, dormir=lambda _: None).status_code == 401
    assert len(llamadas) == 4
