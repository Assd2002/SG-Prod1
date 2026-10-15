from django.db import models


class Empleado(models.Model):
    numero_empleado = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Número de empleado",
    )
    nombre = models.CharField(
        max_length=150,
        verbose_name="Nombre completo",
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )

    def __str__(self):
        return f"{self.numero_empleado} - {self.nombre}"

    class Meta:
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"
        ordering = ["numero_empleado"]


class Linea(models.Model):
    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nombre de la línea",
    )
    activa = models.BooleanField(
        default=True,
        verbose_name="Activa",
    )

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Línea"
        verbose_name_plural = "Líneas"


class Estacion(models.Model):
    linea = models.ForeignKey(
        Linea,
        on_delete=models.CASCADE,
        related_name="estaciones",
        verbose_name="Línea",
    )
    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre de la estación",
    )
    activa = models.BooleanField(
        default=True,
        verbose_name="Activa",
    )

    def __str__(self):
        return f"{self.nombre} ({self.linea.nombre})"

    class Meta:
        verbose_name = "Estación"
        verbose_name_plural = "Estaciones"


class Habilidad(models.Model):
    NIVEL_CHOICES = [
        ("principiante", "Principiante"),
        ("autonomo", "Autónomo"),
        ("experto", "Experto"),
        ("instructor", "Instructor"),
    ]

    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.CASCADE,
        related_name="habilidades",
        verbose_name="Empleado",
    )
    estacion = models.ForeignKey(
        Estacion,
        on_delete=models.CASCADE,
        related_name="habilidades_estacion",
        verbose_name="Estación",
    )
    nivel = models.CharField(
        max_length=20,
        choices=NIVEL_CHOICES,
        verbose_name="Nivel de habilidad",
    )
    actualizado_en = models.DateTimeField(
        auto_now=True,
        verbose_name="Actualizado en",
    )

    def __str__(self):
        return f"{self.empleado.nombre} - {self.estacion.nombre} ({self.get_nivel_display()})"

    class Meta:
        verbose_name = "Habilidad"
        verbose_name_plural = "Habilidades"
        # Regla: Un empleado solo debe tener un nivel de habilidad por estación
        unique_together = ("empleado", "estacion")


class Asignacion(models.Model):
    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.CASCADE,
        related_name="asignaciones",
        verbose_name="Empleado",
    )
    estacion = models.ForeignKey(
        Estacion,
        on_delete=models.CASCADE,
        related_name="asignaciones",
        verbose_name="Estación",
    )
    fecha_inicio = models.DateTimeField(
        verbose_name="Fecha de inicio",
    )
    fecha_fin = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de fin",
    )

    def __str__(self):
        return f"{self.empleado.nombre} en {self.estacion.nombre}"

    class Meta:
        verbose_name = "Asignación"
        verbose_name_plural = "Asignaciones"


class RegistroHorario(models.Model):
    estacion = models.ForeignKey(
        Estacion,
        on_delete=models.CASCADE,
        related_name="registros_horarios",
        verbose_name="Estación",
    )
    fecha = models.DateField(
        verbose_name="Fecha del registro",
    )
    hora_inicio = models.TimeField(
        verbose_name="Hora de inicio",
    )
    hora_fin = models.TimeField(
        verbose_name="Hora de fin",
    )
    aceptadas = models.PositiveIntegerField(
        default=0,
        verbose_name="Piezas aceptadas",
    )
    rechazadas = models.PositiveIntegerField(
        default=0,
        verbose_name="Piezas rechazadas",
    )
    retrabajo = models.PositiveIntegerField(
        default=0,
        verbose_name="Piezas en retrabajo",
    )

    def __str__(self):
        return f"Registro {self.id} - {self.estacion.nombre} ({self.fecha})"

    class Meta:
        verbose_name = "Registro horario de producción"
        verbose_name_plural = "Registros horarios de producción"


class ParticipacionProduccion(models.Model):
    registro = models.ForeignKey(
        RegistroHorario,
        on_delete=models.CASCADE,
        related_name="participaciones",
        verbose_name="Registro horario",
    )
    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.CASCADE,
        related_name="participaciones_produccion",
        verbose_name="Empleado",
    )
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones",
    )

    def __str__(self):
        return f"{self.empleado.nombre} en Registro #{self.registro.id}"

    class Meta:
        verbose_name = "Participación en producción"
        verbose_name_plural = "Participaciones en producción"
        # Regla: La combinación registro_id + empleado_id debe ser única
        unique_together = ("registro", "empleado")


class CatalogoDefecto(models.Model):
    codigo = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Código del defecto",
    )
    nombre = models.CharField(
        max_length=150,
        verbose_name="Descripción del defecto",
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
    )

    def __str__(self):
        return f"[{self.codigo}] {self.nombre}"

    class Meta:
        verbose_name = "Catálogo de defecto"
        verbose_name_plural = "Catálogo de defectos"


class DetalleDefecto(models.Model):
    registro = models.ForeignKey(
        RegistroHorario,
        on_delete=models.CASCADE,
        related_name="detalles_defectos",
        verbose_name="Registro horario",
    )
    defecto = models.ForeignKey(
        CatalogoDefecto,
        on_delete=models.PROTECT,
        related_name="detalles",
        verbose_name="Defecto",
    )
    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="defectos_asociados",
        verbose_name="Empleado asociado",
    )
    cantidad = models.PositiveIntegerField(
        default=1,
        verbose_name="Cantidad",
    )

    def __str__(self):
        return f"{self.defecto.nombre} ({self.cantidad}) en Reg #{self.registro.id}"

    class Meta:
        verbose_name = "Detalle de defecto"
        verbose_name_plural = "Detalles de defectos"


class MetaProduccion(models.Model):
    estacion = models.ForeignKey(
        Estacion,
        on_delete=models.CASCADE,
        related_name="metas",
        verbose_name="Estación",
    )
    piezas_objetivo = models.PositiveIntegerField(
        verbose_name="Piezas objetivo",
    )
    vigente_desde = models.DateTimeField(
        verbose_name="Vigente desde",
    )
    vigente_hasta = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Vigente hasta",
    )

    def __str__(self):
        return f"Meta: {self.piezas_objetivo} pzas - {self.estacion.nombre}"

    class Meta:
        verbose_name = "Meta de producción"
        verbose_name_plural = "Metas de producción"