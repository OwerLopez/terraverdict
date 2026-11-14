import numpy as np

from terraverdict.trends.analizar import analizar_serie
from terraverdict.trends.sen import sen_por_decada


def test_sen_recupera_pendiente_conocida():
    rng = np.random.default_rng(0)
    a = np.arange(1981, 2025.0)
    x = 5 + 0.03 * (a - a[0]) + rng.normal(0, 0.2, len(a))
    s = sen_por_decada(a, x)
    assert s["ic_por_decada"][0] <= 0.30 <= s["ic_por_decada"][1]


def test_enso_sintetico_separa_tendencia_de_oni(pre):
    rng = np.random.default_rng(1)
    a = np.arange(1981, 2025.0)
    oni = {int(y): float(v) for y, v in zip(a, rng.normal(0, 1, len(a)), strict=False)}
    x = 5 + 0.02 * (a - a[0]) + 0.5 * np.array(list(oni.values())) + rng.normal(0, 0.1, len(a))
    r = analizar_serie(a, x, pre, oni=oni, con_ventanas=False)
    assert abs(r["enso"]["pendiente_sin_enso_por_decada"] - 0.2) < 0.1
    assert abs(r["enso"]["coef_oni"] - 0.5) < 0.1


def test_sensor_detecta_escalon_falso(pre):
    a = np.arange(1998, 2025.0)
    x = 1.0 + 0.0 * a + (a >= 2014.5) * 2.0  # solo un escalón, sin tendencia real
    r = analizar_serie(a, x, pre, con_ventanas=False, producto_primario="IMERG_FINAL")
    q = r["sensor"]["quiebres"]["trmm_a_gpm"]
    assert q["aplicable"] and q["delta_aic"] < -10
