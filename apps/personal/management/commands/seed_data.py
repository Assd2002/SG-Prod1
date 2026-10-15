from django.core.management.base import BaseCommand
from apps.personal.models import Linea, Estacion, Empleado, Habilidad, CatalogoDefecto

class Command(BaseCommand):
    help = 'Llena la base de datos con datos de prueba iniciales para SG-Prod'

    def handle(self, *args, **kwargs):
        self.stdout.write('Iniciando la creación de datos de prueba...')

        # 1. Crear Líneas de Producción
        linea_1, _ = Linea.objects.get_or_create(nombre='Línea A - Ensamble')
        linea_2, _ = Linea.objects.get_or_create(nombre='Línea B - Acabados')

        # 2. Crear Estaciones
        Estacion.objects.get_or_create(nombre='Estación 1 - Soldadura', linea=linea_1)
        Estacion.objects.get_or_create(nombre='Estación 2 - Empaque', linea=linea_2)

        # 3. Crear Empleado de prueba
        Empleado.objects.get_or_create(numero_empleado='EMP001', defaults={'nombre': 'Carlos Pérez'})
        
        # 4. Catálogo de Defectos (solo con el código para evitar conflictos de campos)
        CatalogoDefecto.objects.get_or_create(codigo='DEF01')

        self.stdout.write(self.style.SUCCESS('¡Base de datos poblada con éxito con los datos de prueba!'))