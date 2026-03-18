from rest_framework import serializers
from .models import Usuario, Rol


# =====================================================
# SERIALIZER ROL
# =====================================================
class RolSerializer(serializers.ModelSerializer):

    class Meta:
        model = Rol
        fields = ['rol_id', 'nombre', 'descripcion']


# =====================================================
# SERIALIZER USUARIO
# =====================================================
class UsuarioSerializer(serializers.ModelSerializer):

    # Devuelve detalles completos del rol
    rol_detalle = RolSerializer(source='rol', read_only=True)

    class Meta:
        model = Usuario

        fields = [
            'usuario_id',
            'nombre_completo',
            'identificacion',
            'email',
            'activo',
            'rol',
            'rol_detalle',
            'face_embedding',
            'fecha_creacion'
        ]

        # Embedding NO puede escribirse desde el cliente
        extra_kwargs = {
            'face_embedding': {'read_only': True}
        }