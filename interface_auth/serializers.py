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
        
class InterfazUsuarioListSerializer(serializers.ModelSerializer):
    """Solo lectura — no expone contraseña."""
    perfil_nombre = serializers.CharField(
        source='perfil.nombre_completo', read_only=True, default=None
    )
    rol_nombre    = serializers.CharField(
        source='perfil.rol.nombre', read_only=True, default=None
    )
    perfil_id     = serializers.IntegerField(
        source='perfil.usuario_id', read_only=True, default=None  # ← usuario_id, no id
    )
    tiene_2fa     = serializers.SerializerMethodField()

    class Meta:
        model  = InterfazUsuario
        fields = ['id', 'username', 'is_active', 'perfil_id', 'perfil_nombre', 'rol_nombre', 'tiene_2fa']

    def get_tiene_2fa(self, obj) -> bool:
        """True si el empleado vinculado tiene face_embedding registrado."""
        return bool(obj.perfil and obj.perfil.face_embedding)


class InterfazUsuarioWriteSerializer(serializers.ModelSerializer):
    """Escritura — acepta password (ya hasheado por el ViewSet)."""
    class Meta:
        model  = InterfazUsuario
        fields = ['id', 'username', 'password', 'is_active', 'perfil']
        extra_kwargs = {'password': {'write_only': True, 'required': False}}
