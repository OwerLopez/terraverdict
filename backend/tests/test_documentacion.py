"""La documentación de la API cubre cada código de error que el backend puede devolver."""

import re

from app.core import errors
from app.core.config import RAIZ_REPO


def test_cada_codigo_de_error_tiene_su_ancla() -> None:
    doc = (RAIZ_REPO / "docs" / "api" / "README.md").read_text(encoding="utf-8")
    fuente = (RAIZ_REPO / "backend" / "app" / "core" / "errors.py").read_text(encoding="utf-8")
    codigos = {c.codigo for c in errors.ErrorDominio.__subclasses__()} | {errors.ErrorDominio.codigo}
    codigos |= set(re.findall(r'codigo="([a-z_]+)"', fuente)) | {c for c, _ in errors._CODIGOS_HTTP.values()}
    codigos.add("error_http")
    faltan = sorted(c for c in codigos if f"### errores-{c}" not in doc)
    assert not faltan, f"Códigos sin documentar en docs/api/README.md: {faltan}"
    assert errors.TIPO_BASE.endswith("docs/api/README.md#errores")
