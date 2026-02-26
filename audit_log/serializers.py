from rest_framework import serializers
from .models import Area, RegistroAcceso, PermisoArea

class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = '__all__'

class RegistroAccesoSerializer(serializers.ModelSerializer):
    # Campos de solo lectura para mostrar nombres en lugar de IDs
    usuario_nombre = serializers.ReadOnlyField(source='usuario.nombre_completo')
    area_nombre = serializers.ReadOnlyField(source='area.nombre')
    rol_nombre = serializers.ReadOnlyField(source='rol.nombre')
    fecha_formateada = serializers.DateTimeField(source='fecha_hora', format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = RegistroAcceso
        fields = [
            'registro_id', 'usuario', 'usuario_nombre', 'rol', 'rol_nombre',
            'area', 'area_nombre', 'fecha_hora', 'fecha_formateada',
            'permitido', 'estado', 'motivo_denegacion'
        ]