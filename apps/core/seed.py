"""Lectura y validación del dataset JSON que usa ``seed_demo``.

El JSON contiene los datos maestros del escenario (líneas, estaciones, metas,
defectos y personas). Es la fuente de verdad del seeding y se mantiene separado
del comando para que el equipo pueda ajustar el escenario sin tocar Python.

Para agregar una línea, una estación o una persona basta con editar
``data/seed/demo_sgprod.json``; la validación de este módulo avisa si el
archivo queda inconsistente.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings

NIVELES_VALIDOS = {"principiante", "autonomo", "experto", "instructor"}


@dataclass(frozen=True)
class EstacionDemo:
    nombre: str
    nivel: str
    meta: int


@dataclass(frozen=True)
class LineaDemo:
    nombre: str
    estaciones: tuple[EstacionDemo, ...]


@dataclass(frozen=True)
class DefectoDemo:
    codigo: str
    descripcion: str


@dataclass(frozen=True)
class EmpleadoDemo:
    numero: str
    nombre: str


@dataclass(frozen=True)
class EmpleadosDemo:
    gerente: EmpleadoDemo
    jefes: tuple[EmpleadoDemo, ...]
    operadores: tuple[EmpleadoDemo, ...]

    @property
    def total(self) -> int:
        return 1 + len(self.jefes) + len(self.operadores)


@dataclass(frozen=True)
class DatasetDemo:
    version: int
    nombre: str
    descripcion: str
    pin_default: str
    dias_default: int
    lineas: tuple[LineaDemo, ...]
    defectos: tuple[DefectoDemo, ...]
    empleados: EmpleadosDemo

    @property
    def total_estaciones(self) -> int:
        return sum(len(linea.estaciones) for linea in self.lineas)


def ruta_dataset_por_defecto() -> Path:
    """Ruta del JSON incluido en el repositorio."""
    return Path(settings.BASE_DIR) / "data" / "seed" / "demo_sgprod.json"


def cargar_dataset(ruta: str | Path | None = None) -> DatasetDemo:
    """Carga y valida el JSON. Lanza ``ValueError`` con un mensaje accionable."""
    archivo = Path(ruta) if ruta else ruta_dataset_por_defecto()
    try:
        texto = archivo.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ValueError(f"No existe el dataset: {archivo}") from exc
    except OSError as exc:
        raise ValueError(f"No se pudo leer el dataset {archivo}: {exc}") from exc

    try:
        datos = json.loads(texto)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"El JSON {archivo} no es válido (línea {exc.lineno}, columna {exc.colno}): {exc.msg}"
        ) from exc

    if not isinstance(datos, dict):
        raise ValueError("El dataset debe ser un objeto JSON en la raíz.")

    version = _entero(datos, "version", "dataset", minimo=1)
    if version != 1:
        raise ValueError(f"Versión de dataset no soportada: {version}. Se espera la 1.")

    lineas = _lineas(datos.get("lineas"))
    defectos = _defectos(datos.get("defectos"))
    empleados = _empleados(datos.get("empleados"))

    pin_default = datos.get("pin_default", "123456")
    if not isinstance(pin_default, str) or not pin_default.isdigit():
        raise ValueError("'pin_default' debe ser una cadena de dígitos.")
    if len(pin_default) != 6:
        raise ValueError("'pin_default' debe tener 6 dígitos.")

    dias_default = _entero(datos, "dias_default", "dataset", minimo=1)
    nombre = str(datos.get("nombre") or "Dataset de demostración").strip()
    descripcion = str(datos.get("descripcion") or "").strip()

    return DatasetDemo(
        version=version,
        nombre=nombre,
        descripcion=descripcion,
        pin_default=pin_default,
        dias_default=dias_default,
        lineas=lineas,
        defectos=defectos,
        empleados=empleados,
    )


def _lineas(valor) -> tuple[LineaDemo, ...]:
    if not isinstance(valor, list) or not valor:
        raise ValueError("'lineas' debe ser una lista con al menos una línea.")

    nombres = set()
    resultado = []
    for indice, linea in enumerate(valor, start=1):
        contexto = f"lineas[{indice}]"
        if not isinstance(linea, dict):
            raise ValueError(f"{contexto} debe ser un objeto.")
        nombre = _texto(linea, "nombre", contexto)
        if nombre in nombres:
            raise ValueError(f"La línea '{nombre}' está repetida.")
        nombres.add(nombre)

        estaciones_valor = linea.get("estaciones")
        if not isinstance(estaciones_valor, list) or not estaciones_valor:
            raise ValueError(f"{contexto}.estaciones debe ser una lista no vacía.")

        estaciones = []
        nombres_estacion = set()
        for posicion, estacion in enumerate(estaciones_valor, start=1):
            contexto_estacion = f"{contexto}.estaciones[{posicion}]"
            if not isinstance(estacion, dict):
                raise ValueError(f"{contexto_estacion} debe ser un objeto.")
            nombre_estacion = _texto(estacion, "nombre", contexto_estacion)
            if nombre_estacion in nombres_estacion:
                raise ValueError(f"La estación '{nombre_estacion}' está repetida en {nombre}.")
            nombres_estacion.add(nombre_estacion)

            nivel = _texto(estacion, "nivel", contexto_estacion)
            if nivel not in NIVELES_VALIDOS:
                raise ValueError(
                    f"{contexto_estacion}.nivel '{nivel}' no es válido; "
                    f"usa uno de: {', '.join(sorted(NIVELES_VALIDOS))}."
                )
            meta = _entero(estacion, "meta", contexto_estacion, minimo=1)
            estaciones.append(EstacionDemo(nombre=nombre_estacion, nivel=nivel, meta=meta))

        resultado.append(LineaDemo(nombre=nombre, estaciones=tuple(estaciones)))

    return tuple(resultado)


def _defectos(valor) -> tuple[DefectoDemo, ...]:
    if not isinstance(valor, list) or not valor:
        raise ValueError("'defectos' debe ser una lista con al menos un motivo.")

    codigos = set()
    resultado = []
    for indice, defecto in enumerate(valor, start=1):
        contexto = f"defectos[{indice}]"
        if not isinstance(defecto, dict):
            raise ValueError(f"{contexto} debe ser un objeto.")
        codigo = _texto(defecto, "codigo", contexto)
        if codigo in codigos:
            raise ValueError(f"El código de defecto '{codigo}' está repetido.")
        codigos.add(codigo)
        descripcion = _texto(defecto, "descripcion", contexto)
        resultado.append(DefectoDemo(codigo=codigo, descripcion=descripcion))
    return tuple(resultado)


def _empleados(valor) -> EmpleadosDemo:
    if not isinstance(valor, dict):
        raise ValueError("'empleados' debe ser un objeto con gerente, jefes y operadores.")

    gerente = _persona(valor.get("gerente"), "empleados.gerente")
    jefes_valor = valor.get("jefes")
    operadores_valor = valor.get("operadores")
    if not isinstance(jefes_valor, list) or not jefes_valor:
        raise ValueError("'empleados.jefes' debe ser una lista con al menos un jefe.")
    if not isinstance(operadores_valor, list) or not operadores_valor:
        raise ValueError("'empleados.operadores' debe ser una lista con al menos un operador.")

    jefes = tuple(
        _persona(persona, f"empleados.jefes[{indice}]")
        for indice, persona in enumerate(jefes_valor, start=1)
    )
    operadores = tuple(
        _persona(persona, f"empleados.operadores[{indice}]")
        for indice, persona in enumerate(operadores_valor, start=1)
    )

    numeros = [gerente.numero, *(p.numero for p in jefes), *(p.numero for p in operadores)]
    vistos = set()
    repetidos = set()
    for numero in numeros:
        if numero in vistos:
            repetidos.add(numero)
        vistos.add(numero)
    if repetidos:
        raise ValueError(
            "Hay números de empleado repetidos en el dataset: " + ", ".join(sorted(repetidos))
        )

    return EmpleadosDemo(gerente=gerente, jefes=jefes, operadores=operadores)


def _persona(valor, contexto: str) -> EmpleadoDemo:
    if not isinstance(valor, dict):
        raise ValueError(f"{contexto} debe ser un objeto con numero y nombre.")
    return EmpleadoDemo(
        numero=_texto(valor, "numero", contexto),
        nombre=_texto(valor, "nombre", contexto),
    )


def _texto(datos: dict, campo: str, contexto: str) -> str:
    valor = datos.get(campo)
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(f"{contexto}.{campo} debe ser un texto no vacío.")
    return valor.strip()


def _entero(datos: dict, campo: str, contexto: str, *, minimo: int = 0) -> int:
    valor = datos.get(campo)
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise ValueError(f"{contexto}.{campo} debe ser un entero.")
    if valor < minimo:
        raise ValueError(f"{contexto}.{campo} debe ser mayor o igual a {minimo}.")
    return valor
