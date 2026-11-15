"""Fenómenos naturales (M6): tipos de expediente nuevos, sus reglas, el catálogo y las capas del mapa.

Las estructuras son sintéticas y solo prueban el contrato (nunca se importan como datos reales).
"""

from __future__ import annotations

import copy
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.conftest import PROCEDENCIA

ABSTENCION_OK = {"publicar": True, "motivos": [], "advertencias": []}


def _expediente(resultado: dict[str, Any], titulo: str = "Prueba de contrato de fenómenos") -> dict[str, Any]:
    return {
        "dominio_id": "chili_analisis",
        "titulo": titulo,
        "resumen": "Expediente sintético usado solo por las pruebas automatizadas.",
        "resultado": resultado,
        "procedencia": PROCEDENCIA,
    }


def _comparacion(**cambios: Any) -> dict[str, Any]:
    r: dict[str, Any] = {
        "tipo": "comparacion_modelos",
        "fenomeno": "lluvia_extrema",
        "tarea": "clasificacion",
        "objetivo": "lluvia diaria ≥ p90",
        "horizonte": "1 día",
        "metrica_principal": "bss_climatologia",
        "periodo_prueba": {"desde": "2021-01-01", "hasta": "2026-10-31"},
        "modelos": [
            {"nombre": "ref_climatologia", "familia": "referencia", "puntaje_validacion": 0.0},
            {
                "nombre": "logistica",
                "familia": "clasico",
                "puntaje_validacion": 0.12,
                "puntaje_prueba": 0.10,
                "intervalo_prueba": {"lo": 0.04, "hi": 0.17},
                "p_diebold_mariano": 0.03,
            },
            {"nombre": "gru", "familia": "red_neuronal", "puntaje_validacion": 0.11, "puntaje_prueba": 0.13},
        ],
        "mejor_validacion": "logistica",
        "abstencion": ABSTENCION_OK,
    }
    r.update(cambios)
    return r


def _publicar(cliente: TestClient, ingesta: dict[str, str], resultado: dict[str, Any]) -> Any:
    return cliente.post("/api/v1/expedientes", json=_expediente(resultado), headers=ingesta)


def test_comparacion_valida_y_abreviatura(cliente: TestClient, ingesta: dict[str, str]) -> None:
    r = _publicar(cliente, ingesta, _comparacion())
    assert r.status_code == 201, r.text
    assert r.json()["id"].startswith("TV-CMP-") and r.json()["modulo"] == "M6"


@pytest.mark.parametrize(
    ("cambios", "mensaje"),
    [
        ({"mejor_validacion": "gru"}, "mejor en validación"),  # gru es mejor en prueba, no en validación
        ({"mejor_validacion": "ref_climatologia"}, "no sea una referencia"),
        (
            {"modelos": [{"nombre": "logistica", "familia": "clasico", "puntaje_validacion": 0.1}] * 2},
            "repetidos",
        ),
    ],
)
def test_comparacion_reglas(
    cliente: TestClient, ingesta: dict[str, str], cambios: dict[str, Any], mensaje: str
) -> None:
    r = _publicar(cliente, ingesta, _comparacion(**cambios))
    assert r.status_code == 422 and mensaje in str(r.json()["errores"])


def test_comparacion_sin_referencia_o_sin_habilidad(cliente: TestClient, ingesta: dict[str, str]) -> None:
    sin_ref = _comparacion()
    sin_ref["modelos"] = sin_ref["modelos"][1:]
    assert _publicar(cliente, ingesta, sin_ref).status_code == 422
    negativo = _comparacion()
    for m in negativo["modelos"][1:]:
        m["puntaje_validacion"] = -0.05
    assert _publicar(cliente, ingesta, negativo).status_code == 422  # publicar sin habilidad en validación
    negativo["abstencion"] = {"publicar": False, "motivos": ["No supera a la climatología en validación."]}
    assert _publicar(cliente, ingesta, negativo).status_code == 201


