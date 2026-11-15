"""Auditoría de métricas y pesos (docs/auditoria-metricas.md).

Cada prueba fija una propiedad que la auditoría declaró verificada: definiciones de las métricas
contra su fórmula, casos límite (una sola clase, todo ceros, series cortas), bloque del bootstrap,
correcciones por comparaciones múltiples y el protocolo de validación de `evaluar_zoo`
(calibración y ensambles fuera de pliegue, parada temprana sin tocar la validación).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest
from scipy import stats
from sklearn.metrics import roc_auc_score

from terraverdict.config import cargar_yaml
from terraverdict.evaluacion import metricas as M
from terraverdict.evaluacion.incertidumbre import CalibradorIsotonico
from terraverdict.experimentos import comun
from terraverdict.experimentos.comun import (
    Particion,
    calibrar_cruzado,
    construir,
    evaluar_zoo,
    parametros,
    pesos_validacion,
    pliegues_contiguos,
)

RAIZ = Path(__file__).resolve().parents[2]


# ----------------------------------------------------------------------------- definiciones


def test_brier_bss_y_ecm_coinciden_con_su_formula() -> None:
    rng = np.random.default_rng(1)
    y = (rng.uniform(size=300) < 0.3).astype(float)
    p, r = rng.uniform(size=300), np.full(300, 0.3)
    assert M.brier(y, p) == pytest.approx(np.mean((p - y) ** 2))
    assert M.habilidad_brier(y, p, r) == pytest.approx(1 - np.mean((p - y) ** 2) / np.mean((r - y) ** 2))
    z, q = rng.normal(size=200), rng.normal(size=200)
    assert M.habilidad_mse(z, q, np.zeros(200)) == pytest.approx(1 - np.mean((z - q) ** 2) / np.mean(z**2))
    assert M.rmse(z, q) == pytest.approx(np.sqrt(np.mean((z - q) ** 2)))
    assert M.mae(z, q) == pytest.approx(np.mean(np.abs(z - q)))


def test_auc_coincide_con_scikit_learn_y_es_nan_con_una_clase() -> None:
    rng = np.random.default_rng(2)
    y = (rng.uniform(size=200) < 0.4).astype(int)
    p = rng.uniform(size=200) + 0.3 * y
    assert M.auc(y, p) == pytest.approx(roc_auc_score(y, p))
    assert np.isnan(M.auc(np.zeros(50), rng.uniform(size=50)))  # todo ceros
    assert np.isnan(M.auc(np.ones(50), rng.uniform(size=50)))  # todo unos


def test_casos_limite_todo_ceros_dan_nan_no_un_numero_inventado() -> None:
    y = np.zeros(30)
    # Referencia perfecta (Brier 0): la habilidad no está definida → NaN, nunca 0 ni 1
    assert np.isnan(M.habilidad_brier(y, np.full(30, 0.1), np.zeros(30)))
    assert np.isnan(M.habilidad_mse(y, np.ones(30), np.zeros(30)))
    assert np.isnan(M.correlacion(y, np.arange(30.0)))
    t = M.tabla_contingencia(y, np.zeros(30), 0.5)  # ni eventos ni alarmas
    assert np.isnan(t["pod"]) and np.isnan(t["far"]) and np.isnan(t["csi"])


def test_ece_cero_si_lo_pronosticado_es_la_frecuencia_observada() -> None:
    y = np.array([0, 0, 0, 1] * 25 + [1, 1, 1, 0] * 25, float)
    p = np.array([0.25] * 100 + [0.75] * 100)
    assert M.confiabilidad(y, p, bins=2)["ece"] == pytest.approx(0.0, abs=1e-12)
    assert M.confiabilidad(y, np.full(200, 0.9), bins=10)["ece"] == pytest.approx(0.4)  # constante


def test_ganancia_de_informacion_en_bits() -> None:
    rng = np.random.default_rng(3)
    y = rng.poisson(4.0, size=400)
    tasa = np.full(400, 4.0)
    assert (M.log_verosimilitud_poisson(y, tasa) - M.log_verosimilitud_poisson(y, tasa)) / np.log(2) == 0.0
    esperado = np.mean(stats.poisson.logpmf(y, 4.0) - stats.poisson.logpmf(y, 2.0)) / np.log(2)
    obtenido = (M.log_verosimilitud_poisson(y, tasa) - M.log_verosimilitud_poisson(y, np.full(400, 2.0))) / np.log(2)
    assert obtenido == pytest.approx(esperado) and obtenido > 0


def test_diebold_mariano_series_cortas_y_horizonte() -> None:
    assert np.isnan(M.diebold_mariano(np.array([1.0, 2.0]), np.array([0.0, 1.0]))["p"])  # n < 3
    assert np.isnan(M.diebold_mariano(np.ones(40), np.ones(40))["p"])  # pérdidas iguales: varianza 0
    rng = np.random.default_rng(4)
    a, b = rng.normal(size=60) ** 2, (rng.normal(size=60) + 0.6) ** 2
    h1, h3 = M.diebold_mariano(a, b, horizonte=1), M.diebold_mariano(a, b, horizonte=3)
    # La corrección de Harvey-Leybourne-Newbold encoge el estadístico con horizontes largos
    assert abs(h3["estadistico"]) < abs(h1["estadistico"]) and h3["p"] > h1["p"]
    assert h3["rezagos_hac"] >= 2


def test_bootstrap_serie_corta_da_nan() -> None:
    assert all(np.isnan(v) for v in M.bootstrap_bloques(lambda x: float(np.mean(x)), np.array([1.0])))


# ----------------------------------------------------------------------------- bloque y correcciones


def test_bloque_politis_white_crece_con_la_autocorrelacion() -> None:
    rng = np.random.default_rng(5)
    ruido = rng.normal(size=600)
    ar = np.zeros(600)
    for i in range(1, 600):
        ar[i] = 0.9 * ar[i - 1] + rng.normal()
    b_ruido, b_ar = M.bloque_politis_white(ruido), M.bloque_politis_white(ar)
    assert b_ruido <= 3
    assert b_ar >= 10 and b_ar <= int(np.ceil(3 * np.sqrt(600)))
    assert M.bloque_politis_white(np.ones(50)) == 1 and M.bloque_politis_white(np.arange(5.0)) == 1


def test_bloque_del_historial_respeta_la_autocorrelacion_al_concatenar_anios() -> None:
    """Diferenciales AR(1) concatenados por años: el bloque usado (máx. del fijo y Politis-White)
    cubre la escala de decorrelación, así que el IC90 no es artificialmente estrecho."""
    rng = np.random.default_rng(6)
    anios = []
    x = 0.0
    for _ in range(6):  # 6 años de 12 meses consecutivos, como el historial mensual
        serie = []
        for _ in range(12):
            x = 0.7 * x + rng.normal()
            serie.append(x)
        anios.append(serie)
    d = np.concatenate(anios)
    tau = next(k for k in range(1, 30) if 0.7**k < 1 / np.e)  # rezago de decorrelación
    assert max(6, M.bloque_politis_white(d)) >= tau


def test_holm_y_benjamini_hochberg_a_mano() -> None:
    p = [0.01, 0.04, 0.03, None]
    assert M.ajuste_holm(p) == pytest.approx([0.03, 0.06, 0.06, None])  # type: ignore[arg-type]
    assert M.ajuste_bh(p) == pytest.approx([0.03, 0.04, 0.04, None])  # type: ignore[arg-type]
    # Con 39 sustitutos (p mínimo 0,025) y 20 ventanas, ninguna sobrevive a Holm
    assert min(v for v in M.ajuste_holm([0.025] * 20) if v is not None) > 0.05


# ----------------------------------------------------------------------------- protocolo de validación


def test_calibracion_fuera_de_pliegue_no_es_optimista() -> None:
    """Probabilidades sin información: la isotónica evaluada en sus propios datos 'aprende' ruido;
    fuera de pliegue, la habilidad vuelve a ≈ 0 o menos (promedio de 5 repeticiones)."""
    dentro, fuera = [], []
    for semilla in range(5):
        rng = np.random.default_rng(semilla)
        p = rng.uniform(size=200)
        y = (rng.uniform(size=200) < 0.2).astype(float)
        ref = np.full(200, y.mean())
        dentro.append(M.habilidad_brier(y, CalibradorIsotonico().ajustar(p, y).transformar(p), ref))
        fuera.append(M.habilidad_brier(y, calibrar_cruzado(p, y, pliegues_contiguos(200, 5)), ref))
    assert np.mean(dentro) > 0.01  # optimismo de evaluar donde se ajustó
    assert np.mean(fuera) < 0.0 and all(f < d for f, d in zip(fuera, dentro, strict=True))


def test_pesos_de_validacion_suman_uno_y_premian_al_mejor() -> None:
    rng = np.random.default_rng(8)
    y = rng.normal(size=200)
    P = np.column_stack([y + rng.normal(scale=0.1, size=200), rng.normal(size=200), rng.normal(size=200)])
    w = pesos_validacion("regresion", y, P)
    assert w.sum() == pytest.approx(1.0) and (w >= 0).all()
    assert w[0] > 0.9


def _datos_ar(n: int = 1500) -> tuple[pd.DataFrame, pd.Series]:
    rng = np.random.default_rng(9)
    x = np.zeros(n)
    for i in range(1, n):
        x[i] = 0.8 * x[i - 1] + rng.normal()
    idx = pd.date_range("2000-01-01", periods=n, freq="D")
    s = pd.Series(x, index=idx)
    return pd.DataFrame({"x": s}), s.shift(-1)


PART = Particion(("2000-01-01", "2002-06-30"), ("2002-07-01", "2003-03-31"), ("2003-04-01", "2004-12-31"))


def test_parada_temprana_no_usa_la_validacion(monkeypatch: pytest.MonkeyPatch) -> None:
    df, objetivo = _datos_ar()
    d = construir(df, objetivo, 7, PART)
    vistos: list[int] = []
    original = comun.entrenar

    def espia(modelo: Any, X_tr: np.ndarray, y_tr: np.ndarray, X_va: np.ndarray, y_va: np.ndarray, **kw: Any):
        vistos.append(len(X_va))
        np.testing.assert_array_equal(X_va, d.X["entrenamiento"][-len(X_va) :])  # tramo final del entrenamiento
        return original(modelo, X_tr, y_tr, X_va, y_va, **kw)

    monkeypatch.setattr(comun, "entrenar", espia)
    refs = {p: {"climatologia": np.zeros(len(d.y[p]))} for p in ("validacion", "prueba")}
    z = evaluar_zoo(d, "regresion", refs, redes=["mlp"], semillas=(0,), epocas=3, registro=lambda _: None)
    fraccion = float(parametros()["redes"]["fraccion_parada_temprana"])
    assert vistos == [round(len(d.y["entrenamiento"]) * fraccion)]
    assert "entrenamiento" in z["modelos"]["mlp"]["parada_temprana"]


def test_seleccion_por_validacion_con_ensambles_fuera_de_pliegue() -> None:
    df, objetivo = _datos_ar()
    d = construir(df, objetivo, 7, PART)
    refs = {p: {"climatologia": np.zeros(len(d.y[p]))} for p in ("validacion", "prueba")}
    z = evaluar_zoo(d, "regresion", refs, redes=["mlp"], semillas=(0,), epocas=3, registro=lambda _: None)
    m = z["modelos"]
    candidatos = {k: v for k, v in m.items() if v["familia"] != "referencia"}
    assert z["mejor_validacion"] == max(candidatos, key=lambda k: candidatos[k]["puntaje_validacion"])
    assert {"ensamble_top3", "ensamble_ponderado"} <= set(m)
    for e in ("ensamble_top3", "ensamble_ponderado"):
        assert sum(m[e]["pesos"]) == pytest.approx(1.0, abs=1e-3) and len(m[e]["pesos"]) == len(m[e]["miembros"])
        assert "fuera de pliegue" in m[e]["nota"]
        assert m[e]["bloque_bootstrap"] >= 10
    assert m["ensamble_top3"]["pesos"] == pytest.approx([1 / 3] * 3, abs=1e-4)


# ----------------------------------------------------------------------------- configuración única


def test_regla_de_evidencia_igual_en_config_informe_y_web() -> None:
    p = float(cargar_yaml(RAIZ / "config" / "modelos.yaml")["evaluacion"]["p_diebold_mariano"])
    from terraverdict.experimentos.informe import P_DM

    assert p == P_DM
    ts = (RAIZ / "frontend" / "src" / "lib" / "modelos.ts").read_text(encoding="utf-8")
    m = re.search(r"export const UMBRAL_P_DM = ([0-9.]+);", ts)
    assert m and float(m.group(1)) == p


def test_hiperparametros_salen_de_la_configuracion() -> None:
    """Ningún experimento conserva hiperparámetros escritos en el código (auditoría, punto 4)."""
    carpeta = RAIZ / "src" / "terraverdict" / "experimentos"
    prohibidos = [r"C=0\.5", r"alpha=3\.0", r"epocas=(60|150)\b", r"\[3, 7, 14, 30\]", r"\[3, 6, 12, 24\]"]
    prohibidos += [r"VENTANA_CONTEOS_MESES\s*=", r"max\(mc_total, 4\.5\)", r"UMBRAL_SPI_MM = 200"]
    for ruta in carpeta.glob("*.py"):
        texto = ruta.read_text(encoding="utf-8")
        for patron in prohibidos:
            assert not re.search(patron, texto), f"{ruta.name}: {patron}"


def test_prior_fisico_de_lluvia_sale_del_catalogo() -> None:
    from terraverdict.experimentos.lluvia import VARIABLES_CATALOGO, prior_catalogo

    cfg = cargar_yaml(RAIZ / "config" / "fenomenos.yaml")
    prior = prior_catalogo(cfg, list(VARIABLES_CATALOGO))
    catalogo = {v["id"]: v["relevancia"] for v in cfg["fenomenos"]["lluvia_extrema"]["variables"]}
    assert prior == {c: catalogo[i] for c, i in VARIABLES_CATALOGO.items()}
    with pytest.raises(KeyError):
        prior_catalogo(cfg, ["variable_inexistente"])


def test_mc_de_sismos_solo_con_el_entrenamiento(monkeypatch: pytest.MonkeyPatch) -> None:
    from terraverdict.experimentos import sismos

    rng = np.random.default_rng(10)
    t_ent = pd.date_range("1990-01-01", "2015-12-01", periods=600)
    t_pru = pd.date_range("2021-01-01", "2026-06-01", periods=600)
    ev = pd.DataFrame(
        {
            "tiempo": list(t_ent) + list(t_pru),
            # Entrenamiento: moda en 4,9; prueba: moda en 3,9 (si la prueba entrara, Mc bajaría al piso)
            "magnitud": np.round(np.r_[4.9 + rng.exponential(0.4, 600), 3.9 + rng.exponential(0.4, 600)], 1),
            "lat": -16.0,
            "lon": -71.5,
            "profundidad_km": 100.0,
        }
    )
    monkeypatch.setattr(sismos, "catalogo", lambda raw: ev.copy())
    cfg = {"particion_temporal": {"entrenamiento": ["1973-01-01", "2015-12-31"]}}
    prep = sismos.preparar(Path("."), cfg)
    assert prep["mc_total"] >= 5.0  # 4,9 + 0,2 de corrección: solo vio el entrenamiento
