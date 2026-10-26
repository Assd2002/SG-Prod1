# Dataset de demo (US-04)

`demo_sgprod.json` contiene los **datos maestros** que carga `seed_demo`:

- 5 líneas y 40 estaciones.
- Metas por estación.
- 12 motivos de defecto.
- 200 empleados: 1 Gerente, 5 Jefes y 194 Operadores.
- PIN de demo.

El comando carga estos catálogos y la matriz de habilidades. **No** crea
asignaciones ni registros de producción: esa lógica se conecta en historias
posteriores.

## Uso

```bash
python manage.py seed_demo
python manage.py seed_demo --reset
python manage.py seed_demo --empleados 80
python manage.py seed_demo --archivo data/seed/demo_sgprod.json --reset
```

`--empleados` conserva siempre al Gerente y a todos los Jefes del JSON; el resto
se toma del inicio de la lista de Operadores.

## Formato

```json
{
  "version": 1,
  "nombre": "Planta demo SG-Prod",
  "pin_default": "123456",
  "lineas": [
    {
      "nombre": "Línea 3",
      "estaciones": [
        {"nombre": "Corte", "nivel": "experto", "meta": 88}
      ]
    }
  ],
  "defectos": [
    {"codigo": "DEF-01", "descripcion": "Falta de estaño"}
  ],
  "empleados": {
    "gerente": {"numero": "SG-0001", "nombre": "Laura Méndez"},
    "jefes": [{"numero": "SG-0002", "nombre": "Rocío Salas"}],
    "operadores": [{"numero": "SG-0005", "nombre": "Verónica Reyes"}]
  }
}
```

Validaciones:

- nombres de línea únicos;
- nombres de estación únicos dentro de su línea;
- `nivel` en `principiante`, `autonomo`, `experto` o `instructor`;
- `meta` entero positivo;
- códigos de defecto únicos;
- números de empleado únicos;
- al menos una línea, una estación, un defecto, un Gerente, un Jefe y un Operador.

Este archivo es la fuente de verdad de los datos de demo. No edites nombres,
estaciones o personas dentro del comando.
