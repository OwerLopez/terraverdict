"""Portada: estado actual (indicadores) y tabla maestra de veredictos de los cinco fenómenos."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from app.schemas.comun import Esquema

Evidencia = Literal["confirmada", "indicio", "sin_evidencia"]
Veredicto = Literal[
    "habilidad_confirmada", "habilidad_con_indicio", "sin_habilidad", "descriptivo", "recurrencia_historica", "abstencion"
]


class Tendencia(Esquema):
    """Lectura histórica del fenómeno, tal como la publica su expediente."""

    tipo: Literal["pendiente", "valor_b", "probabilidad_anual", "eventos"]
    variable: str | None = Field(None, description="Qué se mide (p. ej. 'lluvia dic–mar', 'Misti').")
    valor: float | None = None
    intervalo: list[float] | None = Field(None, description="IC90 [lo, hi] cuando existe.")
    unidad: str | None = None
    veredicto: str | None = Field(None, description="Veredicto del expediente (p. ej. 'preliminar', 'sin_tendencia').")
    periodo: str | None = None
    expediente_id: str | None = None


class Anticipacion(Esquema):
    """Habilidad fuera de muestra del modelo elegido en la validación (nunca el mejor en la prueba)."""

    metrica: str
    valor: float | None
    intervalo: list[float] | None = None
    p_diebold_mariano: float | None = None
    modelo: str
    familia: str | None = None
    horizonte: str | None = None
    periodo_prueba: str | None = None
    evidencia: Evidencia
    expediente_id: str


class FilaVeredicto(Esquema):
    fenomeno: Literal["lluvia_extrema", "sequia", "sismos", "volcanes", "deslizamientos"]
    fuentes: list[str]
    tendencia: Tendencia | None = None
    anticipacion: Anticipacion | None = None
    abstencion: list[str] = Field(default_factory=list, description="Motivos de abstención publicados.")
    veredicto: Veredicto


class Portada(Esquema):
    indicadores: dict[str, Any] | None = Field(
        None,
        description=(
            "Contenido de resultados/contrato/indicadores.json (ENSO, SPI-3 actual, sequía según ENSO, altitud), "
            "generado por `tv publicar` desde los crudos con su SHA-256. Null si no existe."
        ),
    )
    filas: list[FilaVeredicto]
    lluvia_eventos_documentados: list[dict[str, Any]] = Field(
        default_factory=list, description="Desempeño del modelo de lluvia en los meses de eventos documentados."
    )
    regla_evidencia: str
    aviso: str
