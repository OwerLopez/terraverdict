"""Historial de métricas: cómo habría rendido cada modelo, año por año, con los datos de entonces.

1. Pronóstico por origen móvil anual (Tashman, 2000, doi:10.1016/S0169-2070(00)00065-0).
   Para cada año Y:
   - entrenamiento con datos ≤ 31-dic-(Y−2);
   - el año Y−1 es la validación (calibración isotónica, umbral, conformal y parada temprana);
   - el año Y es la prueba.
   El diseño de cada tarea (variables, ventana y arquitectura) es el CONGELADO del experimento
   principal, leído de `resultados/<fenómeno>.json`. Así el historial reevalúa el modelo publicado y
   no elige uno nuevo mirando el futuro.
   Regímenes:
   - años ≤ fin de la validación original: "validacion_del_diseno". Es una lectura optimista,
     porque esos años sirvieron para elegir el diseño;
   - años posteriores: "fuera_de_muestra".
   Además de cada año, se informa la habilidad agregada por régimen sobre las predicciones
   concatenadas, con IC90 por bootstrap de bloques y Diebold-Mariano frente a la climatología.

2. Dinámica en ventanas deslizantes de N años (paso anual). En cada ventana se calculan con los
   mismos métodos validados del diagnóstico de caos (tests/caos):
   - entropía de permutación (Bandt y Pompe, 2002);
   - entropía muestral (Richman y Moorman, 2000);
   - λ de Rosenstein (1993);
   - determinismo de la RQA;
   - K de la prueba 0-1 (Gottwald y Melbourne, 2004);
   - p de no linealidad por asimetría temporal frente a sustitutos IAAFT (Schreiber y Schmitz, 1996).
   Muestra si la dinámica de cada serie cambió con el tiempo. No reemplaza al veredicto global.
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..caos.embedding import dimension_embedding, embeber, falsos_vecinos, periodo_medio, retardo_optimo
from ..caos.invariantes import entropia_muestral, entropia_permutacion, lyapunov_rosenstein, prueba_01
from ..caos.recurrencia import rqa
from ..caos.surrogates import asimetria_temporal, prueba
from ..config import cargar_yaml
from ..evaluacion import metricas as M
from . import caos_real, lluvia, sequia, sismos
from .comun import Particion, Tarea, construir, evaluar_zoo, puntaje_validacion

RAIZ = Path(__file__).resolve().parents[3]

METRICA_PRINCIPAL = {
    "clasificacion": "bss_climatologia",
    "regresion": "habilidad_climatologia",
    "conteo": "ganancia_informacion_bits",
}


# ----------------------------------------------------------------------------- diseño congelado


def mejor_red(zoo: dict[str, Any]) -> str:
    """La red neuronal con mejor puntaje de validación en el experimento principal."""
    redes = {k: v for k, v in zoo["modelos"].items() if v["familia"] == "red_neuronal"}
    if not redes:
        raise ValueError("El resultado principal no tiene redes neuronales evaluadas.")
    return max(redes, key=lambda k: redes[k]["puntaje_validacion"])


def disenos(cfg: dict[str, Any], raw: Path, resultados: Path) -> dict[str, dict[str, Any]]:
    """Tarea + diseño congelado (columnas, ventana, red) de cada tarea con resultado principal."""
    salida: dict[str, dict[str, Any]] = {}
    ruta = resultados / "lluvia_extrema.json"
    if ruta.exists():
        r = _json(ruta)
        t, _, _, _ = lluvia.tarea(cfg, raw, "power")
        salida[t.nombre] = {
            "tarea": t,
            "fenomeno": "lluvia_extrema",
            "descripcion": r["definicion"]["objetivo"],
            "columnas": lluvia.columnas_diseno(r),
            "L": int(r["ventana"]["elegida"]),
            "red": mejor_red(r["zoo"]),
        }
    ruta = resultados / "sequia.json"
    if ruta.exists():
        r = _json(ruta)
        X, _ = sequia.preparar(raw, cfg["particion_temporal"]["entrenamiento"][1])
        for clave, h in (("h1", 1), ("h3", 3)):
            if clave not in r["horizontes"]:
                continue
            b = r["horizontes"][clave]
            t = sequia.tarea(cfg, raw, h, "power", X)
            salida[t.nombre] = {
                "tarea": t,
                "fenomeno": "sequia",
                "descripcion": b["definicion"]["objetivo"],
                "columnas": list(X.columns),
                "L": int(b["ventana"]["elegida"]),
                "red": mejor_red(b["zoo"]),
            }
    ruta = resultados / "sismos.json"
    if ruta.exists():
        r = _json(ruta)
        t = sismos.tarea(cfg, raw)
        salida[t.nombre] = {
            "tarea": t,
            "fenomeno": "sismos",
            "descripcion": r["pronostico_conteos"]["definicion"],
            "columnas": list(t.X.columns),
            "L": sismos.VENTANA_CONTEOS_MESES,
            "red": mejor_red(r["pronostico_conteos"]["zoo"]),
        }
    return salida


def _json(ruta: Path) -> dict[str, Any]:
    import json

    return json.loads(ruta.read_text(encoding="utf-8"))


# ----------------------------------------------------------------------------- origen móvil


def cortes(anio_inicial: int, anio_final: int) -> list[Particion]:
    """Un corte por año de prueba Y: entrenamiento ≤ Y−2, validación Y−1, prueba Y (sin solapes)."""
    return [
        Particion(
            ("1900-01-01", f"{y - 2}-12-31"),
            (f"{y - 1}-01-01", f"{y - 1}-12-31"),
            (f"{y}-01-01", f"{y}-12-31"),
        )
        for y in range(anio_inicial, anio_final + 1)
    ]


def _escalar(v: Any) -> float | None:
    return float(v) if isinstance(v, (int, float, np.floating)) and np.isfinite(v) else None


def origen_movil(
    t: Tarea,
    columnas: list[str],
    L: int,
    red: str,
    anio_inicial: int,
    anio_final: int,
    frontera_diseno: int,
    *,
    semillas: tuple[int, ...] = (0,),
    n_minimo: int = 10,
    eventos_minimos: int = 3,
    registro: Callable[[str], None] = print,
) -> dict[str, Any]:
    principal = METRICA_PRINCIPAL[t.tipo]
    anios: list[dict[str, Any]] = []
    # predicciones concatenadas por régimen y modelo, para la habilidad agregada
    acumulado: dict[str, dict[str, dict[str, list[np.ndarray]]]] = {}
    for particion in cortes(anio_inicial, anio_final):
        y = int(particion.prueba[0][:4])
        regimen = "validacion_del_diseno" if y <= frontera_diseno else "fuera_de_muestra"
        d = construir(t.X[columnas], t.objetivo, L, particion, t.fechas, t.horizonte)
        n = {k: len(v) for k, v in d.y.items()}
        motivo = None
        if min(n["validacion"], n["prueba"]) < n_minimo:
            motivo = f"menos de {n_minimo} observaciones en validación o prueba"
        elif t.tipo == "clasificacion" and min(d.y["validacion"].sum(), d.y["prueba"].sum()) < eventos_minimos:
            motivo = f"menos de {eventos_minimos} eventos en validación o prueba"
        if motivo:
            anios.append({"anio": y, "regimen": regimen, "n": n, "omitido": motivo})
            continue
        refs = t.referencias(particion.entrenamiento[1])(d)
        zoo = evaluar_zoo(
            d,
            t.tipo,
            refs,
            redes=[red],
            semillas=semillas,
            epocas=t.epocas,
            bloque_bootstrap=t.bloque_bootstrap,
            registro=lambda _: None,
        )
        modelos = {}
        for nombre, m in zoo["modelos"].items():
            modelos[nombre] = {
                "familia": m["familia"],
                "validacion": _escalar(m["puntaje_validacion"]),
                "prueba": _escalar(m["prueba"].get(principal)),
                "ic90": [_escalar(v) for v in m["ic90_prueba"]],
                "p_diebold_mariano": _escalar(m["diebold_mariano_vs_climatologia"]["p"]),
                "secundarias": {k: _escalar(v) for k, v in m["prueba"].items() if _escalar(v) is not None},
            }
            pred = acumulado.setdefault(regimen, {}).setdefault(nombre, {"y": [], "p": [], "ref": []})
            pred["y"].append(d.y["prueba"])
            pred["p"].append(zoo["_predicciones"][nombre]["prueba"])
            pred["ref"].append(refs["prueba"]["climatologia"])
        fila = {
            "anio": y,
            "regimen": regimen,
            "n": n,
            "eventos_prueba": int(d.y["prueba"].sum()) if t.tipo == "clasificacion" else None,
            "elegido_en_validacion": zoo["mejor_validacion"],
            "modelos": modelos,
        }
        anios.append(fila)
        registro(f"  {t.nombre} {y} ({regimen}): {red} {modelos[red]['prueba']}")

    agregado: dict[str, dict[str, Any]] = {}
    for regimen, por_modelo in acumulado.items():
        agregado[regimen] = {}
        for nombre, p in por_modelo.items():
            yy, pp, rr = (np.concatenate(p[k]) for k in ("y", "p", "ref"))
            ic = M.bootstrap_bloques(
                lambda a, b, c: puntaje_validacion(t.tipo, a, b, c), yy, pp, rr, bloque=t.bloque_bootstrap
            )
            dm = M.diebold_mariano(_perdida(t.tipo, yy, pp), _perdida(t.tipo, yy, rr))
            agregado[regimen][nombre] = {
                "valor": _escalar(puntaje_validacion(t.tipo, yy, pp, rr)),
                "ic90": [_escalar(v) for v in ic],
                "p_diebold_mariano": _escalar(dm["p"]),
                "n": len(yy),
                "anios": len(p["y"]),
            }
    return {"metrica_principal": principal, "anios": anios, "agregado": agregado}


def _perdida(tipo: str, y: np.ndarray, p: np.ndarray) -> np.ndarray:
    if tipo == "conteo":
        from scipy import stats

        return -stats.poisson.logpmf(y.astype(int), np.clip(p, 1e-9, None))
    return (p - y) ** 2


# ----------------------------------------------------------------------------- caos en ventanas


def orden_permutacion(n: int, factor: int = 5, minimo: int = 3, maximo: int = 6) -> int:
    """Mayor orden d con n ≥ factor·d! (Riedl et al., 2013); nunca menor que `minimo`."""
    d = minimo
    for k in range(minimo, maximo + 1):
        if n >= factor * math.factorial(k):
            d = k
    return d


def invariantes_ventana(x: np.ndarray, rng: np.random.Generator, n_sustitutos: int) -> dict[str, Any]:
    """Invariantes de una ventana, con el embedding estimado en la propia ventana."""
    x = np.asarray(x, float)
    x = (x - x.mean()) / (x.std() or 1.0)
    n = len(x)
    tau = int(retardo_optimo(x, max_lag=max(2, min(60, n // 10)))["tau"])
    m = max(2, dimension_embedding(falsos_vecinos(x, tau, m_max=8)))
    theiler = int(min(max(tau, round(periodo_medio(x))), max(1, n // 20)))
    orden = orden_permutacion(n)
    lyap = lyapunov_rosenstein(x, m, tau, theiler)
    sampen = entropia_muestral(x)
    no_lineal = prueba(x, lambda s: asimetria_temporal(s, 1), n_sustitutos, "dos", rng)
    return {
        "entropia_permutacion": _escalar(entropia_permutacion(x, orden=orden, retardo=1)),
        "orden_permutacion": orden,
        "entropia_muestral": _escalar(sampen),
        "lyapunov": _escalar(lyap["lambda"]),
        "determinismo": _escalar(rqa(embeber(x, m, tau), theiler=theiler, miniatura=1)["determinismo"]),
        "k_01": _escalar(prueba_01(x[::tau], rng=rng)["K"]),
        "p_no_linealidad": _escalar(no_lineal["p"]),
        "embedding": {"tau": tau, "m": m, "theiler": theiler},
    }


def caos_ventanas(
    serie: pd.Series,
    ventana_anios: int,
    paso_anios: int,
    n_sustitutos: int,
    rng: np.random.Generator,
    n_minimo: int = 240,
) -> list[dict[str, Any]]:
    serie = serie.dropna().sort_index()
    if serie.empty:
        return []
    primero, ultimo = serie.index[0].year, serie.index[-1].year
    filas = []
    for fin in range(primero + ventana_anios - 1, ultimo + 1, paso_anios):
        inicio = fin - ventana_anios + 1
        tramo = serie[(serie.index.year >= inicio) & (serie.index.year <= fin)]
        fila: dict[str, Any] = {"inicio": inicio, "fin": fin, "n": len(tramo)}
        if len(tramo) < n_minimo or float(tramo.std()) == 0.0:
            fila["omitido"] = f"menos de {n_minimo} puntos o serie constante"
        else:
            fila.update(invariantes_ventana(tramo.to_numpy(float), rng, n_sustitutos))
        filas.append(fila)
    return filas


# ----------------------------------------------------------------------------- orquestación


def ejecutar(
    cfg: dict[str, Any],
    raw: Path,
    resultados: Path,
    sismos_resultado: dict[str, Any] | None = None,
    config: Path = RAIZ / "config" / "historial.yaml",
    registro: Callable[[str], None] = print,
    max_cortes: int | None = None,
) -> dict[str, Any]:
    """`max_cortes` limita los años y las ventanas a los más recientes (modo rápido de las pruebas)."""
    h = cargar_yaml(config)
    pt = cfg["particion_temporal"]
    anio_inicial = pd.Timestamp(pt["entrenamiento"][1]).year + 1
    frontera = pd.Timestamp(pt["validacion"][1]).year
    cp = h["pronostico"]

    pronostico: dict[str, Any] = {}
    disponibles = disenos(cfg, raw, resultados)
    for nombre in cp["tareas"]:
        if nombre not in disponibles:
            pronostico[nombre] = {"omitido": "sin resultado principal o sin datos locales"}
            continue
        dz = disponibles[nombre]
        t: Tarea = dz["tarea"]
        anio_final = int(t.objetivo.dropna().index.max().year)
        desde = anio_inicial if max_cortes is None else max(anio_inicial, anio_final - max_cortes + 1)
        registro(f"historial {nombre}: {anio_inicial}–{anio_final}, red {dz['red']}, L={dz['L']}")
        pronostico[nombre] = {
            "fenomeno": dz["fenomeno"],
            "tipo": t.tipo,
            "descripcion": dz["descripcion"],
            "diseno": {"columnas": dz["columnas"], "ventana": dz["L"], "red": dz["red"]},
            **origen_movil(
                t,
                dz["columnas"],
                dz["L"],
                dz["red"],
                desde,
                anio_final,
                frontera,
                semillas=tuple(cp["semillas"]),
                n_minimo=cp["n_minimo_prueba"],
                eventos_minimos=cp["eventos_minimos"],
                registro=registro,
            ),
        }

    cc = h["caos"]
    rng = np.random.default_rng(cc["semilla"])
    omitidas: dict[str, str] = {}
    caos: dict[str, Any] = {}
    for nombre, (serie, unidad, fuente, _) in caos_real.series(cfg, raw, sismos_resultado, omitidas).items():
        if nombre not in cc["series"]:
            continue
        ventana = cc["series"][nombre]["ventana_anios"]
        if max_cortes is not None:
            serie = serie[serie.index.year > serie.index[-1].year - ventana - max_cortes + 1]
        filas = caos_ventanas(serie, ventana, cc["paso_anios"], cc["n_sustitutos"], rng)
        caos[nombre] = {"fuente": fuente, "unidad_tiempo": unidad, "ventana_anios": ventana, "ventanas": filas}
        registro(f"historial caos {nombre}: {sum('omitido' not in f for f in filas)} ventanas")

    return {
        "fenomeno": "historial",
        "tarea": "historial_metricas",
        "configuracion": {"archivo": "config/historial.yaml", "sha256": hashlib.sha256(config.read_bytes()).hexdigest()},
        "metodo": {
            "pronostico": "origen móvil anual (entrena ≤ Y−2, valida Y−1, prueba Y) con el diseño congelado",
            "anio_inicial": anio_inicial,
            "frontera_diseno": frontera,
            "semillas": cp["semillas"],
            "caos": f"ventanas deslizantes, paso {cc['paso_anios']} año(s), {cc['n_sustitutos']} sustitutos IAAFT",
        },
        "pronostico": pronostico,
        "caos": caos,
        "series_omitidas": omitidas,
    }
