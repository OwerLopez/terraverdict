"""Experimento: estadística sísmica del entorno de Arequipa (USGS ComCat, 350 km).

- Magnitud de completitud Mc: máxima curvatura + 0,2 (Wiemer y Wyss, 2000, doi:10.1785/0119990114;
  Woessner y Wiemer, 2005, doi:10.1785/0120040007).
- Valor b: estimador de máxima verosimilitud de Aki (1965) con corrección de agrupamiento de Utsu;
  incertidumbre de Shi y Bolt (1982) y bootstrap.
- Desagrupamiento: ventanas de Gardner y Knopoff (1974).
- Conteos mensuales: ¿hay estructura temporal aprovechable más allá de un Poisson? Se mide con
  ganancia de información frente a la tasa media. NO es un pronóstico de sismos.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..evaluacion.incertidumbre import decidir_abstencion
from ..ingest import usgs
from ..senales.procesamiento import regimenes
from .comun import Particion, construir, evaluar_zoo, limpiar, serie_prueba


def catalogo(raw: Path) -> pd.DataFrame:
    ev = pd.DataFrame(usgs.cargar(raw / "usgs"))
    ev["tiempo"] = pd.to_datetime(ev["tiempo"], utc=True).dt.tz_localize(None)
    return ev.sort_values("tiempo").reset_index(drop=True)


def magnitud_completitud(m: np.ndarray, paso: float = 0.1) -> float:
    bins = np.arange(np.floor(m.min() / paso) * paso, m.max() + paso, paso)
    h, bordes = np.histogram(m, bins)
    return float(round(bordes[int(np.argmax(h))] + 0.2, 1))


def valor_b(m: np.ndarray, mc: float, paso: float = 0.1, n_boot: int = 500, semilla: int = 0) -> dict[str, Any]:
    x = m[m >= mc - 1e-9]
    n = len(x)
    b = np.log10(np.e) / (x.mean() - (mc - paso / 2))
    sigma = 2.3 * b**2 * np.sqrt(np.sum((x - x.mean()) ** 2) / (n * (n - 1)))  # Shi y Bolt (1982)
    rng = np.random.default_rng(semilla)
    boot = [np.log10(np.e) / (s.mean() - (mc - paso / 2)) for s in (rng.choice(x, n) for _ in range(n_boot))]
    a = np.log10(n) + b * mc
    return {
        "b": float(b),
        "sigma_shi_bolt": float(sigma),
        "ic90_bootstrap": [float(np.quantile(boot, 0.05)), float(np.quantile(boot, 0.95))],
        "a": float(a),
        "n": int(n),
        "mc": mc,
    }


def gardner_knopoff(ev: pd.DataFrame) -> np.ndarray:
    """Marca como independientes (True) los sismos que no caen en la ventana de uno mayor."""
    t = ev["tiempo"].to_numpy("datetime64[s]").astype(np.int64) / 86400.0
    lat, lon, m = ev["lat"].to_numpy(), ev["lon"].to_numpy(), ev["magnitud"].to_numpy()
    independiente = np.ones(len(ev), bool)
    for i in np.argsort(-m):
        if not independiente[i]:
            continue
        dist_km = 10 ** (0.1238 * m[i] + 0.983)
        dias = 10 ** (0.032 * m[i] + 2.7389) if m[i] >= 6.5 else 10 ** (0.5409 * m[i] - 0.547)
        dlat = np.radians(lat - lat[i])
        dlon = np.radians(lon - lon[i])
        a = np.sin(dlat / 2) ** 2 + np.cos(np.radians(lat[i])) * np.cos(np.radians(lat)) * np.sin(dlon / 2) ** 2
        d = 2 * 6371 * np.arcsin(np.sqrt(a))
        replicas = (d <= dist_km) & (t - t[i] >= 0) & (t - t[i] <= dias) & (m <= m[i])
        replicas[i] = False
        independiente[replicas] = False
    return independiente


def ejecutar(
    cfg: dict[str, Any],
    raw: Path,
    registro=print,
    redes: list[str] | None = None,
    semillas: tuple[int, ...] = (0, 1, 2),
) -> dict[str, Any]:
    ev = catalogo(raw)
    m = ev["magnitud"].to_numpy()
    mc_total = magnitud_completitud(m)
    por_decada = {
        f"{d}s": magnitud_completitud(ev.loc[ev["tiempo"].dt.year // 10 * 10 == d, "magnitud"].to_numpy())
        for d in range(1970, 2030, 10)
        if (ev["tiempo"].dt.year // 10 * 10 == d).sum() > 50
    }
    mc = max(mc_total, 4.5)  # completitud conservadora para toda la serie
    ev["independiente"] = gardner_knopoff(ev)
    completos = ev[ev["magnitud"] >= mc - 1e-9]
    b_total = valor_b(m, mc)
    b_ind = valor_b(completos.loc[completos["independiente"], "magnitud"].to_numpy(), mc)
    mensual = completos.set_index("tiempo").resample("MS")["magnitud"].count()
    mensual_ind = completos[completos["independiente"]].set_index("tiempo").resample("MS")["magnitud"].count()
    mensual = mensual[mensual.index <= "2026-10-01"]
    mensual_ind = mensual_ind.reindex(mensual.index, fill_value=0)
    intervalos = (
        np.diff(completos.loc[completos["independiente"], "tiempo"].to_numpy("datetime64[s]").astype(np.int64))
        / 86400.0
    )
    registro(
        f"sismos: {len(ev)} eventos, Mc={mc}, b={b_total['b']:.2f}, independientes={int(completos['independiente'].sum())}"
    )

    # Conteos mensuales: ¿mejoran los modelos a un Poisson de tasa constante?
    pt = cfg["particion_temporal"]
    # El catálogo empieza en 1973; la prueba termina en el último mes completo (inicio de mes ≤ fin de la prueba)
    fin_prueba = min(pd.Timestamp(pt["prueba"][1]), mensual.index[-1]).strftime("%Y-%m-%d")
    particion = Particion(
        ("1973-01-01", pt["entrenamiento"][1]), tuple(pt["validacion"]), (pt["prueba"][0], fin_prueba)
    )
    maxmag = completos.set_index("tiempo").resample("MS")["magnitud"].max().reindex(mensual.index).fillna(mc - 0.5)
    X = pd.DataFrame(
        {"conteo_log": np.log1p(mensual), "conteo_independiente_log": np.log1p(mensual_ind), "magnitud_maxima": maxmag},
        index=mensual.index,
    )
    objetivo = mensual.shift(-1).astype(float)
    tasa = float(mensual[mensual.index <= particion.entrenamiento[1]].mean())

    def referencias(d) -> dict[str, dict[str, np.ndarray]]:
        return {
            p: {
                "climatologia": np.full(len(d.y[p]), tasa),
                "persistencia": np.maximum(mensual.reindex(d.fechas[p]).to_numpy(float), 0.5),
            }
            for p in ("validacion", "prueba")
        }

    d = construir(X, objetivo, 12, particion, None, pd.DateOffset(months=1))
    zoo = evaluar_zoo(
        d, "conteo", referencias(d), redes=redes, semillas=semillas, epocas=150, bloque_bootstrap=6, registro=registro
    )
    mejor = zoo["mejor_validacion"]
    abst = decidir_abstencion(
        habilidad_validacion=zoo["modelos"][mejor]["puntaje_validacion"],
        minimo=cfg["abstencion"]["skill_minimo_validacion"],
    )
    grandes = ev[ev["magnitud"] >= 6.5][["tiempo", "magnitud", "profundidad_km", "lugar", "lat", "lon"]]
    return {
        "fenomeno": "sismos",
        "tarea": "conteo",
        "catalogo": {
            "fuente": "USGS ComCat (FDSN)",
            "radio_km": cfg["descarga"]["sismos"]["radio_km"],
            "eventos": len(ev),
            "desde": str(ev["tiempo"].iloc[0].date()),
            "hasta": str(ev["tiempo"].iloc[-1].date()),
            "tipos_magnitud": ev["tipo_magnitud"].value_counts().head(6).to_dict(),
        },
        "completitud": {"mc_maxima_curvatura": mc_total, "mc_por_decada": por_decada, "mc_usada": mc},
        "valor_b": {"todos": b_total, "desagrupados": b_ind},
        "desagrupamiento": {
            "metodo": "Gardner y Knopoff (1974)",
            "independientes": int(completos["independiente"].sum()),
            "dependientes": int((~completos["independiente"]).sum()),
        },
        "tasa_anual_m_mayor_mc": float(len(completos) / ((ev["tiempo"].iloc[-1] - ev["tiempo"].iloc[0]).days / 365.25)),
        "intereventos_independientes": {
            "n": len(intervalos),
            "media_dias": float(intervalos.mean()),
            "cv": float(intervalos.std() / intervalos.mean()),
            "lectura": "CV ≈ 1: Poisson; CV > 1: agrupamiento; CV < 1: cuasiperiodicidad",
        },
        "regimenes_tasa_independiente": regimenes(mensual_ind.astype(float), tamano_minimo=36),
        "grandes_sismos": [{**r, "tiempo": str(r["tiempo"])} for r in grandes.to_dict("records")],
        "conteos_anuales": {
            str(k.year): int(v) for k, v in completos.set_index("tiempo").resample("YS")["magnitud"].count().items()
        },
        "mapa": [
            {
                "t": str(r.tiempo.date()),
                "lat": round(r.lat, 3),
                "lon": round(r.lon, 3),
                "m": r.magnitud,
                "z": round(float(r.profundidad_km), 1) if np.isfinite(r.profundidad_km) else None,
            }
            for r in ev[ev["magnitud"] >= 5.0].itertuples()
        ],
        "pronostico_conteos": {
            "definicion": f"conteo mensual de sismos M ≥ {mc} del mes siguiente",
            "tasa_media_entrenamiento": tasa,
            "zoo": limpiar(zoo),
            "abstencion": abst,
            "serie_prueba": serie_prueba(d, zoo, mejor, referencias(d)["prueba"]["climatologia"]),
        },
        "advertencia": "No es un pronóstico de sismos. Mide si hay estructura temporal (agrupamiento) más allá del azar.",
        "_series": {"mensual_independiente": mensual_ind, "intereventos_log": np.log(np.maximum(intervalos, 1e-3))},
    }
