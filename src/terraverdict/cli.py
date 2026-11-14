"""CLI: tv ingest-power | ingest-oni | trends | report"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import typer

from .config import cargar_preregistro, cargar_yaml
from .expedientes.build import construir_expediente, guardar
from .ingest import noaa, power
from .preprocess.anual import lluvia_dic_mar, mensual, temperatura_media_anual
from .trends.analizar import analizar_serie

app = typer.Typer(help="TerraVerdict · detective de tendencias")


@app.command("ingest-power")
def ingest_power(config: Path = Path("configs/chili.yaml"), raw: Path = Path("data/raw")) -> None:
    c = cargar_yaml(config)
    p = c["puntos"]["cabecera"]
    a, b = c["periodos"]["power"]
    typer.echo(power.descargar(p["lon"], p["lat"], a, b, raw))


@app.command("ingest-oni")
def ingest_oni(raw: Path = Path("data/raw")) -> None:
    typer.echo(noaa.descargar_oni(raw))


def _series(series_json: Path | None, raw: Path, cfg: dict):
    """Devuelve {nombre: (anios, valores, unidad)} desde un JSON de series o desde data/raw (offline)."""
    if series_json:
        j = json.loads(series_json.read_text())
        return {k: (np.array([int(a) for a in v["serie"]]), np.array(list(v["serie"].values())), v.get("unidad", ""))
                for k, v in j["series"].items()}, {int(k): v for k, v in j.get("oni", {}).items()}
    pw = sorted(raw.glob("power_*.json"))
    if not pw:
        raise typer.BadParameter("No hay data/raw/power_*.json: corre `tv ingest-power` o usa --series")
    par, _ = power.cargar(pw[-1])
    a, b = cfg["periodos"]["power"]
    ta, tv = temperatura_media_anual(mensual(par, "T2M"), a, b)
    la, lv = lluvia_dic_mar(mensual(par, "PRECTOTCORR"), a, b)
    oni_f = raw / "oni.ascii.txt"
    oni = noaa.cargar_oni(oni_f) if oni_f.exists() else {}
    return {"t2m_media_anual": (ta, tv, "C"), "lluvia_dic_mar": (la, lv, "mm")}, oni


@app.command("trends")
def trends(series: Path | None = typer.Option(None, help="JSON de series (modo offline/fixture)"),
           config: Path = Path("configs/chili.yaml"), raw: Path = Path("data/raw"),
           pre: Path = Path("preregistro.yaml"), out: Path = Path("expedientes")) -> None:
    cfg, prereg = cargar_yaml(config), cargar_preregistro(pre)
    datos, oni = _series(series, raw, cfg)
    for nombre, (anios, x, unidad) in datos.items():
        res = analizar_serie(anios, x, prereg, oni=oni or None)
        exp = construir_expediente(
            id=f"TV-{cfg['cuenca'].upper()}-{nombre.upper()}-001", objeto={"cuenca": cfg["cuenca"]},
            variable=nombre, anios=anios, valores=x, resultado=res, pre=prereg,
            productos=[{"id": "NASA_POWER_MERRA2"}])
        ruta = guardar(exp, out)
        typer.echo(f"{res['sello']['emoji']} {nombre}: Sen {res['sen']['sen_por_decada']:+.3f}/déc, "
                   f"p_cons={res['mk']['p_conservador']:.4g} ({res['mk']['variante_limitante']}), "
                   f"sello={res['sello']['codigo']} pendientes={res['sello']['pendientes']} "
                   f"fallan={res['sello']['fallan']} -> {ruta}")


@app.command("report")
def report(expediente: Path, out: Path = Path("reports")) -> None:
    e = json.loads(expediente.read_text())
    r = e["resultado"]
    out.mkdir(parents=True, exist_ok=True)
    L = [f"# {e['id']}", "", f"**Veredicto:** {r['sello']['emoji']} {r['sello']['codigo']}  ",
         f"**Periodo:** {e['periodo']['desde']}–{e['periodo']['hasta']} (n={e['periodo']['n']})", "",
         "| Prueba | Resultado |", "|---|---|",
         f"| Sen | {r['sen']['sen_por_decada']:+.3f}/década (IC90 {r['sen']['ic_por_decada'][0]:+.3f} a {r['sen']['ic_por_decada'][1]:+.3f}) |",
         f"| MK (p por variante) | {', '.join(f'{k}={v:.3g}' for k, v in r['mk']['p_variantes'].items())} → conservador {r['mk']['p_conservador']:.3g} |",
         f"| Ventanas | {r['ventanas']['pct_mismo_signo']:.0f} % mismo signo (robustez ante el periodo, no independiente) |"
         if r.get("ventanas") else "| Ventanas | pendiente |",
         f"| ENSO | {r['enso']}" if r.get("enso") else "| ENSO | pendiente (falta ONI) |",
         f"| Independencia | {r['independencia']}" if r.get("independencia") else "| Independencia | **pendiente** |",
         f"| Detectabilidad | {r['detectabilidad']['anios_necesarios']:.1f} años necesarios / {r['detectabilidad']['anios_disponibles']} disponibles |",
         "", "**Advertencias:** " + "; ".join(e["advertencias"]), "",
         f"_preregistro `{e['procedencia']['preregistro_sha256'][:12]}` · entradas `{e['procedencia']['entradas_sha256'][:12]}`_"]
    ruta = out / f"{e['id']}.md"
    ruta.write_text("\n".join(L), encoding="utf-8")
    typer.echo(ruta)


if __name__ == "__main__":
    app()
