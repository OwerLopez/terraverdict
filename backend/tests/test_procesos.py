from fastapi.testclient import TestClient

from tests.conftest import prueba_tendencia

SERIE_REAL = "chili_analisis.cabecera_power:precipitacion:power_mensual:p1y"


def _solicitar(cliente: TestClient, quien: dict[str, str], **parametros: object) -> dict:
    r = cliente.post("/api/v1/procesos", json={"tipo": "tendencia", "parametros": parametros}, headers=quien)
    assert r.status_code == 201, r.text
    return r.json()


def test_solicitud_requiere_analista_y_parametros(
    cliente: TestClient, lector: dict[str, str], analista: dict[str, str]
) -> None:
    assert (
        cliente.post(
            "/api/v1/procesos", json={"tipo": "tendencia", "parametros": {}}, headers=lector
        ).status_code
        == 403
    )
    r = cliente.post("/api/v1/procesos", json={"tipo": "tendencia", "parametros": {}}, headers=analista)
    assert r.status_code == 400 and r.json()["errores"][0]["campo"] == "parametros.serie_id"


def test_ciclo_completo_del_trabajador(
    cliente: TestClient, analista: dict[str, str], trabajador: dict[str, str], ingesta: dict[str, str]
) -> None:
    assert (
        cliente.post(
            "/api/v1/procesos/reclamar",
            json={"trabajador": "worker-01", "tipos": ["tendencia"]},
            headers=trabajador,
        ).status_code
        == 204
    )
    proceso = _solicitar(cliente, analista, serie_id=SERIE_REAL)
    assert proceso["estado"] == "pendiente"

    r = cliente.post(
        "/api/v1/procesos/reclamar",
        json={"trabajador": "worker-01", "tipos": ["tendencia"]},
        headers=trabajador,
    )
    assert r.status_code == 200 and r.json()["id"] == proceso["id"] and r.json()["estado"] == "en_curso"

    url = f"/api/v1/procesos/{proceso['id']}"
    assert (
        cliente.post(f"{url}/eventos", json={"mensaje": "Descargando IMERG"}, headers=trabajador).status_code
        == 201
    )
    assert cliente.patch(url, json={"progreso": 0.5}, headers=trabajador).json()["progreso"] == 0.5

    r = cliente.patch(url, json={"estado": "completado"}, headers=trabajador)
    assert r.status_code == 400
    exp = cliente.post("/api/v1/expedientes", json=prueba_tendencia(), headers=ingesta).json()["id"]
    r = cliente.patch(url, json={"estado": "completado", "expediente_id": exp}, headers=trabajador)
    assert r.status_code == 200 and r.json()["finalizado_en"] is not None

    r = cliente.patch(url, json={"estado": "en_curso"}, headers=trabajador)
    assert r.status_code == 409 and r.json()["codigo"] == "transicion_invalida"

    bitacora = [e["mensaje"] for e in cliente.get(f"{url}/eventos").json()]
    assert bitacora[0].startswith("Solicitado") and "Descargando IMERG" in bitacora
    ultimo_id = cliente.get(f"{url}/eventos").json()[-1]["id"]
    assert cliente.get(f"{url}/eventos", params={"desde_id": ultimo_id}).json() == []


def test_otro_trabajador_no_puede_tocar(
    cliente: TestClient, analista: dict[str, str], trabajador: dict[str, str], otro_trabajador: dict[str, str]
) -> None:
    proceso = _solicitar(cliente, analista, serie_id=SERIE_REAL)
    cliente.post(
        "/api/v1/procesos/reclamar",
        json={"trabajador": "worker-01", "tipos": ["tendencia"]},
        headers=trabajador,
    )
    url = f"/api/v1/procesos/{proceso['id']}"
    assert cliente.patch(url, json={"progreso": 0.1}, headers=otro_trabajador).status_code == 403
    assert cliente.post(f"{url}/eventos", json={"mensaje": "x"}, headers=otro_trabajador).status_code == 403


def test_persona_solo_puede_cancelar(cliente: TestClient, analista: dict[str, str]) -> None:
    proceso = _solicitar(cliente, analista, serie_id=SERIE_REAL)
    url = f"/api/v1/procesos/{proceso['id']}"
    assert cliente.patch(url, json={"progreso": 0.3}, headers=analista).status_code == 403
    r = cliente.patch(url, json={"estado": "cancelado"}, headers=analista)
    assert r.status_code == 200 and r.json()["estado"] == "cancelado"


def test_fallo_exige_error_y_resumen_cuenta_trabajadores(
    cliente: TestClient, analista: dict[str, str], trabajador: dict[str, str]
) -> None:
    proceso = _solicitar(cliente, analista, serie_id=SERIE_REAL)
    cliente.post(
        "/api/v1/procesos/reclamar",
        json={"trabajador": "worker-01", "tipos": ["tendencia"]},
        headers=trabajador,
    )
    url = f"/api/v1/procesos/{proceso['id']}"
    assert cliente.patch(url, json={"estado": "fallido"}, headers=trabajador).status_code == 400
    r = cliente.patch(
        url, json={"estado": "fallido", "error": {"mensaje": "IMERG no respondió"}}, headers=trabajador
    )
    assert r.status_code == 200 and r.json()["error"]["mensaje"] == "IMERG no respondió"
    assert cliente.get("/api/v1/resumen").json()["trabajadores_activos"] == 1


def test_prioridad_en_la_cola(
    cliente: TestClient, analista: dict[str, str], trabajador: dict[str, str]
) -> None:
    _solicitar(cliente, analista, serie_id="a")
    urgente = cliente.post(
        "/api/v1/procesos",
        json={"tipo": "tendencia", "parametros": {"serie_id": "b"}, "prioridad": 9},
        headers=analista,
    ).json()
    r = cliente.post(
        "/api/v1/procesos/reclamar",
        json={"trabajador": "worker-01", "tipos": ["tendencia"]},
        headers=trabajador,
    )
    assert r.json()["id"] == urgente["id"]
