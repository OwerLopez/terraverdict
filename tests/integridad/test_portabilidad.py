"""Portabilidad a Windows: texto siempre en UTF-8 y fin de línea LF.

- `Path.read_text()` sin `encoding` usa la página de códigos local en Windows (cp1252): los JSON y
  YAML con tildes fallan con UnicodeDecodeError o se leen corruptos.
- `Path.write_text()` traduce '\\n' a CRLF en Windows: el SHA-256 de un resultado sellado cambiaría
  al subirlo a git (que normaliza a LF) y `tv verificar-integridad` lo vería alterado.
- Con `core.autocrlf=true`, el checkout convierte LF→CRLF; `.gitattributes` lo impide.
"""

from __future__ import annotations

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PRODUCCION = ("src", "backend/app", "api")
TODO = (*PRODUCCION, "tests", "backend/tests")


def _lineas(carpetas: tuple[str, ...]) -> list[tuple[str, int, str]]:
    return [
        (str(p.relative_to(RAIZ)), n, linea)
        for c in carpetas
        for p in (RAIZ / c).rglob("*.py")
        if ".venv" not in p.parts and p.name != "test_portabilidad.py"
        for n, linea in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
    ]


def test_toda_lectura_de_texto_declara_utf8() -> None:
    faltan = [f"{r}:{n}" for r, n, linea in _lineas(TODO) if ".read_text(" in linea and "encoding=" not in linea]
    assert not faltan, f"read_text sin encoding='utf-8': {faltan}"


def test_escrituras_de_produccion_en_utf8_y_lf() -> None:
    faltan = [
        f"{r}:{n}"
        for r, n, linea in _lineas(PRODUCCION)
        if ".write_text(" in linea and not ("encoding=" in linea and "newline=" in linea)
    ]
    assert not faltan, f"write_text sin encoding='utf-8' y newline: {faltan}"


def test_gitattributes_fuerza_lf() -> None:
    reglas = (RAIZ / ".gitattributes").read_text(encoding="utf-8").splitlines()
    assert "* text=auto eol=lf" in reglas


def test_la_cli_imprime_unicode_con_una_consola_cp1252() -> None:
    """Con stdout en cp1252 (consola de Windows), `tv` no debe caerse al imprimir '→' o '±'."""
    import subprocess
    import sys

    codigo = "import terraverdict.cli; print('→ ± ≥ áéí')"
    r = subprocess.run(
        [sys.executable, "-c", codigo],
        capture_output=True,
        env={**__import__("os").environ, "PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0"},
        check=False,
    )
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    assert "→" in r.stdout.decode("utf-8")


def test_escritura_atomica_reintenta_un_bloqueo_transitorio(tmp_path: Path, monkeypatch: object) -> None:
    """Un bloqueo momentáneo (antivirus en Windows) no tumba la corrida ni deja archivos a medias."""
    import os

    from terraverdict.integridad import escribir_texto

    destino = tmp_path / "r.json"
    original = os.replace
    fallos = {"n": 2}

    def replace(a: str, b: str) -> None:
        if fallos["n"]:
            fallos["n"] -= 1
            raise OSError(22, "Invalid argument")
        original(a, b)

    monkeypatch.setattr(os, "replace", replace)  # type: ignore[attr-defined]
    escribir_texto(destino, "á\n")
    assert destino.read_bytes() == "á\n".encode()
    assert [p.name for p in tmp_path.iterdir()] == ["r.json"]  # sin temporales huérfanos
