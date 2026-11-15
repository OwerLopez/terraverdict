"""Prueba de humo de cada experimento con un recorte de los datos REALES (tests/fixtures/raw_reducido).

El recorte (2008–2020) lo genera scripts/generar_fixtures_experimentos.py desde data/raw y guarda el
SHA-256 de cada crudo original. La partición se acorta para que el recorte tenga las tres partes;
las cifras de aquí no son resultados: solo comprueban que cada experimento corre de punta a punta
y entrega la estructura que consumen el informe y el backend.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from terraverdict.config import cargar_yaml
from terraverdict.experimentos import caos_real, deslizamientos, ejecutar, lluvia, sequia, sismos, volcanes

RAIZ = Path(__file__).resolve().parents[2]
RAW = RAIZ / "tests" / "fixtures" / "raw_reducido"
PARTICION = {
    "entrenamiento": ["2008-01-01", "2016-12-31"],
    "validacion": ["2017-01-01", "2018-12-31"],
    "prueba": ["2019-01-01", "2020-12-31"],
}
RAPIDO: dict[str, Any] = {"redes": ["mlp"], "semillas": (0,)}


def _silencio(_: str) -> None:
    return None


@pytest.fixture(scope="module")
def cfg() -> dict[str, Any]:
    c = cargar_yaml(RAIZ / "config" / "fenomenos.yaml")
    c["particion_temporal"] = PARTICION
    return c


@pytest.fixture(scope="module")
def r_sismos(cfg: dict[str, Any]) -> dict[str, Any]:
    return sismos.ejecutar(cfg, RAW, registro=_silencio, **RAPIDO)


def _serializable(r: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(ejecutar._json(r), allow_nan=False))


def _zoo_valido(zoo: dict[str, Any]) -> None:
    familias = {v["familia"] for v in zoo["modelos"].values()}
    assert {"referencia", "clasico", "red_neuronal", "ensamble"} <= familias
    assert zoo["mejor_validacion"] in zoo["modelos"]
    for v in zoo["modelos"].values():
        assert len(v["ic90_prueba"]) == 2 and "diebold_mariano_vs_climatologia" in v


def test_volcanes(cfg: dict[str, Any]) -> None:
    r = _serializable(volcanes.ejecutar(cfg, RAW, registro=_silencio))
    nombres = {v["nombre"] for v in r["volcanes"]}
    assert {"Misti, El", "Ubinas", "Sabancaya"} <= nombres
    for v in r["volcanes"]:
        lo, hi = v["ic90_probabilidad_anual"]
        assert lo <= v["probabilidad_anual_inicio"] <= hi
    assert r["abstencion"]["abstencion"]  # nunca pronostica erupciones


def test_deslizamientos_se_abstiene_con_pocos_eventos(cfg: dict[str, Any]) -> None:
    r = _serializable(deslizamientos.ejecutar(cfg, RAW, registro=_silencio))
    assert r["eventos_por_lluvia_analizados"] > 0
    if r["eventos_por_lluvia_analizados"] < cfg["abstencion"]["eventos_minimos_umbral"]:
        assert r["abstencion"]["abstencion"] and r["umbral"] is None


def test_sismos(r_sismos: dict[str, Any]) -> None:
    r = _serializable(r_sismos)
    assert r["completitud"]["mc_usada"] >= 4.5
    b = r["valor_b"]["todos"]
    assert 0.5 < b["b"] < 1.6 and b["ic90_bootstrap"][0] < b["b"] < b["ic90_bootstrap"][1]
    _zoo_valido(r["pronostico_conteos"]["zoo"])
    assert all(e["m"] >= 5.0 for e in r["mapa"])


def test_sequia(cfg: dict[str, Any]) -> None:
    r = _serializable(sequia.ejecutar(cfg, RAW, registro=_silencio, **RAPIDO))
    assert set(r["horizontes"]) == {"h1", "h3"}
    for h in r["horizontes"].values():
        _zoo_valido(h["zoo"])
        mejor = h["zoo"]["modelos"][h["zoo"]["mejor_validacion"]]
        assert 0 <= mejor["prueba"]["cobertura_90"] <= 1


def test_lluvia(cfg: dict[str, Any]) -> None:
    r = _serializable(lluvia.ejecutar(cfg, RAW, registro=_silencio, **RAPIDO))
    assert "lluvia_log" in r["seleccion_variables"]["seleccionadas"]
    assert str(r["ventana"]["elegida"]) in r["ventana"]["puntuacion_validacion"]  # JSON: claves en texto
    _zoo_valido(r["zoo"])
    assert set(r["ablaciones"]) == {"seleccion_mrmr", "solo_historia_lluvia", "sin_oni", "todas_las_variables"}
    assert r["calidad"]["contraste_ciudad_vs_estacion"]["dias_comunes"] > 0
    assert len(r["serie_prueba"]["fechas"]) == len(r["serie_prueba"]["observado"])


def test_caos_en_series_reales(cfg: dict[str, Any], r_sismos: dict[str, Any]) -> None:
    r = _serializable(caos_real.ejecutar(cfg, RAW, r_sismos, registro=_silencio))
    assert set(r["series"]) == {
        "lluvia_pentadas_cabecera",
        "temperatura_diaria_cabecera",
        "spi3_mensual_cabecera",
        "oni_mensual",
        "sismos_conteo_mensual",
        "sismos_intereventos_log",
    }
    validos = {
        "lineal_estocastica",
        "no_lineal_sin_caos_demostrado",
        "compatible_con_caos_baja_dimension",
        "regular",
        "insuficiente",
    }
    assert all(s["veredicto"] in validos for s in r["series"].values())
    assert sum(r["resumen_veredictos"].values()) == 6


def test_orquestador_guarda_procedencia(tmp_path: Path) -> None:
    config = tmp_path / "fenomenos.yaml"
    c = cargar_yaml(RAIZ / "config" / "fenomenos.yaml")
    c["particion_temporal"] = PARTICION
    config.write_text(yaml.safe_dump(c, allow_unicode=True), encoding="utf-8")
    indice = ejecutar.ejecutar(raw=RAW, salida=tmp_path / "res", solo=["volcanes", "deslizamientos"], config=config)
    assert indice["experimentos"] == ["deslizamientos", "volcanes"]
    r = json.loads((tmp_path / "res" / "volcanes.json").read_text())
    p = r["procedencia"]
    assert p["config_sha256"] and p["versiones"]["torch"] and p["modo"] == "completo"
    assert json.loads((tmp_path / "res" / "indice.json").read_text())["commit"] == p["commit"]
