from typing import Any

from fastapi.testclient import TestClient

from tests.conftest import CONTRASENA


def test_salud_y_cabeceras(cliente: TestClient) -> None:
    r = cliente.get("/api/v1/salud", headers={"X-Request-ID": "prueba-12345678"})
    assert r.status_code == 200
    assert r.headers["x-request-id"] == "prueba-12345678"
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert "default-src 'none'" in r.headers["content-security-policy"]
    assert cliente.get("/api/v1/salud/lista").json() == {"mensaje": "lista"}


def test_request_id_invalido_se_reemplaza(cliente: TestClient) -> None:
    r = cliente.get("/api/v1/salud", headers={"X-Request-ID": "<script>"})
    assert r.headers["x-request-id"] != "<script>"
    assert len(r.headers["x-request-id"]) == 32


def test_errores_en_formato_problem_json(cliente: TestClient) -> None:
    r = cliente.get("/api/v1/fuentes/no-existe")
    assert r.status_code == 404
    assert r.headers["content-type"] == "application/problem+json"
    cuerpo = r.json()
    assert cuerpo["codigo"] == "no_encontrado"
    assert cuerpo["instance"] == "/api/v1/fuentes/no-existe"
    assert cuerpo["request_id"] == r.headers["x-request-id"]


def test_error_no_controlado_conserva_request_id(app: Any) -> None:
    """Un 500 debe poder rastrearse: request_id en el cuerpo y en la cabecera, sin filtrar la traza."""

    @app.get("/api/v1/_prueba_fallo")
    def _fallo() -> None:
        raise RuntimeError("detalle interno que no debe filtrarse")

    r = TestClient(app).get("/api/v1/_prueba_fallo", headers={"X-Request-ID": "incidente-0001"})
    assert r.status_code == 500
    assert r.headers["content-type"] == "application/problem+json"
    assert r.headers["x-request-id"] == "incidente-0001"
    assert r.headers["x-content-type-options"] == "nosniff"
    cuerpo = r.json()
    assert cuerpo["codigo"] == "error_interno"
    assert cuerpo["request_id"] == "incidente-0001"
    assert "detalle interno" not in r.text


def test_validacion_devuelve_errores_por_campo(cliente: TestClient, admin: dict[str, str]) -> None:
    r = cliente.post(
        "/api/v1/usuarios", json={"email": "malo", "nombre": "x", "contrasena": "corta"}, headers=admin
    )
    assert r.status_code == 422
    campos = {e["campo"] for e in r.json()["errores"]}
    assert {"body.email", "body.nombre", "body.contrasena"} <= campos


def test_login_y_identidad(cliente: TestClient, analista: dict[str, str]) -> None:
    yo = cliente.get("/api/v1/auth/yo", headers=analista).json()
    assert yo["tipo"] == "usuario" and yo["rol"] == "analista"


def test_login_fallido_y_limite(cliente: TestClient) -> None:
    for _ in range(5):
        r = cliente.post("/api/v1/auth/token", data={"username": "lector@tv.pe", "password": "incorrecta"})
        assert r.status_code == 401
        assert r.headers["www-authenticate"] == "Bearer"
    r = cliente.post("/api/v1/auth/token", data={"username": "lector@tv.pe", "password": CONTRASENA})
    assert r.status_code == 429
    assert r.json()["codigo"] == "demasiadas_solicitudes"


def test_token_invalido(cliente: TestClient) -> None:
    r = cliente.get("/api/v1/auth/yo", headers={"Authorization": "Bearer no-es-un-jwt"})
    assert r.status_code == 401 and r.json()["codigo"] == "no_autenticado"


def test_rbac_usuarios(cliente: TestClient, admin: dict[str, str], lector: dict[str, str]) -> None:
    assert cliente.get("/api/v1/usuarios", headers=lector).status_code == 403
    assert cliente.get("/api/v1/usuarios").status_code == 401
    nuevo = {
        "email": "nueva@tv.pe",
        "nombre": "Nueva",
        "contrasena": "una-contrasena-larga",
        "rol": "analista",
    }
    r = cliente.post("/api/v1/usuarios", json=nuevo, headers=admin)
    assert r.status_code == 201 and r.json()["rol"] == "analista"
    assert cliente.post("/api/v1/usuarios", json=nuevo, headers=admin).status_code == 409


def test_usuario_desactivado_pierde_acceso(
    cliente: TestClient, admin: dict[str, str], lector: dict[str, str]
) -> None:
    uid = cliente.get("/api/v1/auth/yo", headers=lector).json()["id"]
    assert cliente.patch(f"/api/v1/usuarios/{uid}", json={"activo": False}, headers=admin).status_code == 200
    assert cliente.get("/api/v1/auth/yo", headers=lector).status_code == 401


def test_claves_api_ciclo(cliente: TestClient, admin: dict[str, str]) -> None:
    r = cliente.post("/api/v1/claves", json={"nombre": "pipeline", "alcances": ["ingesta"]}, headers=admin)
    assert r.status_code == 201
    clave, cid = r.json()["clave"], r.json()["id"]
    assert clave.startswith("tv_")
    listado = cliente.get("/api/v1/claves", headers=admin).json()
    assert all("clave" not in c for c in listado)
    yo = cliente.get("/api/v1/auth/yo", headers={"X-API-Key": clave}).json()
    assert yo["tipo"] == "servicio" and yo["alcances"] == ["ingesta"]
    assert cliente.delete(f"/api/v1/claves/{cid}", headers=admin).status_code == 204
    assert cliente.get("/api/v1/auth/yo", headers={"X-API-Key": clave}).status_code == 401


def test_resumen_refleja_datos_reales(cliente: TestClient) -> None:
    r = cliente.get("/api/v1/resumen").json()
    assert r["fuentes_total"] >= 30
    assert r["verificacion_fuentes"]["correctas"] == 37
    assert r["eventos_documentados"] >= 10
    assert r["asistente_conectado"] is False
    assert {"clave": "tendencia", "total": 2} in r["expedientes_por_tipo"]


def test_unidades_medida(cliente: TestClient) -> None:
    codigos = {u["codigo"] for u in cliente.get("/api/v1/unidades-medida").json()}
    assert {"mm", "Cel", "hm3", "m3/s", "NTU"} <= codigos


def test_eventos_distinguen_cifras_exactas_de_cotas(cliente: TestClient) -> None:
    eventos = {e["id"]: e for e in cliente.get("/api/v1/eventos").json()}
    turbidez = eventos["2025-02-corte-turbidez"]["cifras"]
    assert turbidez[0] == {
        "valor": 5000,
        "unidad": "NTU",
        "descripcion": "Turbidez registrada en la captación",
        "cota": "exacta",
    }
    assert turbidez[1]["cota"] == "minima"  # la fuente dice "más del 70 %"
    assert all(e["fuentes"] for e in eventos.values()), "todo evento debe citar al menos una fuente"
