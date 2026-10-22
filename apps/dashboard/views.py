from django.shortcuts import render

def pantalla_operador(request):
    return render(request, 'dashboard/operador.html')

def pantalla_jefe(request):
    return render(request, 'dashboard/jefe.html')

def pantalla_gerente(request):
    return render(request, 'dashboard/gerente.html')
# Create your views here.
