from django.urls import path
from . import views

app_name = 'personal'

urlpatterns = [
    path('login/', views.login_empleado, name='login'),
]