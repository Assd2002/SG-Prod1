"""Pruebas de US-05: administración de empleados y estaciones (RF-1.1)."""

from types import SimpleNamespace

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.urls import reverse

from .models import Empleado, Estacion, Linea

User = get_user_model()

PERMISOS_DE_CONSULTA = ("view_empleado", "view_estacion", "view_linea")


@pytest.fixture
def planta(db):
    """Dos líneas con una estación cada una y un empleado dado de baja."""
    linea_3 = Linea.objects.create(nombre="Línea 3")
    linea_4 = Linea.objects.create(nombre="Línea 4")
    Estacion.objects.create(linea=linea_3, nombre="Corte", orden=1)
    Estacion.objects.create(linea=linea_4, nombre="Soldadura", orden=1)
    Empleado.objects.create(numero_empleado="SG-0100", nombre="Ana Activa")
    Empleado.objects.create(
        numero_empleado="SG-0101",
        nombre="Beto Baja",
        activo=False,
    )
    return SimpleNamespace(linea_3=linea_3, linea_4=linea_4)


def crear_usuario(username, *, superusuario=False, grupos=()):
    """Crea el usuario de Django que usa el Admin, con permiso de consulta."""
    usuario = User.objects.create_user(
        username=username,
        password="clave-de-prueba",
        is_staff=True,
        is_superuser=superusuario,
    )
    if not superusuario:
        usuario.user_permissions.set(
            Permission.objects.filter(codename__in=PERMISOS_DE_CONSULTA)
        )
    for nombre in grupos:
        grupo, _ = Group.objects.get_or_create(name=nombre)
        usuario.groups.add(grupo)
    return usuario


def test_admin_empleado_muestra_numero_nombre_y_estado(planta, client):
    client.force_login(crear_usuario("admin", superusuario=True))

    respuesta = client.get(reverse("admin:personal_empleado_changelist"))

    contenido = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert "SG-0100" in contenido
    assert "Ana Activa" in contenido
    assert "field-activo" in contenido


def test_empleado_dado_de_baja_no_aparece_para_el_jefe(planta, client):
    client.force_login(crear_usuario("jefe-linea-3", grupos=["Línea 3"]))

    contenido = client.get(
        reverse("admin:personal_empleado_changelist")
    ).content.decode()

    assert "SG-0100" in contenido
    assert "SG-0101" not in contenido


def test_jefe_de_linea_solo_ve_las_estaciones_de_su_linea(planta, client):
    client.force_login(crear_usuario("jefe-linea-3", grupos=["Línea 3"]))

    contenido = client.get(
        reverse("admin:personal_estacion_changelist")
    ).content.decode()

    assert "Corte" in contenido
    assert "Línea 3" in contenido
    assert "Soldadura" not in contenido
    assert "Línea 4" not in contenido


def test_jefe_de_linea_solo_ve_su_linea(planta, client):
    client.force_login(crear_usuario("jefe-linea-3", grupos=["Línea 3"]))

    contenido = client.get(reverse("admin:personal_linea_changelist")).content.decode()

    assert "Línea 3" in contenido
    assert "Línea 4" not in contenido


def test_superusuario_ve_todas_las_estaciones(planta, client):
    client.force_login(crear_usuario("admin", superusuario=True))

    contenido = client.get(
        reverse("admin:personal_estacion_changelist")
    ).content.decode()

    assert "Corte" in contenido
    assert "Soldadura" in contenido


def test_usuario_sin_linea_asignada_no_ve_estaciones(planta, client):
    client.force_login(crear_usuario("sin-linea"))

    contenido = client.get(
        reverse("admin:personal_estacion_changelist")
    ).content.decode()

    assert "Corte" not in contenido
    assert "Soldadura" not in contenido
