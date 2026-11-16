"""Portada: tabla maestra derivada de expedientes y regla de evidencia (estructuras sintéticas)."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from app.api.v1.portada import evidencia
from tests.test_fenomenos import _comparacion, _publicar


def test_regla_de_evidencia() -> None:
    assert evidencia(0.04, 0.03) == "confirmada"
    assert evidencia(0.04, 0.2) == "indicio"
    assert evidencia(-0.01, 0.05) == "indicio"
    assert evidencia(-0.01, 0.5) == "sin_evidencia"
    assert evidencia(None, None) == "sin_evidencia"


def test_portada_sin_expedientes_no_inventa(cliente: TestClient) -> None:
    r = cliente.get("/api/v1/portada")
    assert r.status_code == 200, r.text
    filas = {f["fenomeno"]: f for f in r.json()["filas"]}
    assert set(filas) == {"lluvia_extrema", "sequia", "sismos", "volcanes", "deslizamientos"}
    assert filas["lluvia_extrema"]["anticipacion"] is None
    assert filas["lluvia_extrema"]["veredicto"] == "abstencion"
    assert filas["sismos"]["tendencia"] is None


def test_portada_usa_el_modelo_elegido_en_validacion(cliente: TestClient, ingesta: dict[str, str]) -> None:
    # gru tiene mejor cifra en la prueba, pero la validación eligió logística: la portada debe mostrar logística.
    assert _publicar(cliente, ingesta, _comparacion()).status_code == 201
    fila: dict[str, Any] = next(f for f in cliente.get("/api/v1/portada").json()["filas"] if f["fenomeno"] == "lluvia_extrema")
    a = fila["anticipacion"]
    assert a["modelo"] == "logistica" and a["valor"] == 0.10
    assert a["evidencia"] == "confirmada" and fila["veredicto"] == "habilidad_confirmada"
    assert a["expediente_id"].startswith("TV-CMP-")


def test_eventos_documentados_citables_y_verificables() -> None:
    from app.services import asistente, verificador

    c = asistente.contexto_evento(
        "2024-03-colmatacion-aguada-blanca",
        "2024-03-01",
        "Aguada Blanca pierde cerca de la mitad de su capacidad por sedimentos",
        "Capacidad de diseño frente a capacidad actual estimada.",
        [{"valor": 43, "unidad": "hm3", "descripcion": "Capacidad de diseño"}, {"valor": 22, "unidad": "hm3", "descripcion": "Capacidad actual estimada"}],
        ["https://example.org/nota"],
    )
    assert asistente.PATRON_ID.fullmatch(c.id) and c.id.startswith("TV-EV-")
    assert c.id == asistente.id_evento("2024-03-colmatacion-aguada-blanca")  # estable
    permitidos = verificador.valores_numericos(c.resultado)
    assert 43 in permitidos and 22 in permitidos
    assert asistente.seleccionar("¿Por qué Aguada Blanca perdió capacidad?", [c]) == [c]
