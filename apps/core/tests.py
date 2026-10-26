"""Pruebas del dataset de demo (US-04).

Solo validan el archivo y no necesitan base de datos; la carga completa se
prueba contra una base local con `python manage.py seed_demo --reset`.
"""

import json

import pytest

from apps.core.seed import cargar_dataset, ruta_dataset_por_defecto


def test_dataset_demo_tiene_el_volumen_esperado():
    dataset = cargar_dataset()

    assert len(dataset.lineas) == 5
    assert dataset.total_estaciones == 40
    assert dataset.empleados.total == 200
    assert dataset.empleados.gerente.numero == "SG-0001"
    assert any(
        operador.numero == "SG-0005" for operador in dataset.empleados.operadores
    )


def test_dataset_rechaza_numeros_de_empleado_repetidos(tmp_path):
    datos = json.loads(ruta_dataset_por_defecto().read_text(encoding="utf-8"))
    datos["empleados"]["operadores"][0]["numero"] = datos["empleados"]["gerente"]["numero"]
    archivo = tmp_path / "dataset_invalido.json"
    archivo.write_text(json.dumps(datos), encoding="utf-8")

    with pytest.raises(ValueError, match="repetidos"):
        cargar_dataset(archivo)


@pytest.mark.django_db
def test_check_db_accepts_the_current_schema(capsys):
    from django.core.management import call_command

    call_command("check_db")

    salida = capsys.readouterr().out
    assert "Esquema: OK" in salida
    assert "[ERROR]" not in salida
