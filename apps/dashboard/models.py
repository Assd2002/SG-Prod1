
# Create your models here.
from django.db import models

# Meta de producción por estación (RF-3.2)
class MetaEstacion(models.Model):
    estacion = models.OneToOneField('personal.Estacion', on_delete=models.CASCADE, related_name='meta')
    piezas_por_hora_meta = models.PositiveIntegerField(default=100)

    def __str__(self):
        return f"Meta {self.estacion}: {self.piezas_por_hora_meta} pzas/hr"

# Registro de Bonos e Incentivos (RF-3.3)
class BonoIncentivo(models.Model):
    empleado = models.ForeignKey('personal.Empleado', on_delete=models.CASCADE)
    periodo_inicio = models.DateField()
    periodo_fin = models.DateField()
    monto_bono = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    otorgado = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bono Cero Defectos - {self.empleado.nombre}"

# Alertas de Capacitación Dirigida (RF-3.4)
class AlertaCapacitacion(models.Model):
    estacion = models.ForeignKey('personal.Estacion', on_delete=models.CASCADE)
    empleado = models.ForeignKey('personal.Empleado', on_delete=models.CASCADE, null=True, blank=True)
    motivo = models.TextField()
    resuelto = models.BooleanField(default=False)
    fecha_generacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Capacitación requerida: {self.estacion} - {self.empleado}"