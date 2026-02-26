from rest_framework import serializers
from .models import InterfazUsuario

class InterfazUsuarioSerializer(serializers.ModelSerializer):
    rol_nombre = serializers.ReadOnlyField(source='perfil.rol.nombre')
    nombre_completo = serializers.ReadOnlyField(source='perfil.nombre_completo')
    # Traemos el embedding para comparar en la vista de login facial
    face_embedding = serializers.ReadOnlyField(source='perfil.face_embedding')
    permisos = serializers.ReadOnlyField(source='permisos_frontend')

    class Meta:
        model = InterfazUsuario
        fields = [
            'id', 'username', 'nombre_completo', 'rol_nombre', 
            'permisos', 'face_embedding', 'is_active'
        ]