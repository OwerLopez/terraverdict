"""CLI: tv ingest-power | ingest-oni | ingest-fenomenos | trends | report | experimentos"""

from __future__ import annotations

import copy
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
def ingest_power(config: Path = Path("config/chili.yaml"), raw: Path = Path("data/raw")) -> None:
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
        return {
            k: (np.array([int(a) for a in v["serie"]]), np.array(list(v["serie"].values())), v.get("unidad", ""))
            for k, v in j["series"].items()
        }, {int(k): v for k, v in j.get("oni", {}).items()}
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
def trends(
    series: Path | None = typer.Option(None, help="JSON de series (modo offline/fixture)"),
    config: Path = Path("config/chili.yaml"),
    raw: Path = Path("data/raw"),
    pre: Path = Path("preregistro.yaml"),
    out: Path = Path("expedientes"),
) -> None:
    cfg, prereg = cargar_yaml(config), cargar_preregistro(pre)
    datos, oni = _series(series, raw, cfg)
    for nombre, (anios, x, _unidad) in datos.items():
        res = analizar_serie(anios, x, prereg, oni=oni or None)
        exp = construir_expediente(
            id=f"TV-{cfg['cuenca'].upper()}-{nombre.upper()}-001",
            objeto={"cuenca": cfg["cuenca"]},
            variable=nombre,
            anios=anios,
            valores=x,
            resultado=res,
            pre=prereg,
            productos=[{"id": "NASA_POWER_MERRA2"}],
        )
        ruta = guardar(exp, out)
        typer.echo(
            f"{res['sello']['emoji']} {nombre}: Sen {res['sen']['sen_por_decada']:+.3f}/déc, "
            f"p_cons={res['mk']['p_conservador']:.4g} ({res['mk']['variante_limitante']}), "
            f"sello={res['sello']['codigo']} pendientes={res['sello']['pendientes']} "
            f"fallan={res['sello']['fallan']} -> {ruta}"
        )


@app.command("report")
def report(expediente: Path, out: Path = Path("reports")) -> None:
    e = json.loads(expediente.read_text())
    r = e["resultado"]
    out.mkdir(parents=True, exist_ok=True)
    L = [
        f"# {e['id']}",
        "",
        f"**Veredicto:** {r['sello']['emoji']} {r['sello']['codigo']}  ",
        f"**Periodo:** {e['periodo']['desde']}–{e['periodo']['hasta']} (n={e['periodo']['n']})",
        "",
        "| Prueba | Resultado |",
        "|---|---|",
        f"| Sen | {r['sen']['sen_por_decada']:+.3f}/década (IC90 {r['sen']['ic_por_decada'][0]:+.3f} a {r['sen']['ic_por_decada'][1]:+.3f}) |",
        f"| MK (p por variante) | {', '.join(f'{k}={v:.3g}' for k, v in r['mk']['p_variantes'].items())} → conservador {r['mk']['p_conservador']:.3g} |",
        f"| Ventanas | {r['ventanas']['pct_mismo_signo']:.0f} % mismo signo (robustez ante el periodo, no independiente) |"
        if r.get("ventanas")
        else "| Ventanas | pendiente |",
        f"| ENSO | {r['enso']}" if r.get("enso") else "| ENSO | pendiente (falta ONI) |",
        f"| Independencia | {r['independencia']}" if r.get("independencia") else "| Independencia | **pendiente** |",
        f"| Detectabilidad | {r['detectabilidad']['anios_necesarios']:.1f} años necesarios / {r['detectabilidad']['anios_disponibles']} disponibles |",
        "",
        "**Advertencias:** " + "; ".join(e["advertencias"]),
        "",
        f"_preregistro `{e['procedencia']['preregistro_sha256'][:12]}` · entradas `{e['procedencia']['entradas_sha256'][:12]}`_",
    ]
    ruta = out / f"{e['id']}.md"
    ruta.write_text("\n".join(L), encoding="utf-8")
    typer.echo(ruta)


