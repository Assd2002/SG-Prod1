from django.contrib import admin
from .models import (
    Empleado,
    Linea,
    Estacion,
    Habilidad,
    Asignacion,
    RegistroHorario,
    ParticipacionProduccion,
    CatalogoDefecto,
    DetalleDefecto,
    MetaProduccion,
)

# Registramos todos los modelos para que aparezcan en el panel de administración
admin.site.register(Empleado)
admin.site.register(Linea)
admin.site.register(Estacion)
admin.site.register(Habilidad)
admin.site.register(Asignacion)
admin.site.register(RegistroHorario)
admin.site.register(ParticipacionProduccion)
admin.site.register(CatalogoDefecto)
admin.site.register(DetalleDefecto)
admin.site.register(MetaProduccion)
# Register your models here.
