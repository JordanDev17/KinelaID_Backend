from rest_framework import serializers
from .models import Usuario, Rol

class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = '__all__'

class UsuarioSerializer(serializers.ModelSerializer):
    # Mostramos el nombre del rol en las respuestas, pero recibimos el ID al crear
    rol_nombre = serializers.ReadOnlyField(source='rol.nombre')

    class Meta:
        model = Usuario
        fields = [
            'usuario_id', 'rol', 'rol_nombre', 'nombre_completo', 
            'identificacion', 'email', 'activo', 'face_embedding'
        ]