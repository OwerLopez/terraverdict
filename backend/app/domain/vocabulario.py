"""Vocabulario controlado del dominio: roles, estados, tipos y reglas de transición.

Estos valores forman parte del contrato público de la API: cambiarlos es un cambio
incompatible y requiere una nueva versión del esquema.
"""

from __future__ import annotations

from enum import StrEnum


class Rol(StrEnum):
    lector = "lector"
    analista = "analista"
    admin = "admin"


RANGO_ROL: dict[Rol, int] = {Rol.lector: 1, Rol.analista: 2, Rol.admin: 3}


class Alcance(StrEnum):
    """Permisos de las cuentas de servicio (claves API) del equipo de ciencia de datos."""

    ingesta = "ingesta"  # publicar fuentes, series, expedientes y ejecuciones
    trabajador = "trabajador"  # reclamar y actualizar procesos


class TipoExpediente(StrEnum):
    tendencia = "tendencia"
    relevancia = "relevancia"
    atribucion = "atribucion"
    pronostico = "pronostico"
    alerta = "alerta"
    colmatacion = "colmatacion"
    priorizacion = "priorizacion"
    caos = "caos"  # diagnóstico de dinámica (caos, no linealidad o ruido)
    comparacion_modelos = "comparacion_modelos"  # zoológico de modelos con referencias, IC y abstención
    recurrencia = "recurrencia"  # frecuencia histórica de erupciones (no es pronóstico)
    sismicidad = "sismicidad"  # completitud, valor b y tasas (no es pronóstico)
    inventario = "inventario"  # eventos georreferenciados (p. ej., deslizamientos) y su lluvia antecedente


ABREVIATURA_EXPEDIENTE: dict[TipoExpediente, str] = {
    TipoExpediente.tendencia: "TEN",
    TipoExpediente.relevancia: "REL",
    TipoExpediente.atribucion: "ATR",
    TipoExpediente.pronostico: "PRO",
    TipoExpediente.alerta: "ALE",
    TipoExpediente.colmatacion: "COL",
    TipoExpediente.priorizacion: "PRI",
    TipoExpediente.caos: "CAO",
    TipoExpediente.comparacion_modelos: "CMP",
    TipoExpediente.recurrencia: "REC",
    TipoExpediente.sismicidad: "SIS",
    TipoExpediente.inventario: "INV",
}

MODULO_POR_TIPO: dict[TipoExpediente, str] = {
    TipoExpediente.relevancia: "M1",
    TipoExpediente.tendencia: "M2",
    TipoExpediente.atribucion: "M3",
    TipoExpediente.pronostico: "M4",
    TipoExpediente.alerta: "M4",
    TipoExpediente.colmatacion: "M5",
    TipoExpediente.priorizacion: "M5",
    TipoExpediente.caos: "M6",
    TipoExpediente.comparacion_modelos: "M6",
    TipoExpediente.recurrencia: "M6",
    TipoExpediente.sismicidad: "M6",
    TipoExpediente.inventario: "M6",
}
"""M6: fenómenos naturales (lluvia extrema, sequía, sismos, volcanes, deslizamientos y dinámica)."""


class EstadoExpediente(StrEnum):
    preliminar = "preliminar"  # calculado, sin todas las validaciones del sello
    validado = "validado"  # pasó las validaciones preregistradas
    retirado = "retirado"  # reemplazado o invalidado; se conserva por trazabilidad


class Veredicto(StrEnum):
    robusta = "robusta"
    fragil = "fragil"
    no_decidible = "no_decidible"
    sin_tendencia = "sin_tendencia"
    preliminar = "preliminar"


class EstadoPrueba(StrEnum):
    aprobada = "aprobada"
    fallida = "fallida"
    calculada = "calculada"  # métricas calculadas, sin umbral preregistrado todavía
    pendiente = "pendiente"
    no_aplica = "no_aplica"


class EstadoProceso(StrEnum):
    pendiente = "pendiente"
    en_curso = "en_curso"
    completado = "completado"
    fallido = "fallido"
    cancelado = "cancelado"


TRANSICIONES_PROCESO: dict[EstadoProceso, frozenset[EstadoProceso]] = {
    EstadoProceso.pendiente: frozenset({EstadoProceso.en_curso, EstadoProceso.cancelado}),
    EstadoProceso.en_curso: frozenset(
        {EstadoProceso.completado, EstadoProceso.fallido, EstadoProceso.cancelado}
    ),
    EstadoProceso.completado: frozenset(),
    EstadoProceso.fallido: frozenset(),
    EstadoProceso.cancelado: frozenset(),
}


class TipoProceso(StrEnum):
    ingesta = "ingesta"
    tendencia = "tendencia"
    relevancia = "relevancia"
    atribucion = "atribucion"
    pronostico = "pronostico"
    alerta = "alerta"
    colmatacion = "colmatacion"
    priorizacion = "priorizacion"


PARAMETROS_REQUERIDOS: dict[TipoProceso, frozenset[str]] = {
    TipoProceso.ingesta: frozenset({"fuente_id"}),
    TipoProceso.tendencia: frozenset({"serie_id"}),
    TipoProceso.relevancia: frozenset({"problema_id"}),
    TipoProceso.atribucion: frozenset({"unidad_id"}),
    TipoProceso.pronostico: frozenset({"unidad_id"}),
    TipoProceso.alerta: frozenset({"unidad_id"}),
    TipoProceso.colmatacion: frozenset({"unidad_id"}),
    TipoProceso.priorizacion: frozenset({"dominio_id", "presupuesto"}),
}


class NivelEvento(StrEnum):
    debug = "debug"
    info = "info"
    aviso = "aviso"
    error = "error"


class Frecuencia(StrEnum):
    """Duraciones ISO 8601 admitidas para las series."""

    min30 = "PT30M"
    h3 = "PT3H"
    dia = "P1D"
    d8 = "P8D"
    d16 = "P16D"
    mes = "P1M"
    anio = "P1Y"


class TipoUnidad(StrEnum):
    sistema = "sistema"
    subcuenca = "subcuenca"
    represa = "represa"
    captacion = "captacion"
    bofedal = "bofedal"
    punto = "punto"
    estacion = "estacion"
    celda = "celda"


class EstadoGeometria(StrEnum):
    pendiente = "pendiente"  # aún no delimitada (etapa E1 del pipeline)
    aproximada = "aproximada"
    exacta = "exacta"  # coordenadas exactas de un punto de medición o análisis
    oficial = "oficial"  # polígono de una fuente oficial (p. ej., ANA)


class EstadoVerificacion(StrEnum):
    verificado = "verificado"
    parcial = "parcial"  # verificado, con aspectos marcados por confirmar
    no_verificado = "no_verificado"  # la verificación falló
    sin_evidencia = "sin_evidencia"


class CategoriaEvento(StrEnum):
    escasez = "escasez"
    turbidez = "turbidez"
    colmatacion = "colmatacion"
    almacenamiento = "almacenamiento"
    degradacion = "degradacion"
    clima = "clima"
    institucional = "institucional"


class PrecisionFecha(StrEnum):
    dia = "dia"
    mes = "mes"
    anio = "anio"


class CotaCifra(StrEnum):
    """Cómo debe leerse una cifra citada: la fuente puede dar un valor exacto o solo una cota."""

    exacta = "exacta"
    minima = "minima"  # "más del 70 %"
    maxima = "maxima"  # "menos de 5 hm³"
    aproximada = "aproximada"  # "cerca de 22 hm³"
