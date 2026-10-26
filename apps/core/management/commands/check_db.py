"""Diagnóstico de solo lectura para saber si la base coincide con la rama.

Este comando no crea, borra ni modifica nada. Sirve para detectar el caso más
frecuente al cambiar de rama: la base conserva tablas o columnas de otra
versión del proyecto, mientras Django ya no tiene esas migraciones y por eso
``migrate`` no las corrige.
"""

from __future__ import annotations

import sys

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.db.utils import OperationalError

from apps.calidad.models import CatalogoDefecto
from apps.dashboard.models import MetaEstacion
from apps.personal.models import Empleado, Estacion, Linea, SkillMatrix

PROJECT_APPS = {"personal", "calidad", "dashboard"}
DEMO_MODELS = (
    ("Empleados", Empleado),
    ("Líneas", Linea),
    ("Estaciones", Estacion),
    ("Habilidades", SkillMatrix),
    ("Defectos", CatalogoDefecto),
    ("Metas", MetaEstacion),
)


class Command(BaseCommand):
    help = "Revisa el esquema y las migraciones de la base contra esta rama (solo lectura)."

    def handle(self, *args, **options):
        self.errores = 0
        self.avisos = 0
        self.modelos_rotos = set()

        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("SG-Prod · diagnóstico de base de datos"))

        try:
            connection.ensure_connection()
        except OperationalError as exc:
            self._error(f"No se pudo conectar a la base: {exc}")
            self._salir_si_hay_errores()
            return

        self.stdout.write(f"  Base: {connection.settings_dict['NAME']}")
        self.stdout.write("")

        self._revisar_esquema()
        self._revisar_migraciones()
        self._revisar_datos_demo()

        self.stdout.write("")
        if self.errores:
            self.stdout.write(self.style.ERROR("La base no está sincronizada con esta rama."))
            self.stdout.write("")
            self.stdout.write("  Qué hacer:")
            self.stdout.write("    1. Si puedes conservar los datos: crea una base nueva y apunta")
            self.stdout.write("       DB_NAME a ella; luego corre `python manage.py migrate`.")
            self.stdout.write("    2. Si puedes perder los datos: reinicia el esquema actual")
            self.stdout.write("       (guía §14.8.1) y vuelve a correr `python manage.py migrate`.")
            self.stdout.write("    3. Nunca uses `migrate --fake` para ocultar este problema.")
            self._salir_si_hay_errores()

        if self.avisos:
            self.stdout.write(self.style.WARNING("Diagnóstico terminado con avisos."))
        else:
            self.stdout.write(self.style.SUCCESS("Base sincronizada con esta rama."))

    # ------------------------------------------------------------------
    # Esquema
    # ------------------------------------------------------------------
    def _revisar_esquema(self):
        modelos = sorted(
            (
                modelo
                for modelo in apps.get_models()
                if modelo._meta.app_label in PROJECT_APPS
                and modelo._meta.managed
                and not modelo._meta.proxy
            ),
            key=lambda modelo: modelo._meta.label_lower,
        )
        tablas = set(connection.introspection.table_names())
        revisados = 0

        with connection.cursor() as cursor:
            for modelo in modelos:
                tabla = modelo._meta.db_table
                if tabla not in tablas:
                    self.modelos_rotos.add(modelo)
                    self._error(f"{modelo._meta.label}: falta la tabla `{tabla}`.")
                    continue

                try:
                    columnas = {
                        columna.name
                        for columna in connection.introspection.get_table_description(
                            cursor, tabla
                        )
                    }
                except Exception as exc:  # pragma: no cover - depende del motor
                    self.modelos_rotos.add(modelo)
                    self._error(f"{modelo._meta.label}: no se pudo leer `{tabla}`: {exc}")
                    continue

                esperadas = {
                    campo.column
                    for campo in modelo._meta.local_fields
                    if campo.column
                }
                faltantes = sorted(esperadas - columnas)
                if faltantes:
                    self.modelos_rotos.add(modelo)
                    self._error(
                        f"{modelo._meta.label}: faltan columnas "
                        f"{', '.join(f'`{columna}`' for columna in faltantes)}."
                    )
                else:
                    revisados += 1

        if self.errores:
            self.stdout.write(
                f"  Esquema: {revisados} modelos OK, {len(self.modelos_rotos)} con problemas."
            )
        else:
            self.stdout.write(f"  Esquema: OK ({revisados} modelos).")

    # ------------------------------------------------------------------
    # Migraciones
    # ------------------------------------------------------------------
    def _revisar_migraciones(self):
        try:
            loader = MigrationLoader(connection)
        except Exception as exc:  # pragma: no cover - depende del grafo de migraciones
            self._error(f"No se pudo leer el historial de migraciones: {exc}")
            return

        en_disco = {
            clave for clave in loader.disk_migrations if clave[0] in PROJECT_APPS
        }
        aplicadas = {
            clave for clave in loader.applied_migrations if clave[0] in PROJECT_APPS
        }
        pendientes = sorted(en_disco - aplicadas)
        desconocidas = sorted(aplicadas - en_disco)

        self.stdout.write("")
        self.stdout.write("  Migraciones:")
        self.stdout.write(f"    Aplicadas: {len(aplicadas & en_disco)}")
        self.stdout.write(f"    Pendientes: {len(pendientes)}")

        for app_label, nombre in pendientes:
            self._error(
                f"Falta aplicar `{app_label}.{nombre}`. Corre `python manage.py migrate`."
            )

        if desconocidas:
            self.stdout.write("    Aplicadas por otra rama:")
            for app_label, nombre in desconocidas:
                self.stdout.write(f"      - {app_label}.{nombre}")
            self._error(
                "La base tiene migraciones que no existen en esta rama. "
                "`migrate` no las puede corregir."
            )

    # ------------------------------------------------------------------
    # Datos de demo
    # ------------------------------------------------------------------
    def _revisar_datos_demo(self):
        self.stdout.write("")
        self.stdout.write("  Datos de demo:")

        conteos = {}
        for etiqueta, modelo in DEMO_MODELS:
            if modelo in self.modelos_rotos:
                continue
            try:
                conteos[etiqueta] = modelo.objects.count()
            except Exception as exc:  # pragma: no cover - depende del motor
                self._warning(f"No se pudo contar {etiqueta}: {exc}")
                continue
            self.stdout.write(f"    {etiqueta:<14} {conteos[etiqueta]}")

        if not conteos.get("Empleados"):
            self._warning(
                "No hay empleados de demo. Ejecuta `python manage.py seed_demo --reset` "
                "en una base local."
            )

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    def _error(self, mensaje):
        self.errores += 1
        self.stdout.write(self.style.ERROR(f"[ERROR] {mensaje}"))

    def _warning(self, mensaje):
        self.avisos += 1
        self.stdout.write(self.style.WARNING(f"[AVISO] {mensaje}"))

    def _salir_si_hay_errores(self):
        if self.errores:
            sys.exit(1)
