from django.db import models
from audit_log.models import Area  # Importamos tu modelo Area existente

class Camara(models.Model):
    nombre = models.CharField(max_length=100, help_text="Ej: Cámara Entrada Principal")
    # El hardware_index es el 0, 1, 2 que reconoce OpenCV en tu PC
    hardware_index = models.IntegerField(unique=True, help_text="Índice USB (0, 1, 2...)")
    area = models.ForeignKey(Area, on_delete=models.CASCADE, related_name='camaras')
    is_activa = models.BooleanField(default=True)
    descripcion = models.TextField(blank=True, null=True)
    
    # Este campo no se llena manualmente, lo construiremos dinámicamente en el Serializer
    # o mediante una propiedad para que el Frontend sepa a qué URL conectarse.
    @property
    def stream_url(self):
        return f"/cameras/stream/{self.hardware_index}/"

    def __str__(self):
        return f"{self.nombre} - Área: {self.area.nombre}"