"""Ejecuciones del pipeline, matriz de relevancia, resumen del sistema y asistente."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from app.schemas.catalogo import ProblemaSalida, VariableSalida
from app.schemas.comun import Esquema, IdSlug


class EjecucionCrear(Esquema):
    id: IdSlug
    etapa: str = Field(min_length=2, max_length=40, examples=["E2_ingesta", "E5_derivados"])
    estado: Literal["exitosa", "fallida", "parcial"]
    iniciado: datetime
    finalizado: datetime | None = None
    manifiesto: dict[str, Any] = Field(
        description="Entradas, hashes, conteos, descartes por QC, duración y errores de la corrida."
    )


class EjecucionSalida(EjecucionCrear):
    registrado_por: str
    registrado_en: datetime


class CeldaRelevancia(Esquema):
    problema_id: str
    variable_id: str
    importancia: float
    estabilidad: float
    p_ajustado: float | None
    direccion: str
    expediente_id: str
    publicable: bool


class MatrizRelevancia(Esquema):
    estado: Literal["vacia", "disponible"]
    mensaje: str
    problemas: list[ProblemaSalida]
    variables: list[VariableSalida]
    celdas: list[CeldaRelevancia]
    expedientes: list[str]


class ConteoPorClave(Esquema):
    clave: str
    total: int


class ConteoVerificacion(Esquema):
    """Resultado agregado del último informe de verificación de un tipo."""

    generado_utc: datetime
    total: int = Field(ge=0, description="Consultas o enlaces revisados.")
    correctas: int = Field(ge=0, description="Los que respondieron como se esperaba.")


class ResumenSistema(Esquema):
    version_api: str
    fuentes_total: int
    fuentes_por_estado: list[ConteoPorClave]
    verificacion_fuentes: ConteoVerificacion | None = Field(
        description="Consultas reales a catálogos oficiales (CMR, AppEEARS, POWER, NOAA, Copernicus)."
    )
    verificacion_enlaces: ConteoVerificacion | None = Field(
        description="Enlaces del reto y de la guía que respondieron HTTP 200."
    )
    series_total: int
    observaciones_total: int
    expedientes_por_tipo: list[ConteoPorClave]
    procesos_por_estado: list[ConteoPorClave]
    eventos_documentados: int
    ultima_ejecucion: datetime | None
    asistente_conectado: bool
    trabajadores_activos: int


class RespuestaAsistenteSalida(Esquema):
    texto: str
    expedientes_citados: list[str]


class ConsultaAsistente(Esquema):
    pregunta: str = Field(min_length=3, max_length=2000)
    expediente_ids: list[str] = Field(default_factory=list, max_length=20)


class SolicitudVerificacion(Esquema):
    texto: str = Field(min_length=1, max_length=20_000)
    expediente_ids: list[str] = Field(min_length=1, max_length=50)
    tolerancia_relativa: float = Field(0.005, ge=0, le=0.1)


class CifraDetectada(Esquema):
    texto: str
    valor: float
    trazable: bool
    coincide_con: float | None


class ResultadoVerificacionTexto(Esquema):
    aprobado: bool
    cifras: list[CifraDetectada]
    no_trazables: list[str]
    valores_permitidos: int
