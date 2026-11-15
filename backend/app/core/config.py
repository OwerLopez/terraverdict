"""Configuración por variables de entorno (prefijo ``TV_``).

Todas las opciones están documentadas en ``.env.example`` y en ``docs/arquitectura.md``.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

RAIZ_REPO = Path(__file__).resolve().parents[3]
_SECRETO_DESARROLLO = "solo-para-desarrollo-cambiar-en-produccion"


class Settings(BaseSettings):
    """Parámetros de ejecución de la API."""

    model_config = SettingsConfigDict(
        env_prefix="TV_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    entorno: Literal["desarrollo", "pruebas", "produccion"] = "desarrollo"
    database_url: str = f"sqlite:///{RAIZ_REPO / 'backend' / 'terraverdict.db'}"
    jwt_secreto: SecretStr = SecretStr(_SECRETO_DESARROLLO)
    jwt_algoritmo: Literal["HS256", "HS384", "HS512"] = "HS256"
    jwt_minutos: int = Field(60, ge=5, le=1440)
    cors_origenes: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    login_intentos_por_minuto: int = Field(10, ge=1, le=1000)
    raiz_datos: Path = RAIZ_REPO
    importar_resultados_ciencia: bool = Field(
        True,
        description="Al importar, publicar resultados/contrato/expedientes.json (vistas M6/M7 listas al desplegar).",
    )
    log_nivel: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    anthropic_api_key: SecretStr | None = None

    @model_validator(mode="after")
    def _exigir_secretos_en_produccion(self) -> Settings:
        if self.entorno == "produccion":
            secreto = self.jwt_secreto.get_secret_value()
            if secreto == _SECRETO_DESARROLLO or len(secreto) < 32:
                raise ValueError("TV_JWT_SECRETO debe tener al menos 32 caracteres en producción.")
            if "*" in self.cors_origenes:
                raise ValueError("TV_CORS_ORIGENES no puede contener '*' en producción.")
        return self


@lru_cache
def obtener_settings() -> Settings:
    return Settings()
