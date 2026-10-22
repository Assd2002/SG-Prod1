from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.apps import apps

User = get_user_model()

class Command(BaseCommand):
    help = 'Carga datos de prueba reproducibles para la demo (US-04)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Iniciando Seeding de Datos (US-04) ==='))

        # Búsqueda segura de modelos
        def get_model_safe(model_name):
            for model in apps.get_models():
                if model.__name__.lower() == model_name.lower():
                    return model
            raise LookupError(f"No se encontró el modelo {model_name}")

        # Función auxiliar para crear registros usando solo los campos existentes en el modelo
        def safe_get_or_create(model, search_kwargs, defaults_kwargs=None):
            if defaults_kwargs is None:
                defaults_kwargs = {}
            valid_fields = {f.name for f in model._meta.get_fields()}
            
            # Filtrar solo argumentos que sí pertenecen al modelo
            filtered_search = {k: v for k, v in search_kwargs.items() if k in valid_fields}
            filtered_defaults = {k: v for k, v in defaults_kwargs.items() if k in valid_fields}
            
            return model.objects.get_or_create(**filtered_search, defaults=filtered_defaults)

        Rol = get_model_safe('Rol')
        Empleado = get_model_safe('Empleado')
        Linea = get_model_safe('Linea')
        Estacion = get_model_safe('Estacion')
        SkillMatrix = get_model_safe('SkillMatrix')
        MetaEstacion = get_model_safe('MetaEstacion')
        CatalogoDefecto = get_model_safe('CatalogoDefecto')

        # 1. Crear Usuario Administrador y Roles
        self.stdout.write('1. Creando Usuarios y Roles...')
        admin_user, _ = User.objects.get_or_create(
            username='admin_demo',
            defaults={'email': 'admin@sgprod.com', 'is_staff': True, 'is_superuser': True}
        )
        admin_user.set_password('admin123')
        admin_user.save()

        rol_operador, _ = safe_get_or_create(Rol, {'tipo_rol': 'Operador'}, {'nombre': 'Operador'})
        rol_supervisor, _ = safe_get_or_create(Rol, {'tipo_rol': 'Supervisor'}, {'nombre': 'Supervisor'})

        # 2. Crear Empleados
        self.stdout.write('2. Creando Empleados...')
        emp1, _ = safe_get_or_create(
            Empleado, 
            {'numero_empleado': 'EMP001'}, 
            {'nombre': 'Juan Pérez', 'rol': rol_operador, 'activo': True}
        )
        emp2, _ = safe_get_or_create(
            Empleado, 
            {'numero_empleado': 'EMP002'}, 
            {'nombre': 'María Gómez', 'rol': rol_operador, 'activo': True}
        )

        # 3. Crear Líneas y Estaciones
        self.stdout.write('3. Creando Líneas y Estaciones...')
        linea_a, _ = safe_get_or_create(Linea, {'nombre': 'Línea Ensamblaje A'})
        
        estacion_1, _ = safe_get_or_create(
            Estacion, 
            {'nombre': 'Estación 1 - Crimpado', 'linea': linea_a}, 
            {'orden': 1}
        )
        estacion_2, _ = safe_get_or_create(
            Estacion, 
            {'nombre': 'Estación 2 - Soldadura', 'linea': linea_a}, 
            {'orden': 2}
        )

        # 4. Crear Matriz de Habilidades
        self.stdout.write('4. Creando Matriz de Habilidades...')
        safe_get_or_create(
            SkillMatrix, 
            {'empleado': emp1, 'estacion': estacion_1}, 
            {'nivel_habilidad': 4, 'nivel': 4, 'nivel_certificacion': 4, 'certificado': True}
        )

        # 5. Crear Catálogo de Defectos
        self.stdout.write('5. Creando Catálogo de Defectos...')
        safe_get_or_create(
            CatalogoDefecto, 
            {'codigo': 'DEF01'}, 
            {'nombre': 'Mala Soldadura', 'categoria': 'Crítico', 'descripcion': 'Falta de estaño'}
        )

        # 6. Crear Metas de Producción
        self.stdout.write('6. Creando Metas de Producción...')
        safe_get_or_create(
            MetaEstacion, 
            {'estacion': estacion_1}, 
            {'piezas_por_hora': 120, 'meta_piezas': 120, 'activo': True}
        )

        self.stdout.write(self.style.SUCCESS('=== Seeding finalizado con éxito (US-04 Completado) ==='))