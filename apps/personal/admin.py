"""Admin de personal (US-05, RF-1.1).

Empleados y estaciones se consultan y administran desde el Admin de Django.
"""

from django.contrib import admin

from .models import Empleado, Estacion, Linea, Rol, SkillMatrix


def lineas_del_usuario(user):
    """Líneas asignadas al Jefe de Línea.

    US-05 no modifica el modelo, así que la línea asignada se representa con
    los grupos de Django: el grupo del jefe se llama igual que su línea
    (`Línea 3`, `Línea 4`, ...). Un usuario sin grupo de línea no ve líneas
    ni estaciones; el superusuario ve todas.
    """
    if not user.is_authenticated:
        return Linea.objects.none()
    return Linea.objects.filter(nombre__in=user.groups.values_list("name", flat=True))


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
    search_fields = ("nombre",)

    def get_list_filter(self, request):
        """El filtro por línea no se le ofrece al Jefe de Línea.

        Mostrarle todas las líneas en el filtro contradice que solo ve su
        propia línea; además solo tiene una, así que el filtro no le aporta.
        """
        if request.user.is_superuser:
            return ("linea",)
        return ()

    def get_queryset(self, request):
        """El Jefe de Línea solo ve las estaciones de su línea."""
        qs = super().get_queryset(request).select_related("linea")
        if request.user.is_superuser:
            return qs
        return qs.filter(linea__in=lineas_del_usuario(request.user))


@admin.register(Linea)
class LineaAdmin(admin.ModelAdmin):
    """Consulta de las líneas de producción."""

    list_display = ("nombre",)
    search_fields = ("nombre",)

    def get_queryset(self, request):
        """El Jefe de Línea solo ve su propia línea."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(pk__in=lineas_del_usuario(request.user))


admin.site.register(Rol)
admin.site.register(SkillMatrix)
