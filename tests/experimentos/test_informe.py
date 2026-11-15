"""El informe se genera solo desde resultados/*.json y reproduce sus cifras."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from terraverdict.experimentos import informe

RAIZ = Path(__file__).resolve().parents[2]
RESULTADOS = RAIZ / "resultados"

pytestmark = pytest.mark.skipif(not (RESULTADOS / "indice.json").exists(), reason="sin resultados/")


@pytest.fixture(scope="module")
def texto() -> str:
    return informe.generar(RESULTADOS)


def test_secciones_de_cada_experimento(texto: str) -> None:
    indice = json.loads((RESULTADOS / "indice.json").read_text())
    titulos = {
        "lluvia_extrema": "Lluvia fuerte a 1 día · NASA POWER",
        "lluvia_extrema_chirps": "Lluvia fuerte a 1 día · CHIRPS",
        "sequia": "Sequía (SPI-3) · NASA POWER",
        "sequia_chirps": "Sequía (SPI-3) · CHIRPS",
        "sismos": "## Sismos",
        "volcanes": "## Volcanes",
        "deslizamientos": "## Deslizamientos",
        "caos": "## Dinámica",
        "fuentes": "## Contraste entre fuentes",
        "nacional": "## Escala nacional · 25 departamentos",
        "historial": "## Historial de métricas · origen móvil y dinámica en ventanas",
    }
    for experimento in indice["experimentos"]:
        assert titulos[experimento] in texto
    assert indice["commit"] in texto


def test_cifras_iguales_a_los_json(texto: str) -> None:
    for nombre in ("lluvia_extrema", "sismos"):
        r = json.loads((RESULTADOS / f"{nombre}.json").read_text())
        zoo = r["zoo"] if "zoo" in r else r["pronostico_conteos"]["zoo"]
        m = zoo["modelos"][zoo["mejor_validacion"]]
        assert informe.n(m["prueba"][m["metrica_principal"]]) in texto
        assert informe.ic(m["ic90_prueba"]) in texto
    v = json.loads((RESULTADOS / "volcanes.json").read_text())["volcanes"][0]
    assert informe.n(100 * v["probabilidad_anual_inicio"], 2) in texto


def test_sin_valores_crudos_de_python(texto: str) -> None:
    for basura in ("None", "nan", "NaN", "inf"):
        assert f" {basura} " not in texto and f"| {basura} |" not in texto


def test_formato_numerico() -> None:
    assert informe.n(-0.0001) == "0,000"
    assert informe.n(1234) == "1 234"
    assert informe.ic([0.1, None]) == "—"
    assert informe.tabla(["a"], [["x|y"]]).splitlines()[-1] == "| x\\|y |"


def test_regla_de_evidencia_exige_ic_y_diebold_mariano() -> None:
    base = {"ic90_prueba": [0.01, 0.2], "diebold_mariano_vs_climatologia": {"p": 0.05}}
    assert informe.nivel_evidencia(base) == "confirmada"
    assert informe.nivel_evidencia({**base, "diebold_mariano_vs_climatologia": {"p": 0.15}}) == "indicio"
    assert informe.nivel_evidencia({**base, "ic90_prueba": [-0.01, 0.2]}) == "indicio"
    assert (
        informe.nivel_evidencia({"ic90_prueba": [-0.01, 0.2], "diebold_mariano_vs_climatologia": {"p": 0.4}})
        == "no_confirmada"
    )
