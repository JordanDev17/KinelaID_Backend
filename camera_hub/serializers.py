from rest_framework import serializers
from .models import Camara

class CamaraSerializer(serializers.ModelSerializer):
    # Incluimos la propiedad stream_url que definimos en el modelo
    stream_url = serializers.ReadOnlyField()
    nombre_area = serializers.CharField(source='area.nombre', read_only=True)

    class Meta:
        model = Camara
        fields = ['id', 'nombre', 'hardware_index', 'area', 'nombre_area', 'is_activa', 'descripcion', 'stream_url']