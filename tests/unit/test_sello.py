import copy

from terraverdict.trends.sello import decidir

BASE = {"mk": {"p_conservador": 0.001}, "sen": {"pendiente": 0.02},
        "ventanas": {"pct_mismo_signo": 100.0},
        "enso": {"evaluada": True, "pendiente_sin_enso_por_decada": 0.2, "p_pendiente_sin_enso_hac": 0.01},
        "sensor": {"quiebres": {"x": {"aplicable": True, "cambia_signo": False, "cambio_relativo_b": 0.1}}},
        "independencia": {"n_familias_mismo_signo": 2},
        "palanca": {"evaluada": True, "sobrevive": True},
        "detectabilidad": {"anios_necesarios": 14, "anios_disponibles": 44}}


def test_robusta_cuando_todo_pasa(pre):
    assert decidir(BASE, pre).codigo == "robusta"


def test_cada_falla_se_nombra(pre):
    for clave, cambio, nombre in [
        ("ventanas", {"pct_mismo_signo": 50.0}, "ventanas"),
        ("enso", {"evaluada": True, "pendiente_sin_enso_por_decada": -0.1, "p_pendiente_sin_enso_hac": 0.5}, "enso"),
        ("independencia", {"n_familias_mismo_signo": 1}, "independencia"),
        ("palanca", {"evaluada": True, "sobrevive": False}, "palanca"),
        ("sensor", {"quiebres": {"x": {"aplicable": True, "cambia_signo": True, "cambio_relativo_b": 2}}}, "sensor")]:
        r = copy.deepcopy(BASE); r[clave] = cambio
        v = decidir(r, pre)
        assert v.codigo == "fragil" and nombre in v.fallan


def test_no_decidible_vs_sin_tendencia(pre):
    r = copy.deepcopy(BASE); r["mk"]["p_conservador"] = 0.4
    r["detectabilidad"] = {"anios_necesarios": 60, "anios_disponibles": 44}
    assert decidir(r, pre).codigo == "no_decidible"
    r["detectabilidad"] = {"anios_necesarios": 10, "anios_disponibles": 44}
    assert decidir(r, pre).codigo == "sin_tendencia"


def test_prueba_pendiente_impide_robusta(pre):
    r = copy.deepcopy(BASE); r["independencia"] = None
    v = decidir(r, pre)
    assert v.codigo == "fragil" and v.pendientes == ["independencia"]
