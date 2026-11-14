"""Modelo de datos persistente.

Los campos JSON guardan estructuras validadas por los esquemas Pydantic de ``app.schemas``;
la base de datos nunca recibe datos que no hayan pasado por su contrato.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def ahora() -> datetime:
    return datetime.now(UTC)


def nuevo_id() -> str:
    return uuid4().hex


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=nuevo_id)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(120))
    hash_contrasena: Mapped[str] = mapped_column(String(255))
    rol: Mapped[str] = mapped_column(String(20))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)


class ClaveApi(Base):
    __tablename__ = "claves_api"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=nuevo_id)
    nombre: Mapped[str] = mapped_column(String(120))
    prefijo: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    hash_clave: Mapped[str] = mapped_column(String(64))
    alcances: Mapped[list[str]] = mapped_column(JSON, default=list)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_por: Mapped[str | None] = mapped_column(String(32))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)
    ultimo_uso: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Fuente(Base):
    __tablename__ = "fuentes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200))
    coleccion: Mapped[str | None] = mapped_column(String(200))
    version: Mapped[str | None] = mapped_column(String(40))
    acceso: Mapped[list[str]] = mapped_column(JSON, default=list)
    familia: Mapped[str | None] = mapped_column(String(64), index=True)
    url: Mapped[str | None] = mapped_column(Text)
    licencia: Mapped[str | None] = mapped_column(Text)
    periodo: Mapped[list[str | None] | None] = mapped_column(JSON)
    resolucion: Mapped[dict[str, str] | None] = mapped_column(JSON)
    usos: Mapped[list[str]] = mapped_column(JSON, default=list)
    advertencia: Mapped[str | None] = mapped_column(Text)
    por_confirmar: Mapped[str | None] = mapped_column(Text)
    metadatos: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    estado_verificacion: Mapped[str] = mapped_column(String(20), default="sin_evidencia")
    verificado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    evidencia: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class Variable(Base):
    __tablename__ = "variables"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200))
    simbolo: Mapped[str] = mapped_column(String(40))
    unidad: Mapped[str] = mapped_column(String(20))
    grupo: Mapped[str] = mapped_column(String(40), index=True)
    descripcion: Mapped[str] = mapped_column(Text)
    relacion: Mapped[str | None] = mapped_column(Text)


class Problema(Base):
    __tablename__ = "problemas"

    id: Mapped[str] = mapped_column(String(8), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200))
    objetivo: Mapped[str] = mapped_column(Text)
    candidatas: Mapped[list[str]] = mapped_column(JSON, default=list)
    muestras: Mapped[str] = mapped_column(String(120))
    viabilidad: Mapped[str] = mapped_column(String(20))
    dominio_entrenamiento: Mapped[str] = mapped_column(String(64))


class Dominio(Base):
    __tablename__ = "dominios"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200))
    descripcion: Mapped[str] = mapped_column(Text)
    tipo: Mapped[str] = mapped_column(String(20))
    bbox: Mapped[list[float]] = mapped_column(JSON)
    geometria: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    aproximado: Mapped[bool] = mapped_column(Boolean, default=True)
    metadatos: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    unidades: Mapped[list[Unidad]] = relationship(back_populates="dominio", order_by="Unidad.id")


class Unidad(Base):
    __tablename__ = "unidades"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    dominio_id: Mapped[str] = mapped_column(ForeignKey("dominios.id"), index=True)
    tipo: Mapped[str] = mapped_column(String(20))
    nombre: Mapped[str] = mapped_column(String(200))
    geometria: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    estado_geometria: Mapped[str] = mapped_column(String(20), default="pendiente")
    metadatos: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    dominio: Mapped[Dominio] = relationship(back_populates="unidades")


class Serie(Base):
    __tablename__ = "series"
    __table_args__ = (Index("ix_series_dominio_variable", "dominio_id", "variable_id"),)

    id: Mapped[str] = mapped_column(String(200), primary_key=True)
    dominio_id: Mapped[str] = mapped_column(ForeignKey("dominios.id"))
    unidad_id: Mapped[str | None] = mapped_column(ForeignKey("unidades.id"), index=True)
    variable_id: Mapped[str] = mapped_column(ForeignKey("variables.id"))
    fuente_id: Mapped[str] = mapped_column(ForeignKey("fuentes.id"), index=True)
    unidad: Mapped[str] = mapped_column(String(20))
    frecuencia: Mapped[str] = mapped_column(String(10))
    agregacion: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    descripcion: Mapped[str] = mapped_column(Text)
    procedencia: Mapped[dict[str, Any]] = mapped_column(JSON)
    version: Mapped[int] = mapped_column(Integer, default=1)
    t_inicio: Mapped[date | None] = mapped_column(Date)
    t_fin: Mapped[date | None] = mapped_column(Date)
    n_observaciones: Mapped[int] = mapped_column(Integer, default=0)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)
    actualizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)


class Observacion(Base):
    __tablename__ = "observaciones"

    serie_id: Mapped[str] = mapped_column(ForeignKey("series.id", ondelete="CASCADE"), primary_key=True)
    t: Mapped[date] = mapped_column(Date, primary_key=True)
    valor: Mapped[float | None] = mapped_column(Float)
    frac_valida: Mapped[float | None] = mapped_column(Float)
    calidad: Mapped[str | None] = mapped_column(String(20))


class Expediente(Base):
    __tablename__ = "expedientes"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    tipo: Mapped[str] = mapped_column(String(20), index=True)
    modulo: Mapped[str] = mapped_column(String(4))
    estado: Mapped[str] = mapped_column(String(20), index=True)
    dominio_id: Mapped[str] = mapped_column(ForeignKey("dominios.id"), index=True)
    unidad_id: Mapped[str | None] = mapped_column(ForeignKey("unidades.id"))
    variable_id: Mapped[str | None] = mapped_column(ForeignKey("variables.id"))
    serie_id: Mapped[str | None] = mapped_column(ForeignKey("series.id"))
    titulo: Mapped[str] = mapped_column(String(200))
    resumen: Mapped[str] = mapped_column(Text)
    resultado: Mapped[dict[str, Any]] = mapped_column(JSON)
    procedencia: Mapped[dict[str, Any]] = mapped_column(JSON)
    schema_version: Mapped[str] = mapped_column(String(10))
    hash_contenido: Mapped[str] = mapped_column(String(64), unique=True)
    reemplaza_a: Mapped[str | None] = mapped_column(String(40))
    creado_por: Mapped[str | None] = mapped_column(String(64))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora, index=True)
    motivo_retiro: Mapped[str | None] = mapped_column(Text)
    retirado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Proceso(Base):
    __tablename__ = "procesos"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=nuevo_id)
    tipo: Mapped[str] = mapped_column(String(20), index=True)
    parametros: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    estado: Mapped[str] = mapped_column(String(20), index=True, default="pendiente")
    prioridad: Mapped[int] = mapped_column(Integer, default=0)
    solicitado_por: Mapped[str] = mapped_column(String(64))
    trabajador: Mapped[str | None] = mapped_column(String(64))
    reclamado_por: Mapped[str | None] = mapped_column(String(32))
    progreso: Mapped[float | None] = mapped_column(Float)
    expediente_id: Mapped[str | None] = mapped_column(ForeignKey("expedientes.id"))
    error: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)
    iniciado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finalizado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ultimo_latido: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    eventos: Mapped[list[EventoProceso]] = relationship(
        back_populates="proceso", order_by="EventoProceso.id", cascade="all, delete-orphan"
    )


class EventoProceso(Base):
    __tablename__ = "eventos_proceso"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    proceso_id: Mapped[str] = mapped_column(ForeignKey("procesos.id", ondelete="CASCADE"), index=True)
    t: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)
    nivel: Mapped[str] = mapped_column(String(10))
    mensaje: Mapped[str] = mapped_column(Text)
    datos: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    proceso: Mapped[Proceso] = relationship(back_populates="eventos")


class Ejecucion(Base):
    __tablename__ = "ejecuciones"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    etapa: Mapped[str] = mapped_column(String(40), index=True)
    estado: Mapped[str] = mapped_column(String(20))
    iniciado: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finalizado: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    manifiesto: Mapped[dict[str, Any]] = mapped_column(JSON)
    registrado_por: Mapped[str] = mapped_column(String(64))
    registrado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)


class EventoDocumentado(Base):
    __tablename__ = "eventos_documentados"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    fecha: Mapped[date] = mapped_column(Date, index=True)
    precision: Mapped[str] = mapped_column(String(10))
    categoria: Mapped[str] = mapped_column(String(30), index=True)
    titulo: Mapped[str] = mapped_column(String(200))
    descripcion: Mapped[str] = mapped_column(Text)
    cifras: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    fuentes: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    dominio_id: Mapped[str | None] = mapped_column(ForeignKey("dominios.id"))


class InformeVerificacion(Base):
    __tablename__ = "informes_verificacion"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=nuevo_id)
    tipo: Mapped[str] = mapped_column(String(20), index=True)
    generado_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    total: Mapped[int] = mapped_column(Integer)
    correctas: Mapped[int] = mapped_column(Integer)
    datos: Mapped[dict[str, Any]] = mapped_column(JSON)
    importado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)
