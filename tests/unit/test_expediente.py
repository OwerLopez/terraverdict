from terraverdict.expedientes.build import construir_expediente
from terraverdict.expedientes.hash import sha256_json
from terraverdict.trends.analizar import analizar_serie


def test_hash_estable_y_sensible(fx, pre):
    a, x = fx[0]["t2m_media_anual"]
    assert sha256_json({"x": x, "a": a}) == sha256_json({"a": a, "x": x})
    assert sha256_json({"x": x}) != sha256_json({"x": x + 1e-9})


def test_expediente_declara_independencia_pendiente(fx, pre):
    a, x = fx[0]["t2m_media_anual"]
    r = analizar_serie(a, x, pre, con_ventanas=False)
    e = construir_expediente(id="TV-T", objeto={}, variable="t2m", anios=a, valores=x, resultado=r,
                             productos=[{"id": "POWER"}], pre=pre)
    assert any("independencia" in w for w in e.advertencias)
    assert e.procedencia.preregistro_sha256 == pre.sha256
