from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Empleado
from .forms import LoginForm

def login_empleado(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            num_emp = form.cleaned_data['numero_empleado'].strip()
            pin_ingresado = form.cleaned_data['pin'].strip()

            try:
                empleado = Empleado.objects.get(numero_empleado__iexact=num_emp.strip())

                if not empleado.activo:
                    messages.error(request, "Acceso denegado: El usuario se encuentra inactivo.")
                    return render(request, 'login.html', {'form': form})

                if empleado.pin == pin_ingresado:
                    request.session['empleado_id'] = empleado.id
                    request.session['empleado_nombre'] = empleado.nombre
                    
                    tipo_rol = empleado.rol.tipo_rol.lower() if empleado.rol else 'operador'

                    if 'gerente' in tipo_rol:
                        return redirect('dashboard:pantalla_gerente')
                    elif 'jefe' in tipo_rol:
                        return redirect('dashboard:pantalla_jefe')
                    else:
                        return redirect('dashboard:pantalla_operador')
                else:
                    messages.error(request, "Acceso denegado: PIN incorrecto.")

            except Empleado.DoesNotExist:
                messages.error(request, "Acceso denegado: Número de empleado no registrado.")
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})