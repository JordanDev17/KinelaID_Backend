from rest_framework import serializers
from .models import Usuario, Rol

class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Rol
        fields = ['rol_id', 'nombre', 'descripcion']


class UsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Usuario real.
    IMPORTANTE: NO hay campo 'cargo' ni 'username' en Usuario.
    Campos: usuario_id, nombre_completo, identificacion,
            email, activo, rol(FK), face_embedding, fecha_creacion
    """
    # Expone el objeto rol completo (no solo el ID)
    rol_detalle = RolSerializer(source='rol', read_only=True)

    class Meta:
        model  = Usuario
        fields = [
            'usuario_id', 'nombre_completo', 'identificacion',
            'email', 'activo', 'rol', 'rol_detalle',
            'face_embedding', 'fecha_creacion'
        ]
        # face_embedding no se escribe desde fuera (se genera en el servidor)
        extra_kwargs = {
            'face_embedding': {'read_only': True},
        }
