from typing import Any

from fastapi.testclient import TestClient

from tests.conftest import PROCEDENCIA

SERIE = {
    "id": "chili_analisis.cabecera_power:precipitacion:imerg_final_mensual:p1m",
    "dominio_id": "chili_analisis",
    "unidad_id": "chili_analisis.cabecera_power",
    "variable_id": "precipitacion",
    "fuente_id": "imerg_final_mensual",
    "unidad": "mm",
    "frecuencia": "P1M",
    "descripcion": "Serie de prueba de contrato (no es un dato real).",
    "procedencia": PROCEDENCIA,
}


def _crear(cliente: TestClient, ingesta: dict[str, str], **cambios: Any) -> Any:
    return cliente.post("/api/v1/series", json={**SERIE, **cambios}, headers=ingesta)


def test_lectura_publica_de_series_reales(cliente: TestClient) -> None:
    r = cliente.get("/api/v1/series", params={"variable_id": "temperatura_aire_2m"}).json()
    assert r["total"] == 1
    serie = r["items"][0]
    assert serie["n_observaciones"] == 44 and serie["t_inicio"] == "1981-01-01"
    assert serie["procedencia"]["fuentes"][0]["fuente_id"] == "power_mensual"


def test_crear_serie_requiere_ingesta(
    cliente: TestClient, lector: dict[str, str], ingesta: dict[str, str]
) -> None:
    assert _crear(cliente, {}).status_code == 401
    assert _crear(cliente, lector).status_code == 403
    assert _crear(cliente, ingesta).status_code == 201
    assert _crear(cliente, ingesta).status_code == 409


def test_contrato_de_serie(cliente: TestClient, ingesta: dict[str, str]) -> None:
    assert _crear(cliente, ingesta, unidad="pulgadas").status_code == 422
    assert _crear(cliente, ingesta, id="Mayusculas:no").status_code == 422
    r = _crear(cliente, ingesta, variable_id="no_existe")
    assert r.status_code == 404 and r.json()["errores"][0]["campo"] == "variable_id"


def test_carga_idempotente_y_versionado(cliente: TestClient, ingesta: dict[str, str]) -> None:
    _crear(cliente, ingesta)
    url = f"/api/v1/series/{SERIE['id']}/observaciones"
    carga = {"observaciones": [{"t": "2020-01-01", "valor": 10.5}, {"t": "2020-02-01", "valor": None}]}
    r = cliente.put(url, json=carga, headers=ingesta).json()
    assert (r["insertadas"], r["actualizadas"], r["version"]) == (2, 0, 2)
    r = cliente.put(url, json=carga, headers=ingesta).json()
    assert (r["insertadas"], r["actualizadas"], r["version"]) == (0, 0, 2)
    r = cliente.put(url, json={"observaciones": [{"t": "2020-01-01", "valor": 11.0}]}, headers=ingesta).json()
    assert (r["actualizadas"], r["version"], r["n_observaciones"]) == (1, 3, 2)
    obs = cliente.get(url).json()["observaciones"]
    assert obs[1]["valor"] is None


def test_carga_rechaza_no_finitos_y_duplicados(cliente: TestClient, ingesta: dict[str, str]) -> None:
    _crear(cliente, ingesta)
    url = f"/api/v1/series/{SERIE['id']}/observaciones"
    duplicadas = {"observaciones": [{"t": "2020-01-01", "valor": 1}, {"t": "2020-01-01", "valor": 2}]}
    assert cliente.put(url, json=duplicadas, headers=ingesta).status_code == 422
    fuera_de_rango = {"observaciones": [{"t": "2020-01-01", "valor": 1, "frac_valida": 1.5}]}
    assert cliente.put(url, json=fuera_de_rango, headers=ingesta).status_code == 422


def test_etag_y_filtros(cliente: TestClient) -> None:
    sid = cliente.get(
        "/api/v1/series", params={"variable_id": "precipitacion", "fuente_id": "power_mensual"}
    ).json()["items"][0]["id"]
    r = cliente.get(
        f"/api/v1/series/{sid}/observaciones", params={"desde": "2000-01-01", "hasta": "2005-12-31"}
    )
    assert all("2000" <= o["t"] <= "2005-12-31" for o in r.json()["observaciones"])
    r2 = cliente.get(
        f"/api/v1/series/{sid}/observaciones",
        params={"desde": "2000-01-01", "hasta": "2005-12-31"},
        headers={"If-None-Match": r.headers["etag"]},
    )
    assert r2.status_code == 304


def test_unidades_y_geojson(cliente: TestClient, ingesta: dict[str, str]) -> None:
    fc = cliente.get("/api/v1/dominios/chili_analisis/unidades").json()
    represas = [f for f in fc["features"] if f["properties"]["tipo"] == "represa"]
    assert len(represas) == 7 and all(f["geometry"] is None for f in represas)
    poligono = {
        "type": "Polygon",
        "coordinates": [[[-71.2, -16.0], [-71.1, -16.0], [-71.1, -15.9], [-71.2, -16.0]]],
    }
    r = cliente.put(
        "/api/v1/unidades/chili_analisis.el_frayle/geometria",
        json={"geometria": poligono, "estado_geometria": "aproximada"},
        headers=ingesta,
    )
    assert r.status_code == 200 and r.json()["estado_geometria"] == "aproximada"
