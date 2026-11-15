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
from app.schemas.comun import Esquema, Metricas, NumeroFinito, NumeroFinitoOpcional
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
    intervalo_conformal: Intervalo | None = Field(
        None, description="Intervalo de predicción conformal (cobertura medida en prueba)."
    )
    cobertura_conformal_prueba: Probabilidad | None = None
    abstencion: Abstencion | None = None

    @model_validator(mode="after")
    def _regla_habilidad(self) -> ResultadoPronostico:
        if self.publicable and self.habilidad.intervalo.lo <= 0:
            raise ValueError("Un pronóstico solo es publicable si el CRPSS es > 0 con su intervalo (ADR-6).")
        if self.publicable and self.abstencion is not None and not self.abstencion.publicar:
            raise ValueError("Un pronóstico con abstención no puede ser publicable.")
        if self.intervalo_conformal is not None and not (
            self.intervalo_conformal.lo <= self.cuantiles.p50 <= self.intervalo_conformal.hi
        ):
            raise ValueError("El intervalo conformal debe contener la mediana pronosticada.")
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


class Abstencion(Esquema):
    """Decisión explícita de publicar o abstenerse, con sus motivos (nunca una abstención muda)."""

    publicar: bool
    motivos: list[Annotated[str, StringConstraints(max_length=500)]] = Field(default_factory=list)
    advertencias: list[Annotated[str, StringConstraints(max_length=500)]] = Field(default_factory=list)

    @model_validator(mode="after")
    def _motivada(self) -> Abstencion:
        if not self.publicar and not self.motivos:
            raise ValueError("Una abstención exige al menos un motivo.")
        if self.publicar and self.motivos:
            raise ValueError("Si hay motivos de abstención, 'publicar' debe ser false.")
        return self


VeredictoDinamica = Literal[
    "lineal_estocastica",
    "no_lineal_sin_caos_demostrado",
    "compatible_con_caos_baja_dimension",
    "regular",
    "insuficiente",
]
CONDICIONES_CAOS = (
    "no_linealidad_significativa",
    "determinismo_prediccion_analogos",
    "d2_satura_bajo",
    "lyapunov_positivo",
    "prueba_01_caotica",
)


class DistribucionSustitutos(Esquema):
    """Estadístico de la serie frente a sus sustitutos IAAFT (para el histograma de la vista Caos)."""

    estadistico: str
    original: NumeroFinito
    sustitutos: list[NumeroFinito] = Field(max_length=500)
    p: Probabilidad


class SerieDinamica(Esquema):
    serie_id: Annotated[str, StringConstraints(pattern=r"^[a-z0-9_]{2,80}$")]
    fuente: str
    n: int = Field(ge=0)
    unidad_tiempo: str
    veredicto: VeredictoDinamica
    condiciones: dict[str, bool] = Field(default_factory=dict)
    tau: int | None = Field(None, ge=1)
    m: int | None = Field(None, ge=1)
    d2: NumeroFinitoOpcional = Field(None, description="D2 saturado; null si no satura.")
    lyapunov: NumeroFinitoOpcional = None
    k_01: NumeroFinitoOpcional = None
    determinismo_rqa: NumeroFinitoOpcional = None
    espacio_fases: list[tuple[NumeroFinito, NumeroFinito]] = Field(
        default_factory=list, max_length=3000, description="Pares (x(t), x(t+τ)) para el gráfico."
    )
    sustitutos: list[DistribucionSustitutos] = Field(default_factory=list)
    recurrencia_miniatura: list[list[Probabilidad]] = Field(
        default_factory=list,
        max_length=200,
        description="Densidad de recurrencias por bloque (gráfico de recurrencia).",
    )

    @model_validator(mode="after")
    def _regla_caos(self) -> SerieDinamica:
        if self.veredicto == "compatible_con_caos_baja_dimension":
            faltan = [c for c in CONDICIONES_CAOS if not self.condiciones.get(c)]
            if faltan:
                raise ValueError(
                    f"'compatible_con_caos_baja_dimension' exige todas las condiciones; faltan: {faltan}"
                )
            if self.d2 is None or self.d2 >= 5 or (self.lyapunov or 0) <= 0 or (self.k_01 or 0) <= 0.8:
                raise ValueError("Caos de baja dimensión exige D2 < 5, λ > 0 y K > 0,8.")
        return self


