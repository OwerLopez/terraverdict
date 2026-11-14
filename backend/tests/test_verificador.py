import pytest

from app.services.verificador import extraer_cifras, valores_numericos, verificar


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("sube 0,23 °C", [0.23]),
        ("r = −0,345", [-0.345]),
        ("1.234,5 hm³", [1234.5]),
        ("10 135 gránulos", [10135.0]),
        ("39 %", [39.0]),
        ("+16,8 mm", [16.8]),
    ],
)
def test_extraccion_formatos_en_espanol(texto: str, esperado: list[float]) -> None:
    assert [c.valor for c in extraer_cifras(texto)] == esperado


def test_ignora_anios_e_identificadores() -> None:
    assert extraer_cifras("Entre 1981 y 2024, en P1 y TV-TEN-3F2A") == []


def test_redondeo_valido_y_no_trazable() -> None:
    permitidos = [0.2257, 0.1504, 0.303, -0.345, 0.39]
    resultado = verificar("Sube 0,23 (0,15–0,30), r = −0,35, 39 % y 0,99.", permitidos)
    assert not resultado.aprobado
    assert resultado.no_trazables == ["0,99"]
    assert verificar("Sube 0,23 por década.", permitidos).aprobado


def test_redondeo_segun_decimales_escritos() -> None:
    assert verificar("Sube 0,2 por década.", [0.2257]).aprobado  # 0,2 es un redondeo válido (±0,05)
    assert not verificar("Sube 0,30 por década.", [0.2257]).aprobado  # 0,30 exige ±0,005


def test_valores_numericos_excluye_booleanos() -> None:
    assert valores_numericos({"a": 1, "b": [2.5, {"c": True}], "d": "3"}) == [1.0, 2.5]
