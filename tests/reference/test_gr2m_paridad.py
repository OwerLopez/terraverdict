import pytest
from pathlib import Path

REF = Path(__file__).resolve().parents[1] / "fixtures/airgr/gr2m_ref.csv"


@pytest.mark.skipif(not REF.exists(), reason="Generar con Rscript tests/fixtures/airgr/generar_gr2m.R")
def test_gr2m_igual_a_airgr():
    pytest.skip("S5: implementar terraverdict.hydro.gr2m y comparar con tolerancia 1e-6")
