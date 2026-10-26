"""Carga los datos maestros del escenario de demo (US-04).

El comando no crea asignaciones, registros de producción ni cálculos de
tablero: esas piezas se conectan en historias posteriores. Aquí solo se
preparan los catálogos que necesitan todas las pantallas para dejar de estar
vacías cuando el equipo conecte la lógica.
"""

import random

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.calidad.models import (
    Asignacion,
    CatalogoDefecto,
    DetalleDefecto,
    RegistroCalidadHorario,
)
from apps.core.seed import cargar_dataset, ruta_dataset_por_defecto
from apps.dashboard.models import (
    AlertaCapacitacion,
    BonoIncentivo,
    MetaEstacion,
)
from apps.personal.models import (
    Empleado,
    Estacion,
    Linea,
    NivelHabilidad,
    Rol,
    SkillMatrix,
)

ROLES_DEMO = (
    ("operador", "Operador"),
    ("jefe", "Jefe de Línea"),
    ("gerente", "Gerente de Producción"),
)

NIVELES_COBERTURA = (
    NivelHabilidad.INSTRUCTOR,
    NivelHabilidad.EXPERTO,
    NivelHabilidad.EXPERTO,
    NivelHabilidad.AUTONOMO,
    NivelHabilidad.AUTONOMO,
)


