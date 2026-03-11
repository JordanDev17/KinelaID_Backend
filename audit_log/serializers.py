from rest_framework import serializers
from .models import Area, RegistroAcceso, PermisoArea
from users_hub.models import Rol


class AreaSerializer(serializers.ModelSerializer):
    """
    Serializa el modelo Area incluyendo ubicacion y camara_ip.
    camara_ip contiene la URL completa del stream M-JPEG:
      ej. http://127.0.0.1:8000/api/cameras/stream/0/
    """
    class Meta:
        model  = Area
        fields = ['area_id', 'nombre', 'ubicacion', 'camara_ip']


class PermisoAreaSerializer(serializers.ModelSerializer):
    """
    Serializa PermisoArea alineado al modelo real.
    
    Campos del modelo:
      permiso_id         → PK AutoField
      rol                → FK a Rol
      area               → FK a Area
      puede_acceder      → BooleanField
      fecha_modificacion → DateTimeField (auto_now=True)
    
    unique_together = ('rol', 'area')
    """
    # Campos de solo lectura para mostrar en el frontend
    rol_nombre         = serializers.CharField(source='rol.nombre',  read_only=True)
    area_nombre        = serializers.CharField(source='area.nombre', read_only=True)
    fecha_modificacion = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M')

    class Meta:
        model  = PermisoArea
        fields = [
            'permiso_id', 'rol', 'rol_nombre',
            'area', 'area_nombre',
            'puede_acceder', 'fecha_modificacion'
        ]
        # El campo PK se llama permiso_id, no id
        # DRF lo detecta por primary_key=True en el modelo


class RegistroAccesoSerializer(serializers.ModelSerializer):
    """
    Serializa RegistroAcceso con campos denormalizados
    para evitar joins en el frontend.
    """
    usuario_nombre = serializers.CharField(
        source='usuario.nombre_completo', read_only=True, default='DESCONOCIDO'
    )
    area_nombre    = serializers.CharField(source='area.nombre', read_only=True)
    rol_nombre     = serializers.CharField(source='rol.nombre',  read_only=True, default=None)
    fecha_formateada = serializers.DateTimeField(
        source='fecha_hora', format='%Y-%m-%d %H:%M:%S', read_only=True
    )

    class Meta:
        model  = RegistroAcceso
        fields = [
            'registro_id', 'usuario_nombre', 'area_nombre', 'rol_nombre',
            'fecha_formateada', 'permitido', 'estado', 'motivo_denegacion'
        ]

