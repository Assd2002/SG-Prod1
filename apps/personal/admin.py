
# Register your models here.
from django.contrib import admin
from .models import Empleado, Linea, Estacion, Rol, SkillMatrix

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    # Criterio 1: muestra número, nombre y estado
    list_display = ('numero_empleado', 'nombre', 'activo', 'rol')
    list_filter = ('activo', 'rol')
    search_fields = ('numero_empleado', 'nombre')

    # Criterio 2: no muestra los dados de baja (activo=False) a menos que seas superusuario
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(activo=True)


@admin.register(Estacion)
class EstacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'linea', 'orden')

    # Criterio 3: el Jefe de Línea solo ve las estaciones de su línea
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(linea__jefe=request.user)


@admin.register(Linea)
class LineaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'jefe')


admin.site.register(Rol)
admin.site.register(SkillMatrix)