def test_abstencion_siempre_motivada(cliente: TestClient, ingesta: dict[str, str]) -> None:
    r = _publicar(cliente, ingesta, _comparacion(abstencion={"publicar": False, "motivos": []}))
    assert r.status_code == 422 and "motivo" in str(r.json()["errores"])


def _serie_caos(**cambios: Any) -> dict[str, Any]:
    s: dict[str, Any] = {
        "serie_id": "oni_mensual",
        "fuente": "NOAA CPC ONI",
        "n": 921,
        "unidad_tiempo": "mes",
        "veredicto": "no_lineal_sin_caos_demostrado",
        "condiciones": {"no_linealidad_significativa": True},
        "espacio_fases": [[0.1, 0.2], [0.2, 0.3]],
    }
    s.update(cambios)
    return s


def test_caos_exige_todas_las_condiciones(cliente: TestClient, ingesta: dict[str, str]) -> None:
    base = {"tipo": "caos", "metodo": "Diagnóstico integrado (sustitutos IAAFT, D2, λ, prueba 0-1)."}
    assert _publicar(cliente, ingesta, {**base, "series": [_serie_caos()]}).status_code == 201
    falso_caos = _serie_caos(veredicto="compatible_con_caos_baja_dimension", d2=1.2, lyapunov=0.4, k_01=0.95)
    r = _publicar(cliente, ingesta, {**base, "series": [falso_caos]})
    assert r.status_code == 422 and "todas las condiciones" in str(r.json()["errores"])
    condiciones = dict.fromkeys(
        (
            "no_linealidad_significativa",
            "determinismo_prediccion_analogos",
            "d2_satura_bajo",
            "lyapunov_positivo",
            "prueba_01_caotica",
        ),
        True,
    )
    caos = _serie_caos(
        serie_id="henon",
        condiciones=condiciones,
        **{k: v for k, v in falso_caos.items() if k in ("veredicto", "d2", "lyapunov", "k_01")},
    )
    assert _publicar(cliente, ingesta, {**base, "series": [caos]}).status_code == 201


def _recurrencia(p: float = 0.008) -> dict[str, Any]:
    return {
        "tipo": "recurrencia",
        "fuente": "Smithsonian GVP",
        "inicio_registro": 1550,
        "metodo": "Poisson n/T; IC exacto de Garwood al 90 %",
        "volcanes": [
            {
                "numero_gvp": 354020,
                "nombre": "Misti, El",
                "lat": -16.294,
                "lon": -71.409,
                "distancia_km": 17.8,
                "erupciones": 4,
                "probabilidad_anual": p,
                "intervalo": {"lo": 0.003, "hi": 0.019},
            }
        ],
        "abstencion": {
            "publicar": False,
            "motivos": ["Sin monitoreo continuo no se pronostican erupciones."],
        },
    }


def _sismicidad() -> dict[str, Any]:
    return {
        "tipo": "sismicidad",
        "fuente": "USGS ComCat",
        "periodo": {"desde": "1973-01-08", "hasta": "2026-10-30"},
        "radio_km": 350,
        "eventos": 4052,
        "mc": 4.5,
        "valor_b": 1.0,
        "intervalo_b": {"lo": 0.96, "hi": 1.03},
        "independientes": 900,
        "tasa_anual_mc": 30.0,
        "mapa": [
            {"fecha": "2001-06-23", "lat": -16.26, "lon": -73.64, "magnitud": 8.4, "profundidad_km": 33},
            {"fecha": "2020-01-01", "lat": -16.0, "lon": -72.0, "magnitud": 5.2},
        ],
    }


def test_recurrencia_dentro_del_intervalo(cliente: TestClient, ingesta: dict[str, str]) -> None:
    assert _publicar(cliente, ingesta, _recurrencia(0.05)).status_code == 422
    r = _publicar(cliente, ingesta, _recurrencia())
    assert r.status_code == 201 and r.json()["resultado"]["es_pronostico"] is False


