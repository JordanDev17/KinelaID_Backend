from rest_framework import serializers
from .models import Area, RegistroAcceso, PermisoArea

class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ['area_id', 'nombre', 'ubicacion', 'camara_ip']

class PermisoAreaSerializer(serializers.ModelSerializer):
    rol_nombre = serializers.CharField(source='rol.nombre', read_only=True)
    area_nombre = serializers.CharField(source='area.nombre', read_only=True)
    fecha_modificacion = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')

    class Meta:
        model = PermisoArea
        fields = [
            'permiso_id', 'rol', 'rol_nombre',
            'area', 'area_nombre',
            'puede_acceder', 'fecha_modificacion'
        ]

class RegistroAccesoSerializer(serializers.ModelSerializer):
    # Denormalización para el Frontend
    usuario_nombre = serializers.CharField(source='usuario.nombre_completo', read_only=True, default='DESCONOCIDO')
    identificacion = serializers.CharField(source='usuario.identificacion', read_only=True, default='N/A')
    area_nombre = serializers.CharField(source='area.nombre', read_only=True)
    rol_nombre = serializers.CharField(source='rol.nombre', read_only=True, default='SIN ROL')
    fecha_formateada = serializers.DateTimeField(source='fecha_hora', format='%Y-%m-%d %H:%M:%S', read_only=True)

    class Meta:
        model = RegistroAcceso
        fields = [
            'registro_id', 'usuario_nombre', 'identificacion', 'area_nombre', 
            'rol_nombre', 'fecha_formateada', 'permitido', 'estado', 'motivo_denegacion'
        ]