class ResultadoCaos(Esquema):
    tipo: Literal["caos"]
    series: list[SerieDinamica] = Field(min_length=1)
    alfa: float = Field(0.05, gt=0, lt=1)
    metodo: str = Field(max_length=1000)

    @model_validator(mode="after")
    def _series_unicas(self) -> ResultadoCaos:
        ids = [s.serie_id for s in self.series]
        if len(ids) != len(set(ids)):
            raise ValueError("Series repetidas en el diagnóstico.")
        return self


FamiliaModelo = Literal["referencia", "clasico", "red_neuronal", "ensamble"]


class ModeloEvaluado(Esquema):
    nombre: Annotated[str, StringConstraints(pattern=r"^[a-z0-9_]{2,40}$")]
    familia: FamiliaModelo
    puntaje_validacion: NumeroFinito
    puntaje_prueba: NumeroFinitoOpcional = None
    intervalo_prueba: Intervalo | None = None
    p_diebold_mariano: Probabilidad | None = Field(None, description="Frente a la climatología, en prueba.")
    dispersion_semillas: NumeroFinitoOpcional = None
    referencia: str | None = Field(None, max_length=300, description="Artículo de la arquitectura.")


class Ablacion(Esquema):
    nombre: str = Field(max_length=80)
    variables: list[str]
    mejor_validacion: NumeroFinito
    mejor_prueba: NumeroFinitoOpcional = None


class PuntoConfiabilidad(Esquema):
    pronosticada: Probabilidad
    observada: Probabilidad
    n: int = Field(ge=1)


class ImportanciaVariable(Esquema):
    variable: str
    importancia: NumeroFinito
    desviacion: NumeroFinito = Field(ge=0)


class ResultadoComparacionModelos(Esquema):
    """Zoológico de modelos: el elegido es SIEMPRE el mejor en validación; la prueba solo informa."""

    tipo: Literal["comparacion_modelos"]
    fenomeno: str
    tarea: Literal["clasificacion", "regresion", "conteo"]
    objetivo: str = Field(max_length=300)
    horizonte: str = Field(max_length=40, examples=["1 día", "3 meses"])
    metrica_principal: str
    periodo_prueba: Periodo
    modelos: list[ModeloEvaluado] = Field(min_length=2)
    mejor_validacion: str
    variables_seleccionadas: list[str] = Field(default_factory=list)
    ventana: int | None = Field(None, ge=1)
    ablaciones: list[Ablacion] = Field(default_factory=list)
    confiabilidad: list[PuntoConfiabilidad] = Field(default_factory=list)
    ece: NumeroFinitoOpcional = None
    cobertura_conformal_90: Probabilidad | None = None
    importancia: list[ImportanciaVariable] = Field(default_factory=list)
    abstencion: Abstencion

    @model_validator(mode="after")
    def _reglas(self) -> ResultadoComparacionModelos:
        nombres = [m.nombre for m in self.modelos]
        if len(nombres) != len(set(nombres)):
            raise ValueError("Modelos repetidos.")
        if not any(m.familia == "referencia" for m in self.modelos):
            raise ValueError("Toda comparación exige al menos una referencia (climatología o persistencia).")
        candidatos = {m.nombre: m for m in self.modelos if m.familia != "referencia"}
        if self.mejor_validacion not in candidatos:
            raise ValueError("'mejor_validacion' debe ser un modelo evaluado que no sea una referencia.")
        maximo = max(m.puntaje_validacion for m in candidatos.values())
        if candidatos[self.mejor_validacion].puntaje_validacion < maximo - 1e-9:
            raise ValueError("El modelo elegido debe ser el mejor en validación: la prueba no elige modelos.")
        if self.abstencion.publicar and candidatos[self.mejor_validacion].puntaje_validacion <= 0:
            raise ValueError("Solo se publica si el modelo elegido supera a la referencia en validación.")
        return self


