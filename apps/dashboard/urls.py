from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('operador/', views.pantalla_operador, name='pantalla_operador'),
    path('jefe/', views.pantalla_jefe, name='pantalla_jefe'),
    path('gerente/', views.pantalla_gerente, name='pantalla_gerente'),
]