class Command(BaseCommand):
    help = "Carga el escenario maestro de demo desde JSON (US-04)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--archivo",
            default=None,
            help="Ruta al JSON. Por defecto data/seed/demo_sgprod.json.",
        )
        parser.add_argument(
            "--empleados",
            type=int,
            default=None,
            help=(
                "Total de empleados a cargar. Por defecto, todos los del JSON. "
                "No elimina sobrantes; combínalo con --reset para un volumen exacto."
            ),
        )
        parser.add_argument(
            "--pin",
            default=None,
            help="PIN de demo. Por defecto, el valor del JSON (123456).",
        )
        parser.add_argument(
            "--aleatorio",
            type=int,
            default=2026,
            help="Semilla para que la matriz de habilidades sea reproducible.",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help=(
                "Borra TODOS los datos de dominio de la base antes de cargar "
                "(no solo los de demo). Solo para desarrollo local."
            ),
        )

    def handle(self, *args, **options):
        try:
            dataset = cargar_dataset(options["archivo"])
        except ValueError as exc:
            raise CommandError(f"Dataset inválido: {exc}") from exc

        total_dataset = dataset.empleados.total
        empleados_total = (
            options["empleados"]
            if options["empleados"] is not None
            else total_dataset
        )
        pin = options["pin"] if options["pin"] is not None else dataset.pin_default

        minimo = 1 + len(dataset.empleados.jefes) + 1
        if empleados_total < max(10, minimo):
            raise CommandError(
                f"Se necesitan al menos {max(10, minimo)} empleados "
                f"(Gerente + Jefes + Operadores); el JSON tiene {total_dataset}."
            )
        if empleados_total > total_dataset:
            raise CommandError(
                f"El dataset solo tiene {total_dataset} empleados; "
                f"pediste {empleados_total}."
            )
        if not pin.isdigit() or len(pin) != 6:
            raise CommandError("El PIN debe tener exactamente 6 dígitos.")

        self.dataset = dataset
        self.empleados_total = empleados_total
        self.pin = pin
        self.rng = random.Random(options["aleatorio"])
        self.archivo = options["archivo"] or str(ruta_dataset_por_defecto())

        with transaction.atomic():
            if options["reset"]:
                self._reset()
            roles = self._roles()
            lineas = self._lineas_y_estaciones()
            defectos = self._defectos()
            empleados, gerente, jefes = self._empleados(roles)
            estaciones = list(
                Estacion.objects.filter(linea__in=lineas)
                .select_related("linea")
                .order_by("linea__nombre", "orden")
            )
            self._metas(estaciones)
            habilidades = self._habilidades(empleados, estaciones)

        self._resumen(
            lineas=lineas,
            estaciones=estaciones,
            empleados=empleados,
            gerente=gerente,
            jefes=jefes,
            defectos=defectos,
            habilidades=habilidades,
        )

    # ------------------------------------------------------------------
    # Catálogos
    # ------------------------------------------------------------------
    def _reset(self):
        self.stdout.write(self.style.WARNING("Borrando datos de demo…"))
        AlertaCapacitacion.objects.all().delete()
        BonoIncentivo.objects.all().delete()
        DetalleDefecto.objects.all().delete()
        RegistroCalidadHorario.objects.all().delete()
        Asignacion.objects.all().delete()
        SkillMatrix.objects.all().delete()
        MetaEstacion.objects.all().delete()
        Estacion.objects.all().delete()
        Linea.objects.all().delete()
        Empleado.objects.all().delete()
        Rol.objects.all().delete()
        CatalogoDefecto.objects.all().delete()

    def _roles(self):
        roles = {}
        for tipo, nombre in ROLES_DEMO:
            rol, _ = Rol.objects.update_or_create(
                tipo_rol=tipo, defaults={"nombre": nombre}
            )
            roles[tipo] = rol
        return roles

    def _lineas_y_estaciones(self):
        lineas = []
        for linea_demo in self.dataset.lineas:
            linea, _ = Linea.objects.update_or_create(nombre=linea_demo.nombre)
            lineas.append(linea)
            for orden, estacion_demo in enumerate(linea_demo.estaciones, start=1):
                Estacion.objects.update_or_create(
                    linea=linea,
                    nombre=estacion_demo.nombre,
                    defaults={"orden": orden},
                )
        return lineas

    def _defectos(self):
        defectos = []
        for defecto_demo in self.dataset.defectos:
            defecto, _ = CatalogoDefecto.objects.update_or_create(
                codigo=defecto_demo.codigo,
                defaults={"descripcion": defecto_demo.descripcion},
            )
            defectos.append(defecto)
        return defectos

    def _empleados(self, roles):
        gerente_demo = self.dataset.empleados.gerente
        jefes_demo = self.dataset.empleados.jefes
        operadores_demo = self.dataset.empleados.operadores
        cupo_operadores = self.empleados_total - 1 - len(jefes_demo)
        operadores_demo = operadores_demo[:cupo_operadores]

        empleados = []
        jefes = []

        def guardar(persona_demo, tipo):
            empleado, _ = Empleado.objects.update_or_create(
                numero_empleado=persona_demo.numero,
                defaults={
                    "nombre": persona_demo.nombre,
                    "rol": roles[tipo],
                    "activo": True,
                    "pin": self.pin,
                },
            )
            return empleado

        gerente = guardar(gerente_demo, "gerente")
        empleados.append(gerente)
        for jefe_demo in jefes_demo:
            jefe = guardar(jefe_demo, "jefe")
            empleados.append(jefe)
            jefes.append(jefe)
        for operador_demo in operadores_demo:
            empleados.append(guardar(operador_demo, "operador"))
        return empleados, gerente, jefes

    def _metas(self, estaciones):
        metas = {}
        for linea_demo in self.dataset.lineas:
            for estacion_demo in linea_demo.estaciones:
                metas[(linea_demo.nombre, estacion_demo.nombre)] = estacion_demo.meta

        for estacion in estaciones:
            meta = metas.get((estacion.linea.nombre, estacion.nombre), 100)
            MetaEstacion.objects.update_or_create(
                estacion=estacion,
                defaults={"piezas_por_hora_meta": meta},
            )

    # ------------------------------------------------------------------
    # Matriz de habilidades
    # ------------------------------------------------------------------
    def _habilidades(self, empleados, estaciones):
        operadores = [empleado for empleado in empleados if empleado.rol.tipo_rol == "operador"]
        if not operadores:
            raise CommandError("No hay operadores para construir la matriz de habilidades.")

        habilidades = {}
        for estacion in estaciones:
            candidatos = self.rng.sample(
                operadores, k=min(len(NIVELES_COBERTURA), len(operadores))
            )
            for empleado, nivel in zip(candidatos, NIVELES_COBERTURA, strict=False):
                habilidades[(empleado.id, estacion.id)] = nivel

        # Cada operador debe tener al menos una estación para que la matriz no
        # deje personas completamente vacías.
        for empleado in operadores:
            if not any(clave[0] == empleado.id for clave in habilidades):
                estacion = self.rng.choice(estaciones)
                habilidades[(empleado.id, estacion.id)] = NivelHabilidad.AUTONOMO

        SkillMatrix.objects.filter(empleado__in=operadores).delete()
        SkillMatrix.objects.bulk_create(
            [
                SkillMatrix(empleado_id=empleado_id, estacion_id=estacion_id, nivel=nivel)
                for (empleado_id, estacion_id), nivel in habilidades.items()
            ],
            batch_size=500,
        )
        return habilidades

    def _resumen(
        self,
        *,
        lineas,
        estaciones,
        empleados,
        gerente,
        jefes,
        defectos,
        habilidades,
    ):
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS("SG-Prod · datos maestros de demo cargados")
        )
        self.stdout.write(f"  Dataset:       {self.dataset.nombre}")
        self.stdout.write(f"  Archivo:       {self.archivo}")
        self.stdout.write(f"  Líneas:        {len(lineas)}")
        self.stdout.write(f"  Estaciones:    {len(estaciones)}")
        self.stdout.write(f"  Empleados:     {len(empleados)}")
        self.stdout.write(f"  Habilidades:   {len(habilidades)}")
        self.stdout.write(f"  Defectos:      {len(defectos)}")
        self.stdout.write(f"  Metas:         {MetaEstacion.objects.count()}")
        self.stdout.write("")
        self.stdout.write(
            self.style.MIGRATE_HEADING(f"Credenciales de demo (PIN: {self.pin})")
        )
        self.stdout.write(f"  Gerente:       {gerente.numero_empleado} · {gerente.nombre}")
        for jefe in jefes:
            self.stdout.write(f"  Jefe:          {jefe.numero_empleado} · {jefe.nombre}")
        operador = next(
            (empleado for empleado in empleados if empleado.rol.tipo_rol == "operador"),
            None,
        )
        if operador:
            self.stdout.write(
                f"  Operador:      {operador.numero_empleado} · {operador.nombre}"
            )
        self.stdout.write("")
        self.stdout.write(
            "  Nota: asignaciones y producción se agregan en historias posteriores."
        )