class VolcanRecurrencia(Esquema):
    numero_gvp: int
    nombre: str
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    distancia_km: NumeroFinito = Field(ge=0)
    erupciones: int = Field(ge=0, description="Inicios de erupción confirmados desde el inicio del registro.")
    probabilidad_anual: Probabilidad
    intervalo: Intervalo
    intervalo_medio_anios: NumeroFinitoOpcional = None
    iev_maximo: int | None = Field(None, ge=0, le=8)
    ultima_erupcion: int | None = None
    inicios: list[int] = Field(
        default_factory=list, description="Año de inicio de cada erupción contada (historia eruptiva)."
    )

    @model_validator(mode="after")
    def _dentro_del_intervalo(self) -> VolcanRecurrencia:
        if not self.intervalo.lo - 1e-12 <= self.probabilidad_anual <= self.intervalo.hi + 1e-12:
            raise ValueError("La probabilidad anual debe estar dentro de su intervalo.")
        if self.inicios and len(self.inicios) != self.erupciones:
            raise ValueError("'inicios' debe tener un año por cada erupción contada.")
        return self


class ResultadoRecurrencia(Esquema):
    tipo: Literal["recurrencia"]
    fuente: str
    inicio_registro: int
    metodo: str = Field(max_length=500)
    volcanes: list[VolcanRecurrencia] = Field(min_length=1)
    es_pronostico: Literal[False] = False
    abstencion: Abstencion


class EventoSismico(Esquema):
    fecha: FechaParcial
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    magnitud: NumeroFinito
    profundidad_km: NumeroFinitoOpcional = None


class ResultadoSismicidad(Esquema):
    tipo: Literal["sismicidad"]
    fuente: str
    periodo: Periodo
    radio_km: NumeroFinito = Field(gt=0)
    eventos: int = Field(ge=0)
    mc: NumeroFinito
    valor_b: NumeroFinito = Field(gt=0)
    intervalo_b: Intervalo
    independientes: int = Field(ge=0)
    cv_intereventos: NumeroFinitoOpcional = None
    tasa_anual_mc: NumeroFinito = Field(ge=0)
    conteos_anuales: dict[str, int] = Field(default_factory=dict)
    mapa: list[EventoSismico] = Field(default_factory=list, max_length=5000)
    es_pronostico: Literal[False] = False

    @model_validator(mode="after")
    def _b_en_intervalo(self) -> ResultadoSismicidad:
        if not self.intervalo_b.lo <= self.valor_b <= self.intervalo_b.hi:
            raise ValueError("El valor b debe estar dentro de su intervalo.")
        return self


class EventoInventario(Esquema):
    id: str
    fecha: FechaParcial
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    lugar: str | None = None
    categoria: str | None = None
    detonante: str | None = None
    lluvia_mm: dict[str, NumeroFinitoOpcional] = Field(
        default_factory=dict, description="Acumulados (1d, 3d…)."
    )
    percentiles: dict[str, NumeroFinitoOpcional] = Field(default_factory=dict)


class ResultadoInventario(Esquema):
    tipo: Literal["inventario"]
    fenomeno: str
    fuente: str
    eventos: list[EventoInventario]
    eventos_minimos_umbral: int = Field(ge=1)
    umbral_estimado: bool
    abstencion: Abstencion

    @model_validator(mode="after")
    def _umbral_con_datos(self) -> ResultadoInventario:
        if self.umbral_estimado and len(self.eventos) < self.eventos_minimos_umbral:
            raise ValueError("No se estima un umbral con menos eventos que el mínimo preregistrado.")
        return self


Resultado = Annotated[
    ResultadoTendencia
    | ResultadoRelevancia
    | ResultadoAtribucion
    | ResultadoPronostico
    | ResultadoAlerta
    | ResultadoColmatacion
    | ResultadoPriorizacion
    | ResultadoCaos
    | ResultadoComparacionModelos
    | ResultadoRecurrencia
    | ResultadoSismicidad
    | ResultadoInventario,
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
