"""Línea de comandos de administración: ``python -m app.cli <comando>``."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session

from app.core.config import obtener_settings
from app.db.session import crear_fabrica_sesiones, crear_motor
from app.domain.vocabulario import Alcance
from app.importacion import importar_todo
from app.schemas.auth import ClaveCrear
from app.services import usuarios

RAIZ_BACKEND = Path(__file__).resolve().parents[1]


def _sesion() -> Session:
    settings = obtener_settings()
    return crear_fabrica_sesiones(crear_motor(settings.database_url))()


def migrar(_: argparse.Namespace) -> None:
    config = Config(str(RAIZ_BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(RAIZ_BACKEND / "alembic"))
    command.upgrade(config, "head")
    print("Migraciones aplicadas.")


def importar(_: argparse.Namespace) -> None:
    with _sesion() as sesion:
        cfg = obtener_settings()
        resumen = importar_todo(sesion, cfg.raiz_datos, incluir_ciencia=cfg.importar_resultados_ciencia)
    print(json.dumps(resumen, ensure_ascii=False, indent=2, default=str))


def crear_admin(args: argparse.Namespace) -> None:
    contrasena = os.environ.get("TV_ADMIN_PASSWORD") or getpass.getpass("Contraseña (mín. 12 caracteres): ")
    with _sesion() as sesion:
        creado = usuarios.asegurar_admin(sesion, args.email, contrasena, args.nombre)
    print("Administrador creado." if creado else "El administrador ya existía.")


def crear_clave(args: argparse.Namespace) -> None:
    with _sesion() as sesion:
        registro, clave = usuarios.crear_clave(
            sesion, ClaveCrear(nombre=args.nombre, alcances=[Alcance(a) for a in args.alcance]), None
        )
    print(f"Clave '{registro.nombre}' ({', '.join(registro.alcances)}). Se muestra una sola vez:\n{clave}")


def exportar_openapi(args: argparse.Namespace) -> None:
    from app.main import create_app

    especificacion = create_app().openapi()
    salida = Path(args.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(especificacion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OpenAPI escrito en {salida}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli", description="Administración de TerraVerdict")
    sub = parser.add_subparsers(dest="comando", required=True)
    sub.add_parser("migrar", help="Aplica las migraciones de Alembic").set_defaults(func=migrar)
    sub.add_parser("importar", help="Importa los datos reales del repositorio").set_defaults(func=importar)
    p = sub.add_parser("crear-admin", help="Crea el usuario administrador inicial")
    p.add_argument("--email", required=True)
    p.add_argument("--nombre", default="Administración")
    p.set_defaults(func=crear_admin)
    p = sub.add_parser("crear-clave", help="Crea una clave API de servicio")
    p.add_argument("--nombre", required=True)
    p.add_argument("--alcance", action="append", choices=[a.value for a in Alcance], required=True)
    p.set_defaults(func=crear_clave)
    p = sub.add_parser("exportar-openapi", help="Escribe la especificación OpenAPI en un archivo")
    p.add_argument("--salida", default=str(RAIZ_BACKEND.parent / "docs" / "api" / "openapi.json"))
    p.set_defaults(func=exportar_openapi)
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main(sys.argv[1:])
