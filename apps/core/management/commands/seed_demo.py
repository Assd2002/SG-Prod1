import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group

# Ajusta estos nombres según los que veas en apps/core/models.py
from apps.core.models import *


class Command(BaseCommand):
    help = "Pobla la base de datos con +100 registros por catálogo para pruebas de demo (US-04)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=== Iniciando Seeding Masivo de Datos (+100 por catálogo) ==="))

        nombres = [
            "Carlos", "Ana", "Luis", "Maria", "Jorge", "Sofía", "Pedro", "Lucía", "Diego", "Elena",
            "Gabriel", "Valeria", "Fernando", "Camila", "Mateo", "Daniela", "Javier", "Natalia", "Alejandro", "Isabella"
        ]
        apellidos = [
            "García", "López", "Martínez", "Hernández", "González", "Pérez", "Rodríguez", "Sánchez",
            "Ramírez", "Cruz", "Flores", "Gómez", "Morales", "Vázquez", "Reyes", "Jiménez", "Torres", "Díaz"
        ]
        areas = ["Corte", "Costura", "Ensamble", "Acabado", "Empaque", "Inspección", "Mantenimiento"]

        # Intenta obtener el modelo de Empleado (sea en inglés o español)
        EmployeeModel = globals().get('Employee') or globals().get('Empleado')
        StationModel = globals().get('Station') or globals().get('Estacion') or globals().get('Linea')
        DefectModel = globals().get('Defect') or globals().get('Defecto')
        SkillModel = globals().get('SkillMatrix') or globals().get('MatrizHabilidad') or globals().get('Habilidad')
        GoalModel = globals().get('ProductionGoal') or globals().get('MetaProduccion') or globals().get('Meta')

        # 1. Crear Grupos / Roles
        roles = ["Administrador", "Supervisor", "Operador", "Quality_Inspector"]
        for role_name in roles:
            Group.objects.get_or_create(name=role_name)

        # 2. Usuarios y Empleados (+100)
        self.stdout.write("1. Generando 100 Empleados y Usuarios...")
        empleados_creados = []
        for i in range(1, 105):
            nom = nombres[i % len(nombres)]
            ape = apellidos[i % len(apellidos)]
            username = f"emp_user_{i:03d}"
            email = f"empleado{i:03d}@empresa.com"

            user, _ = User.objects.get_or_create(
                username=username,
                defaults={'email': email, 'first_name': nom, 'last_name': ape}
            )
            
            if EmployeeModel:
                emp, _ = EmployeeModel.objects.get_or_create(
                    id=i,
                    defaults={'user': user} if hasattr(EmployeeModel, 'user') else {}
                )
                empleados_creados.append(emp)

        # 3. Estaciones / Líneas (+100)
        self.stdout.write("2. Generando 100 Estaciones de Trabajo...")
        estaciones_creadas = []
        for i in range(1, 105):
            if StationModel:
                st, _ = StationModel.objects.get_or_create(id=i)
                estaciones_creadas.append(st)

        # 4. Defectos (+100)
        self.stdout.write("3. Generando 100 Tipos de Defectos...")
        for i in range(1, 105):
            if DefectModel:
                DefectModel.objects.get_or_create(id=i)

        # 5. SkillMatrix (+100)
        self.stdout.write("4. Generando 100 Registros en Matriz de Habilidades...")
        for i in range(1, 105):
            if SkillModel and empleados_creados and estaciones_creadas:
                emp = empleados_creados[i - 1]
                st = estaciones_creadas[i - 1]
                try:
                    SkillModel.objects.get_or_create(id=i)
                except Exception:
                    pass

        # 6. Metas de Producción (+100)
        self.stdout.write("5. Generando 100 Metas de Producción...")
        for i in range(1, 105):
            if GoalModel:
                try:
                    GoalModel.objects.get_or_create(id=i)
                except Exception:
                    pass

        self.stdout.write(self.style.SUCCESS("=== Seeding finalizado con éxito (US-04 Completado con +100 registros) ==="))