@app.command("ingest-fenomenos")
def ingest_fenomenos(
    config: Path = Path("config/fenomenos.yaml"),
    raw: Path = Path("data/raw"),
    solo_adicionales: bool = typer.Option(
        False, help="Solo CHIRPS, IGP, IMERG y MODIS; conserva el resto del registro"
    ),
    fuentes: str = typer.Option("chirps,igp,imerg,modis", help="Fuentes adicionales (con --solo-adicionales)"),
    tolerar_fallos: bool = typer.Option(
        False, help="Termina con código 0 aunque falle alguna fuente (p. ej. entornos sin acceso a ellas)"
    ),
) -> None:
    """Descarga trazable de todas las fuentes de los cinco fenómenos (con manifiesto SHA-256).

    Termina con código 1 si falla alguna fuente pedida: una descarga incompleta no debe pasar por buena.
    """
    from .ingest import fenomenos, glc

    cfg = cargar_yaml(config)
    ruta = raw / "registro_descarga.json"
    if solo_adicionales:
        inicial = json.loads(ruta.read_text()) if ruta.exists() else {}
        reg = copy.deepcopy(inicial)
        fenomenos.descargar_fuentes_adicionales(cfg, raw, reg, tuple(fuentes.split(",")))
        fenomenos.registrar_desde_manifiestos(reg, raw)
        # Otra ingesta pudo escribir el registro mientras esta descargaba (p. ej., IMERG y MODIS en
        # paralelo): se relee y solo se actualizan los pasos que cambió esta corrida.
        actual = json.loads(ruta.read_text()) if ruta.exists() else {}
        actual.update({k: v for k, v in reg.items() if inicial.get(k) != v})
        reg = actual
    else:
        reg = fenomenos.descargar_todo(cfg, raw)
        if reg.get("glc", {}).get("ok"):
            reg["celdas_deslizamientos"] = fenomenos.descargar_celdas_deslizamientos(glc.cargar(raw / "glc"), cfg, raw)
    fenomenos.guardar_registro(reg, ruta)
    pedidas = tuple(fuentes.split(",")) if solo_adicionales else None
    fallidas = []
    for nombre, paso in reg.items():
        if isinstance(paso, dict) and "ok" in paso:
            typer.echo(f"{'OK ' if paso['ok'] else 'ERR'} {nombre} {paso.get('error') or ''}")
            if not paso["ok"] and (pedidas is None or nombre.startswith(pedidas)):
                fallidas.append(nombre)
    if fallidas and not tolerar_fallos:
        typer.echo(f"Fuentes con error: {', '.join(fallidas)} (use --tolerar-fallos para aceptarlo)", err=True)
        raise typer.Exit(code=1)


@app.command("experimentos")
def experimentos(
    rapido: bool = typer.Option(False, help="Solo GRU y TCN con una semilla (para probar el pipeline)"),
    solo: list[str] = typer.Option(
        None,
        help="volcanes, deslizamientos, sismos, fuentes, sequia, sequia_chirps, lluvia_extrema, lluvia_extrema_chirps, caos, nacional, historial",
    ),
) -> None:
    """Ejecuta los experimentos reproducibles y escribe resultados/*.json con su procedencia."""
    from .experimentos.ejecutar import ejecutar

    typer.echo(json.dumps(ejecutar(rapido=rapido, solo=solo or None), ensure_ascii=False, indent=1))


@app.command("informe")
def informe(resultados: Path = Path("resultados"), salida: Path = Path("docs/experimentos.md")) -> None:
    """Genera docs/experimentos.md solo con las cifras de resultados/*.json."""
    from .experimentos.informe import generar

    salida.write_text(generar(resultados), encoding="utf-8")
    typer.echo(f"Informe escrito en {salida}")


@app.command("publicar")
def publicar(
    api: str = typer.Option("http://localhost:8000", help="URL base del backend"),
    resultados: Path = Path("resultados"),
    expedientes: Path = Path("expedientes"),
    pre: Path = Path("preregistro.yaml"),
    config: Path = Path("config/fenomenos.yaml"),
    simular: bool = typer.Option(False, help="Solo convierte y escribe los expedientes, sin enviarlos"),
    exportar: Path = typer.Option(
        None, help="Escribe los expedientes del contrato en este archivo (p. ej. resultados/contrato/expedientes.json)"
    ),
) -> None:
    """Publica resultados/*.json y expedientes/*.json en el backend (idempotente por contenido)."""
    from .publicar import cliente, convertir

    minimo = cargar_yaml(config)["abstencion"]["eventos_minimos_umbral"]
    lista = convertir.de_resultados(resultados, minimo) + convertir.de_expedientes(
        expedientes, cargar_preregistro(pre).alpha
    )
    if simular:
        typer.echo(json.dumps(lista, ensure_ascii=False, indent=1))
        return
    if exportar:
        # Contrato como interfaz: el backend importa este archivo al arrancar (sin depender de este paquete).
        exportar.write_text(json.dumps(lista, ensure_ascii=False, indent=1), encoding="utf-8")
        typer.echo(f"{len(lista)} expedientes exportados a {exportar}")
        return
    informe = cliente.publicar(lista, api, cliente.clave_ingesta())
    for i in informe:
        typer.echo(f"{i['http']} {i['estado']:<10} {i['id'] or '-'}  {i['titulo']}")
        if i["errores"]:
            typer.echo(f"    {i['errores']}")
    if any(i["estado"] == "error" for i in informe):
        raise typer.Exit(1)


@app.command("verificar-integridad")
def verificar_integridad(raw: Path = Path("data/raw"), resultados: Path = Path("resultados")) -> None:
    """Cadena de custodia: crudos frente a sus manifiestos y resultados frente a sus sellos SHA-256."""
    from .integridad import verificar_crudos, verificar_resultados

    c = verificar_crudos(raw)
    r = verificar_resultados(resultados) if (resultados / "indice.json").exists() else {"ok": True, "sellados": 0}
    typer.echo(json.dumps({"crudos": c, "resultados": r}, ensure_ascii=False, indent=1))
    if not (c["ok"] and r["ok"]):
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
