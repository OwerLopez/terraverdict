import json
from pathlib import Path

import numpy as np
import pytest

from terraverdict.config import cargar_preregistro

RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def pre():
    return cargar_preregistro(RAIZ / "preregistro.yaml")


@pytest.fixture(scope="session")
def fx():
    j = json.loads((RAIZ / "tests/fixtures/preliminar_series.json").read_text())
    s = {k: (np.array([int(a) for a in v["serie"]], float), np.array(list(v["serie"].values()))) for k, v in j["series"].items()}
    return s, j["esperado"]
