"""Admin de personal (US-05, RF-1.1).

Empleados y estaciones se consultan y administran desde el Admin de Django.
"""

from django.contrib import admin

from .models import Empleado, Estacion, Linea, Rol, SkillMatrix


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    """Consulta de empleados: número, nombre y estado."""

    list_display = ("numero_empleado", "nombre", "activo", "rol")
    list_filter = ("activo", "rol")
    search_fields = ("numero_empleado", "nombre")

    def get_queryset(self, request):
        """Un empleado dado de baja no aparece como disponible."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(activo=True)


@admin.register(Estacion)
class EstacionAdmin(admin.ModelAdmin):
    """Consulta de estaciones por línea."""

    list_display = ("nombre", "linea", "orden")
    list_filter = ("linea",)
    search_fields = ("nombre",)


@admin.register(Linea)
class LineaAdmin(admin.ModelAdmin):
    """Consulta de las líneas de producción."""

    list_display = ("nombre",)
    search_fields = ("nombre",)


admin.site.register(Rol)
admin.site.register(SkillMatrix)
