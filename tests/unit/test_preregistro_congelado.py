"""El preregistro y la partición temporal están congelados (decisión del equipo, 2026-11-15).

Si esta prueba falla, alguien cambió un valor preregistrado. Eso no se corrige editando el hash:
se sube `version` en preregistro.yaml, se registra el motivo en docs/bitacora.md y se regeneran
los expedientes y resultados que dependen de él.
"""

from __future__ import annotations

from pathlib import Path

from terraverdict.config import cargar_preregistro, cargar_yaml

RAIZ = Path(__file__).resolve().parents[2]
SHA256_CONGELADO = "c40676fd76ab55434bb8f0a89fe6c1bcf8845551dd884b41444682f3bd00d596"


def test_preregistro_congelado_sin_cambios() -> None:
    pre = cargar_preregistro(RAIZ / "preregistro.yaml")
    assert pre.datos["estado"] == "congelado"
    assert pre.sha256 == SHA256_CONGELADO


def test_particion_temporal_congelada() -> None:
    pt = cargar_yaml(RAIZ / "config" / "fenomenos.yaml")["particion_temporal"]
    assert pt == {
        "entrenamiento": ["1981-01-01", "2015-12-31"],
        "validacion": ["2016-01-01", "2020-12-31"],
        "prueba": ["2021-01-01", "2026-10-31"],
    }
