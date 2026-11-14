"""Golden: reproduce analisis_preliminar.json desde las series guardadas (sin red)."""
import pytest

from terraverdict.trends.analizar import analizar_serie


@pytest.mark.parametrize("nombre", ["t2m_media_anual", "lluvia_dic_mar"])
def test_reproduce_preliminar(fx, pre, nombre):
    series, esp = fx
    anios, x = series[nombre]
    e = esp[nombre]
    r = analizar_serie(anios, x, pre)
    assert round(r["sen"]["sen_por_decada"], 4) == pytest.approx(e["sen_por_decada"], abs=1e-4)
    # El JSON guarda la serie redondeada a 3 decimales (cambia ties) -> tolerancia 1e-3 en el IC.
    assert r["sen"]["ic_por_decada"] == pytest.approx(e["ic90"], abs=1e-3)
    assert r["ventanas"]["n_ventanas"] == e["n_ventanas"]
    assert round(r["ventanas"]["pct_mismo_signo"], 1) == e["pct_mismo_signo"]
    d = r["detectabilidad"]
    assert round(d["sigma_ruido"], 4) == pytest.approx(e["sigma"], abs=1e-3)
    assert round(d["phi_ar1"], 3) == pytest.approx(e["phi"], abs=1e-3)
    assert round(d["anios_necesarios"], 1) == pytest.approx(e["n_star"], abs=0.1)


def test_p_conservador_lluvia_no_es_hamed_rao(fx, pre):
    """Hallazgo 2: HR da p=0.0002 pero el conservador debe ser ≥ MK original (0.057)."""
    anios, x = fx[0]["lluvia_dic_mar"]
    r = analizar_serie(anios, x, pre, con_ventanas=False)
    assert r["mk"]["p_variantes"]["hamed_rao"] < 0.001
    assert r["mk"]["p_conservador"] >= 0.0568 - 1e-3
    assert r["mk"]["variante_limitante"] == "prewhitening"


def test_temperatura_sobrevive_sin_2023_2024(fx, pre):
    """Hallazgo 3: el salto 2023-24 no debe ser lo único que sostiene la tendencia."""
    anios, x = fx[0]["t2m_media_anual"]
    r = analizar_serie(anios[:-2], x[:-2], pre, con_ventanas=False)
    assert r["sen"]["sen_por_decada"] > 0.15 and r["mk"]["p_conservador"] < pre.alpha


def test_sello_con_una_familia_nunca_es_robusto(fx, pre):
    anios, x = fx[0]["t2m_media_anual"]
    r = analizar_serie(anios, x, pre, con_ventanas=False)
    assert r["sello"]["codigo"] == "fragil" and "independencia" in r["sello"]["pendientes"]
