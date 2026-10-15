from django.shortcuts import render
from apps.personal.models import Linea, Estacion, Empleado, CatalogoDefecto

def dashboard_metricas(request):
    # Obtenemos los totales para las métricas de producción
    total_lineas = Linea.objects.count()
    total_estaciones = Estacion.objects.count()
    total_empleados = Empleado.objects.count()
    total_defectos = CatalogoDefecto.objects.count()

    context = {
        'total_lineas': total_lineas,
        'total_estaciones': total_estaciones,
        'total_empleados': total_empleados,
        'total_defectos': total_defectos,
    }
    
    return render(request, 'personal/dashboard.html', context)
