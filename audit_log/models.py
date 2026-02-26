from django.db import models
from users_hub.models import Usuario, Rol 


class Area(models.Model):
    area_id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, unique=True)
    ubicacion = models.CharField(max_length=255, null=True, blank=True)
    camara_ip = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre


class PermisoArea(models.Model):
    permiso_id = models.AutoField(primary_key=True)
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE)
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    puede_acceder = models.BooleanField(default=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('rol', 'area')


class RegistroAcceso(models.Model):
    registro_id = models.AutoField(primary_key=True)

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    rol = models.ForeignKey(
        Rol,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    area = models.ForeignKey(Area, on_delete=models.CASCADE)

    fecha_hora = models.DateTimeField(auto_now_add=True)

    permitido = models.BooleanField(default=False)

    estado = models.CharField(max_length=50)

    motivo_denegacion = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    foto_registro_path = models.ImageField(
        upload_to='capturas_acceso/',
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['-fecha_hora']
        indexes = [
            models.Index(fields=['fecha_hora']),
            models.Index(fields=['permitido']),
            models.Index(fields=['area']),
        ]
