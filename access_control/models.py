from django.db import models
from audit_log.models import Area


class Camara(models.Model):
    """
    Representa una cámara física o lógica del sistema.
    """

    camara_id = models.AutoField(primary_key=True)

    nombre = models.CharField(
        max_length=100,
        help_text="Nombre descriptivo de la cámara"
    )

    ip = models.GenericIPAddressField(
        unique=True,
        help_text="IP desde donde se conecta la cámara"
    )

    area = models.ForeignKey(
        Area,
        on_delete=models.CASCADE,
        related_name='camaras'
    )

    activa = models.BooleanField(default=True)

    descripcion = models.TextField(null=True, blank=True)

    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} - {self.ip}"