def test_inventario_no_estima_umbral_con_pocos_eventos(cliente: TestClient, ingesta: dict[str, str]) -> None:
    evento = {"id": "glc-1", "fecha": "2010-02-01", "lat": -15.0, "lon": -72.0, "percentiles": {"3d": 91.0}}
    base = {
        "tipo": "inventario",
        "fenomeno": "deslizamientos",
        "fuente": "NASA GLC",
        "eventos": [evento],
        "eventos_minimos_umbral": 30,
        "abstencion": {"publicar": False, "motivos": ["Solo 1 evento: se necesitan 30."]},
    }
    assert _publicar(cliente, ingesta, {**base, "umbral_estimado": True}).status_code == 422
    assert _publicar(cliente, ingesta, {**base, "umbral_estimado": False}).status_code == 201


def test_pronostico_con_conformal_y_abstencion(cliente: TestClient, ingesta: dict[str, str]) -> None:
    from tests.test_expedientes import _pronostico

    datos = _pronostico(True, 0.05)
    datos["resultado"]["intervalo_conformal"] = {"lo": 250, "hi": 400}  # no contiene la mediana (200)
    assert cliente.post("/api/v1/expedientes", json=datos, headers=ingesta).status_code == 422
    datos["resultado"]["intervalo_conformal"] = {"lo": 120, "hi": 280}
    datos["resultado"]["abstencion"] = {"publicar": False, "motivos": ["Deriva fuerte de las entradas."]}
    assert cliente.post("/api/v1/expedientes", json=datos, headers=ingesta).status_code == 422
    datos["resultado"]["publicable"] = False
    assert cliente.post("/api/v1/expedientes", json=datos, headers=ingesta).status_code == 201


def test_catalogo_de_fenomenos(cliente: TestClient) -> None:
    c = cliente.get("/api/v1/fenomenos").json()
    ids = {f["id"] for f in c["fenomenos"]}
    assert {"lluvia_extrema", "sequia", "sismos", "volcanes", "deslizamientos"} <= ids
    assert "No son alertas oficiales" in c["aviso"]
    assert c["particion_temporal"]["prueba"][0] == "2021-01-01"
    lluvia = cliente.get("/api/v1/fenomenos/lluvia_extrema").json()
    assert all(v["justificacion"] for v in lluvia["variables"])
    assert cliente.get("/api/v1/fenomenos/no_existe").status_code == 404


def test_capas_vacias_sin_expediente(cliente: TestClient) -> None:
    for capa in ("sismos", "volcanes", "deslizamientos"):
        c = cliente.get(f"/api/v1/capas/{capa}").json()
        assert c["features"] == [] and c["expediente_id"] is None and c["nota"]


def test_capas_salen_del_expediente_vigente(
    cliente: TestClient, ingesta: dict[str, str], admin: dict[str, str]
) -> None:
    s = _publicar(cliente, ingesta, _sismicidad()).json()
    v = _publicar(cliente, ingesta, _recurrencia()).json()
    sismos = cliente.get("/api/v1/capas/sismos").json()
    assert sismos["expediente_id"] == s["id"] and len(sismos["features"]) == 2
    assert len(cliente.get("/api/v1/capas/sismos", params={"magnitud_min": 6}).json()["features"]) == 1
    assert sismos["features"][0]["geometry"]["coordinates"] == [-73.64, -16.26]
    volcanes = cliente.get("/api/v1/capas/volcanes").json()
    assert (
        volcanes["expediente_id"] == v["id"]
        and volcanes["features"][0]["properties"]["nombre"] == "Misti, El"
    )
    retiro = {"motivo": "Prueba de retiro de un expediente de contrato."}
    assert (
        cliente.post(f"/api/v1/expedientes/{s['id']}/retirar", json=retiro, headers=admin).status_code == 200
    )
    assert cliente.get("/api/v1/capas/sismos").json()["expediente_id"] is None


def test_expediente_es_inmutable_ante_copias(cliente: TestClient, ingesta: dict[str, str]) -> None:
    datos = _comparacion()
    otra = copy.deepcopy(datos)
    otra["modelos"][1]["puntaje_prueba"] = 0.11
    a, b = _publicar(cliente, ingesta, datos).json(), _publicar(cliente, ingesta, otra).json()
    assert a["id"] != b["id"]  # cualquier cambio de contenido produce un expediente nuevo
