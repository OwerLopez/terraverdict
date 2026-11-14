from typing import Any

from fastapi.testclient import TestClient

from tests.conftest import PROCEDENCIA, prueba_tendencia

APROBADA = {"estado": "aprobada"}


def test_expedientes_reales_preliminares(cliente: TestClient) -> None:
    pagina = cliente.get("/api/v1/expedientes", params={"tipo": "tendencia"}).json()
    assert pagina["total"] == 2
    detalle = cliente.get(f"/api/v1/expedientes/{pagina['items'][0]['id']}").json()
    assert detalle["resultado"]["veredicto"] == "preliminar"
    assert detalle["resultado"]["sello"]["independencia"]["estado"] == "pendiente"
    assert len(detalle["procedencia"]["pasos"]) == 9
    assert detalle["id"].startswith("TV-TEN-")


def test_publicacion_idempotente(cliente: TestClient, ingesta: dict[str, str]) -> None:
    r1 = cliente.post("/api/v1/expedientes", json=prueba_tendencia(), headers=ingesta)
    r2 = cliente.post("/api/v1/expedientes", json=prueba_tendencia(), headers=ingesta)
    assert (r1.status_code, r2.status_code) == (201, 200)
    assert r1.json()["id"] == r2.json()["id"]
    assert r1.headers["location"].endswith(r1.json()["id"])


def test_regla_robusta_exige_sello_completo(cliente: TestClient, ingesta: dict[str, str]) -> None:
    datos = prueba_tendencia(
        veredicto="robusta",
        significancia={"p_mann_kendall": 0.01, "p_conservador": 0.01},
    )
    r = cliente.post("/api/v1/expedientes", json=datos, headers=ingesta)
    assert r.status_code == 422
    assert "cinco pruebas" in str(r.json()["errores"])


def test_regla_p_conservador(cliente: TestClient, ingesta: dict[str, str]) -> None:
    datos = prueba_tendencia(significancia={"p_mann_kendall": 0.2, "p_hamed_rao": 0.3, "p_conservador": 0.2})
    assert cliente.post("/api/v1/expedientes", json=datos, headers=ingesta).status_code == 422


def test_robusta_valida_cuando_todo_aprueba(cliente: TestClient, ingesta: dict[str, str]) -> None:
    sello = dict.fromkeys(("ventanas", "enso", "sensor", "independencia", "detectabilidad"), APROBADA)
    datos = prueba_tendencia(
        veredicto="robusta", sello=sello, significancia={"p_mann_kendall": 0.01, "p_conservador": 0.01}
    )
    assert cliente.post("/api/v1/expedientes", json=datos, headers=ingesta).status_code == 201


def _pronostico(publicable: bool, lo: float) -> dict[str, Any]:
    return {
        "dominio_id": "chili_analisis",
        "unidad_id": "chili_analisis.el_frayle",
        "titulo": "Pronóstico de prueba de contrato",
        "resumen": "Expediente sintético usado solo por las pruebas automatizadas.",
        "procedencia": PROCEDENCIA,
        "resultado": {
            "tipo": "pronostico",
            "emitido_utc": "2026-11-14T00:00:00Z",
            "fin_horizonte": "2027-04-30",
            "variable_objetivo": "volumen_util",
            "umbral": {"valor": 200, "unidad": "hm3"},
            "cuantiles": {"p10": 100, "p50": 200, "p90": 300, "unidad": "hm3"},
            "prob_bajo_umbral": 0.5,
            "habilidad": {"crpss": 0.1, "intervalo": {"lo": lo, "hi": 0.2}, "anios_evaluados": 25},
            "publicable": publicable,
        },
    }


def test_pronostico_sin_habilidad_no_es_publicable(cliente: TestClient, ingesta: dict[str, str]) -> None:
    assert (
        cliente.post("/api/v1/expedientes", json=_pronostico(True, -0.05), headers=ingesta).status_code == 422
    )
    assert (
        cliente.post("/api/v1/expedientes", json=_pronostico(False, -0.05), headers=ingesta).status_code
        == 201
    )
    assert (
        cliente.post("/api/v1/expedientes", json=_pronostico(True, 0.02), headers=ingesta).status_code == 201
    )


def test_referencias_inexistentes(cliente: TestClient, ingesta: dict[str, str]) -> None:
    datos = prueba_tendencia()
    datos["procedencia"] = {**PROCEDENCIA, "fuentes": [{"fuente_id": "inventada"}]}
    r = cliente.post("/api/v1/expedientes", json=datos, headers=ingesta)
    assert r.status_code == 404 and "procedencia.fuentes[0]" in r.json()["errores"][0]["campo"]


def test_reemplazo_y_retiro(cliente: TestClient, ingesta: dict[str, str], admin: dict[str, str]) -> None:
    viejo = cliente.post("/api/v1/expedientes", json=prueba_tendencia(n=20), headers=ingesta).json()["id"]
    nuevo = cliente.post(
        "/api/v1/expedientes", json={**prueba_tendencia(n=21), "reemplaza_a": viejo}, headers=ingesta
    ).json()["id"]
    assert cliente.get(f"/api/v1/expedientes/{viejo}").json()["estado"] == "retirado"
    ids = [e["id"] for e in cliente.get("/api/v1/expedientes").json()["items"]]
    assert nuevo in ids and viejo not in ids
    r = cliente.post(
        f"/api/v1/expedientes/{nuevo}/retirar", json={"motivo": "Datos de entrada corregidos."}, headers=admin
    )
    assert r.status_code == 200 and r.json()["motivo_retiro"].startswith("Datos de entrada")
    r = cliente.post(
        f"/api/v1/expedientes/{nuevo}/retirar", json={"motivo": "Segundo intento de retiro."}, headers=admin
    )
    assert r.status_code == 409


def test_matriz_vacia_y_luego_disponible(cliente: TestClient, ingesta: dict[str, str]) -> None:
    vacia = cliente.get("/api/v1/relevancia/matriz").json()
    assert vacia["estado"] == "vacia" and vacia["celdas"] == [] and len(vacia["problemas"]) == 4
    relevancia = {
        "dominio_id": "chili_analisis",
        "titulo": "Relevancia de prueba de contrato",
        "resumen": "Expediente sintético usado solo por las pruebas automatizadas.",
        "procedencia": PROCEDENCIA,
        "resultado": {
            "tipo": "relevancia",
            "problema_id": "P1",
            "version_modelo": "v0-prueba",
            "particion_prueba": "2021-2025",
            "habilidad": {
                "metrica": "AUC-PR",
                "valor": 0.3,
                "intervalo": {"lo": 0.1, "hi": 0.4},
                "linea_base": "climatologia",
                "supera_linea_base": True,
            },
            "variables": [
                {
                    "variable_id": "indice_oni",
                    "importancia": 0.7,
                    "estabilidad": 0.9,
                    "p_ajustado": 0.01,
                    "direccion": "negativa",
                }
            ],
            "publicable": True,
        },
    }
    assert cliente.post("/api/v1/expedientes", json=relevancia, headers=ingesta).status_code == 201
    matriz = cliente.get("/api/v1/relevancia/matriz").json()
    assert matriz["estado"] == "disponible"
    assert matriz["celdas"][0]["variable_id"] == "indice_oni"
