"""Lectores de CHIRPS (ClimateSERV), IGP, IMERG (OPeNDAP) y MODIS (ORNL) sobre el formato real de cada API.

Los registros de ejemplo son copias literales de respuestas reales (2026-11-15), salvo el de IMERG:
GES DISC exige aceptar su licencia para leer datos, así que su formato se tomó de la salida ASCII de
arreglos de un servidor Hyrax público (test.opendap.org), el mismo software que usa GES DISC.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from terraverdict.ingest import chirps, earthdata, igp, modis


def test_chirps_lee_fechas_y_descarta_sin_dato(tmp_path: Path) -> None:
    datos = {
        "data": [
            {"date": "01/01/2020", "raw_value": 1.2131267786026, "value": {"avg": 1.2131267786026}},
            {"date": "01/02/2020", "raw_value": 6.271523475646973, "value": {"avg": 6.271523475646973}},
            {"date": "01/03/2020", "raw_value": -9999.0, "value": {"avg": -9999.0}},
        ]
    }
    (tmp_path / "chirps_cabecera_local_2020_2020.json").write_text(json.dumps(datos))
    assert chirps.cargar(tmp_path, "cabecera_local") == {"2020-01-01": 1.2131267786026, "2020-01-02": 6.271523475646973}


def test_chirps_caja_cerrada() -> None:
    c = chirps.caja(-71.25, -15.95, 0.1, 0.1)["coordinates"][0]
    assert c[0] == c[-1] and len(c) == 5
    assert c[0] == pytest.approx([-71.3, -16.0])


def test_igp_convierte_hora_local_a_utc(tmp_path: Path) -> None:
    real = {
        "codigo": "2024-0001",
        "fecha_local": "2024-01-01T00:00:00.000Z",
        "hora_local": "1970-01-01T02:06:07.000Z",
        "latitud": "-10.69",
        "longitud": "-78.54",
        "magnitud": "4.2",
        "profundidad": 35,
        "referencia": "81 km al SO de Huarmey, Huarmey - Ancash",
        "tipomagnitud": "",
    }
    antiguo = {  # formato hasta 2018: sin 'codigo' (copia literal de igp_2013.json)
        "idlistasismos": 295,
        "fecha_local": "2013-01-03T00:00:00.000Z",
        "hora_local": "1970-01-01T21:14:37.000Z",
        "fecha_utc": "2013-01-04T00:00:00.000Z",
        "hora_utc": "1970-01-01T02:14:37.000Z",
        "latitud": "-5.84",
        "longitud": "-75.97",
        "magnitud": "4.2",
        "profundidad": 35,
        "tipomagnitud": "ML",
    }
    (tmp_path / "igp_2024.json").write_text(json.dumps([real, {**real, "magnitud": None, "codigo": "malo"}]))
    (tmp_path / "igp_2013.json").write_text(json.dumps([antiguo]))
    e = igp.cargar(tmp_path)
    assert len(e) == 2
    assert (e[0]["id"], e[0]["tiempo"]) == ("igp-295", "2013-01-04T02:14:37")  # coincide con fecha_utc/hora_utc
    e = e[1:]
    assert e[0]["tiempo"] == "2024-01-01T07:06:07"  # 02:06:07 en Lima = 07:06:07 UTC
    assert (e[0]["magnitud"], e[0]["profundidad_km"], e[0]["tipo_magnitud"]) == (4.2, 35.0, None)


def test_imerg_indices_y_lectura(tmp_path: Path) -> None:
    assert earthdata.indice_imerg(-71.25, -15.95) == (1087, 740)
    assert earthdata.indice_imerg(-71.535, -16.4) == (1084, 736)
    texto = (
        "### 2020-01-01\nDataset: 3B-DAY.MS.MRG.3IMERG.20200101-S000000-E235959.V07B.nc4\n"
        "precipitation.precipitation[0][0], 0.5, 1.5, 2.5\n"
        "precipitation.precipitation[0][1], 3.5, -9999.9, 4.5\n"
        "### 2020-01-02\nDataset: x\n"
        "precipitation.precipitation[0][0], 0, 0, 7\n"
        "precipitation.precipitation[0][1], 0, 8, 9\n"
    )
    (tmp_path / "imerg_diaria_2020.txt").write_text(texto)
    assert earthdata.cargar_imerg(tmp_path, 1085, 742, 1084, 740) == {"2020-01-01": 4.5, "2020-01-02": 9.0}
    assert earthdata.cargar_imerg(tmp_path, 1085, 741, 1084, 740) == {"2020-01-02": 8.0}  # −9999,9 = sin dato


def test_token_earthdata(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EARTHDATA_TOKEN", raising=False)
    solo = tmp_path / "solo"
    solo.write_text("abc.def.ghi\n")
    assert earthdata.token_earthdata(solo) == "abc.def.ghi"
    clave = tmp_path / "clave"
    clave.write_text("OTRA=1\nEARTHDATA_TOKEN='xyz'\n")
    assert earthdata.token_earthdata(clave) == "xyz"
    monkeypatch.setenv("EARTHDATA_TOKEN", "env")
    assert earthdata.token_earthdata(clave) == "env"
    monkeypatch.delenv("EARTHDATA_TOKEN")
    with pytest.raises(RuntimeError):
        earthdata.token_earthdata(tmp_path / "no_existe")


def test_modis_escala_y_nulos(tmp_path: Path) -> None:
    j = {
        "subset": [
            {"modis_date": "A2020001", "calendar_date": "2020-01-01", "band": "LST_Day_1km", "data": [15159]},
            {"modis_date": "A2020009", "calendar_date": "2020-01-09", "band": "LST_Day_1km", "data": [0]},
        ]
    }
    (tmp_path / "modis_cabecera_LST_Day_1km.json").write_text(json.dumps(j))
    assert modis.cargar(tmp_path, "cabecera", "LST_Day_1km") == {"2020-01-01": pytest.approx(15159 * 0.02 - 273.15)}
