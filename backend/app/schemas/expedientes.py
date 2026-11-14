"""Expedientes: resultados científicos inmutables, con sus reglas de publicación.

Cada tipo de resultado tiene un esquema propio (unión discriminada por ``tipo``). Las reglas
de publicación del proyecto están codificadas aquí, de modo que la API **rechaza** cualquier
resultado que las viole (por ejemplo, una tendencia "robusta" con pruebas pendientes o un
pronóstico publicable sin habilidad frente a la climatología).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Any, Literal

from pydantic import Field, StringConstraints, model_validator

from app.domain.vocabulario import EstadoExpediente, EstadoPrueba, TipoExpediente, Veredicto
from app.schemas.comun import Esquema, Metricas, NumeroFinito
from app.schemas.procedencia import Procedencia

FechaParcial = Annotated[str, StringConstraints(pattern=r"^\d{4}(-\d{2}(-\d{2})?)?$")]
Probabilidad = Annotated[float, Field(ge=0, le=1)]


class Periodo(Esquema):
    desde: FechaParcial
    hasta: FechaParcial

    @model_validator(mode="after")
    def _ordenado(self) -> Periodo:
        if self.desde > self.hasta:
            raise ValueError("'desde' debe ser anterior o igual a 'hasta'.")
        return self


class Intervalo(Esquema):
    lo: NumeroFinito
    hi: NumeroFinito
    nivel: float = Field(0.9, gt=0, lt=1)

    @model_validator(mode="after")
    def _ordenado(self) -> Intervalo:
        if self.lo > self.hi:
            raise ValueError("El límite inferior supera al superior.")
        return self


class Pendiente(Esquema):
    valor: NumeroFinito
    intervalo: Intervalo
    unidad: str = Field(examples=["Cel/decada", "mm/decada"])
    metodo: Literal["theil_sen"] = "theil_sen"


class Significancia(Esquema):
    p_mann_kendall: Probabilidad
    p_hamed_rao: Probabilidad | None = None
    p_conservador: Probabilidad = Field(description="El mayor p de las variantes calculadas.")
    alfa: float = Field(0.05, gt=0, lt=1)

    @model_validator(mode="after")
    def _conservador(self) -> Significancia:
        candidatos = [self.p_mann_kendall] + ([self.p_hamed_rao] if self.p_hamed_rao is not None else [])
        if self.p_conservador + 1e-12 < max(candidatos):
            raise ValueError("p_conservador debe ser el mayor p de las variantes (regla conservadora).")
        return self


class Prueba(Esquema):
    estado: EstadoPrueba
    metricas: Metricas = Field(default_factory=dict)
    nota: str | None = Field(None, max_length=500)


class Sello(Esquema):
    """Las cinco pruebas del Sello de Confianza."""

    ventanas: Prueba
    enso: Prueba
    sensor: Prueba
    independencia: Prueba
    detectabilidad: Prueba

    def pruebas(self) -> dict[str, Prueba]:
        return {
            "ventanas": self.ventanas,
            "enso": self.enso,
            "sensor": self.sensor,
            "independencia": self.independencia,
            "detectabilidad": self.detectabilidad,
        }


class ResultadoTendencia(Esquema):
    tipo: Literal["tendencia"]
    periodo: Periodo
    n: int = Field(ge=3)
    pendiente: Pendiente
    significancia: Significancia
    sello: Sello
    veredicto: Veredicto
    anios_para_decidir: float | None = Field(None, ge=0)

    @model_validator(mode="after")
    def _reglas_de_veredicto(self) -> ResultadoTendencia:
        pruebas = self.sello.pruebas()
        significativa = self.significancia.p_conservador <= self.significancia.alfa
        if self.veredicto == Veredicto.robusta:
            no_aprobadas = [k for k, p in pruebas.items() if p.estado != EstadoPrueba.aprobada]
            if no_aprobadas:
                raise ValueError(
                    f"Una tendencia 'robusta' exige las cinco pruebas aprobadas; faltan: {no_aprobadas}"
                )
        if self.veredicto in (Veredicto.robusta, Veredicto.fragil) and not significativa:
            raise ValueError("'robusta' y 'fragil' exigen p_conservador ≤ alfa.")
        if self.veredicto == Veredicto.fragil and not any(
            p.estado == EstadoPrueba.fallida for p in pruebas.values()
        ):
            raise ValueError("'fragil' exige al menos una prueba fallida (indique cuál).")
        if self.veredicto in (Veredicto.sin_tendencia, Veredicto.no_decidible) and significativa:
            raise ValueError("'sin_tendencia' y 'no_decidible' exigen p_conservador > alfa.")
        return self


class Habilidad(Esquema):
    metrica: str = Field(examples=["AUC-PR", "KGE", "CRPSS"])
    valor: NumeroFinito
    intervalo: Intervalo
    linea_base: str
    supera_linea_base: bool


class VariableRelevancia(Esquema):
    variable_id: str
    importancia: Probabilidad = Field(description="Importancia normalizada en [0, 1].")
    estabilidad: Probabilidad = Field(description="Frecuencia en el top-k entre remuestreos.")
    p_ajustado: Probabilidad | None = Field(None, description="p ajustado por FDR frente al nulo barajado.")
    direccion: Literal["positiva", "negativa", "no_monotona", "indeterminada"]


class ResultadoRelevancia(Esquema):
    tipo: Literal["relevancia"]
    problema_id: str
    version_modelo: str
    particion_prueba: str = Field(description="Descripción de los datos apartados para la prueba final.")
    habilidad: Habilidad
    variables: list[VariableRelevancia] = Field(min_length=1)
    publicable: bool

    @model_validator(mode="after")
    def _regla_publicacion(self) -> ResultadoRelevancia:
        if self.publicable and not (self.habilidad.supera_linea_base and self.habilidad.intervalo.lo > 0):
            raise ValueError("Solo es publicable si supera la línea base con el intervalo por encima de 0.")
        ids = [v.variable_id for v in self.variables]
        if len(ids) != len(set(ids)):
            raise ValueError("Variables repetidas en la matriz.")
        return self


class Cuantiles(Esquema):
    p05: NumeroFinito
    p50: NumeroFinito
    p95: NumeroFinito

    @model_validator(mode="after")
    def _ordenados(self) -> Cuantiles:
        if not self.p05 <= self.p50 <= self.p95:
            raise ValueError("Se exige p05 ≤ p50 ≤ p95.")
        return self


class CalidadGemelo(Esquema):
    kge_calibracion: NumeroFinito
    kge_validacion: NumeroFinito
    umbral_kge: NumeroFinito
    parametros_aceptables: int = Field(ge=1)


class ResultadoAtribucion(Esquema):
    tipo: Literal["atribucion"]
    periodo: Periodo
    delta_total: Cuantiles
    unidad_delta: str
    fraccion_temperatura: Cuantiles
    fraccion_lluvia: Cuantiles
    fraccion_residuo: Cuantiles
    calidad_gemelo: CalidadGemelo
    veredicto: Veredicto

    @model_validator(mode="after")
    def _gemelo_validado(self) -> ResultadoAtribucion:
        if self.calidad_gemelo.kge_validacion < self.calidad_gemelo.umbral_kge:
            raise ValueError("Un gemelo que no supera su KGE de validación no puede alimentar la atribución.")
        return self


class ValorConUnidad(Esquema):
    valor: NumeroFinito
    unidad: str


class CuantilesPronostico(Esquema):
    p10: NumeroFinito
    p50: NumeroFinito
    p90: NumeroFinito
    unidad: str

    @model_validator(mode="after")
    def _ordenados(self) -> CuantilesPronostico:
        if not self.p10 <= self.p50 <= self.p90:
            raise ValueError("Se exige p10 ≤ p50 ≤ p90.")
        return self


class HabilidadPronostico(Esquema):
    crpss: NumeroFinito
    intervalo: Intervalo
    anios_evaluados: int = Field(ge=1)


class ResultadoPronostico(Esquema):
    tipo: Literal["pronostico"]
    emitido_utc: datetime
    fin_horizonte: date
    variable_objetivo: str
    umbral: ValorConUnidad
    cuantiles: CuantilesPronostico
    prob_bajo_umbral: Probabilidad
    habilidad: HabilidadPronostico
    publicable: bool

    @model_validator(mode="after")
    def _regla_habilidad(self) -> ResultadoPronostico:
        if self.publicable and self.habilidad.intervalo.lo <= 0:
            raise ValueError("Un pronóstico solo es publicable si el CRPSS es > 0 con su intervalo (ADR-6).")
        return self


class ResultadoAlerta(Esquema):
    tipo: Literal["alerta"]
    nivel: Literal["sin_riesgo", "bajo", "medio", "alto"]
    valido_desde: datetime
    valido_hasta: datetime
    disparadores: dict[str, NumeroFinito] = Field(default_factory=dict)
    eventos_calibracion: int = Field(ge=0)
    prototipo: bool = True

    @model_validator(mode="after")
    def _ventana(self) -> ResultadoAlerta:
        if self.valido_hasta <= self.valido_desde:
            raise ValueError("'valido_hasta' debe ser posterior a 'valido_desde'.")
        return self


class ResultadoColmatacion(Esquema):
    tipo: Literal["colmatacion"]
    periodo: Periodo
    serie_area_id: str
    pendiente: Pendiente
    significancia: Significancia
    veredicto: Veredicto
    coherencia_swot: dict[str, float | None] = Field(default_factory=dict)


class Monto(Esquema):
    valor: NumeroFinito = Field(ge=0)
    moneda: Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]


class Seleccion(Esquema):
    unidad_id: str
    area_ha: NumeroFinito = Field(gt=0)
    beneficio: NumeroFinito = Field(ge=0)
    costo: NumeroFinito = Field(ge=0)


class ResultadoPriorizacion(Esquema):
    tipo: Literal["priorizacion"]
    presupuesto: Monto
    costo_por_ha: Monto
    seleccion: list[Seleccion]
    beneficio_total: NumeroFinito = Field(ge=0)

    @model_validator(mode="after")
    def _dentro_de_presupuesto(self) -> ResultadoPriorizacion:
        if sum(s.costo for s in self.seleccion) > self.presupuesto.valor * (1 + 1e-9):
            raise ValueError("La selección supera el presupuesto.")
        if abs(sum(s.beneficio for s in self.seleccion) - self.beneficio_total) > 1e-6 * max(
            1.0, self.beneficio_total
        ):
            raise ValueError("beneficio_total no coincide con la suma de la selección.")
        return self


Resultado = Annotated[
    ResultadoTendencia
    | ResultadoRelevancia
    | ResultadoAtribucion
    | ResultadoPronostico
    | ResultadoAlerta
    | ResultadoColmatacion
    | ResultadoPriorizacion,
    Field(discriminator="tipo"),
]


class ExpedienteCrear(Esquema):
    estado: Literal["preliminar", "validado"] = "preliminar"
    dominio_id: str
    unidad_id: str | None = None
    variable_id: str | None = None
    serie_id: str | None = None
    titulo: str = Field(min_length=5, max_length=200)
    resumen: str = Field(min_length=10, max_length=2000)
    resultado: Resultado
    procedencia: Procedencia
    reemplaza_a: str | None = None
    schema_version: Literal["1.0"] = "1.0"


class ExpedienteResumen(Esquema):
    id: str
    tipo: TipoExpediente
    modulo: str
    estado: EstadoExpediente
    dominio_id: str
    unidad_id: str | None
    variable_id: str | None
    serie_id: str | None
    titulo: str
    resumen: str
    veredicto: Veredicto | None = None
    creado_en: datetime


class ExpedienteSalida(ExpedienteResumen):
    resultado: Resultado
    procedencia: Procedencia
    hash_contenido: str
    reemplaza_a: str | None
    creado_por: str | None
    schema_version: str
    motivo_retiro: str | None = None
    retirado_en: datetime | None = None


class ExpedienteRetirar(Esquema):
    motivo: str = Field(min_length=10, max_length=500)


def extraer_veredicto(resultado: dict[str, Any]) -> str | None:
    valor = resultado.get("veredicto")
    return valor if isinstance(valor, str) else None
