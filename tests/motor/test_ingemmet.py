"""INGEMMET: cadena TLS sin desactivar la verificación y geometría de la línea base."""

from pathlib import Path

import numpy as np
import pytest

from terraverdict.experimentos.deslizamientos import _dentro, _km
from terraverdict.ingest import ingemmet


def test_intermedio_coincide_con_la_huella_fijada():
    assert ingemmet.huella_pem(ingemmet.INTERMEDIO.read_text(encoding="utf-8")) == ingemmet.HUELLA_INTERMEDIO


def test_intermedio_alterado_se_rechaza(tmp_path: Path):
    falso = tmp_path / "falso.pem"
    texto = ingemmet.INTERMEDIO.read_text(encoding="utf-8").splitlines()
    texto[5] = texto[5][:-4] + "AAAA"
    falso.write_text("\n".join(texto), encoding="utf-8", newline="\n")
    with pytest.raises(ValueError, match="huella"), ingemmet.almacen_con_intermedio(falso):
        pass


def test_el_codigo_no_desactiva_la_verificacion_tls():
    fuente = Path(ingemmet.__file__).read_text(encoding="utf-8")
    assert "verify=False" not in fuente and "CERT_NONE" not in fuente


def test_punto_en_poligono_y_distancia():
    cuadrado = [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]
    x, y = np.array([0.5, 1.5, 0.2]), np.array([0.5, 0.5, 0.9])
    assert _dentro(x, y, cuadrado).tolist() == [True, False, True]
    # 1° de latitud ≈ 111,2 km
    assert abs(float(_km(0.0, 0.0, np.array([1.0]), np.array([0.0]))[0]) - 111.19) < 0.1
