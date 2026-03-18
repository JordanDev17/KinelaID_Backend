from rest_framework import viewsets
from .models import Usuario, Rol
from .serializers import UsuarioSerializer, RolSerializer


# =====================================================
# CRUD DE ROLES
# =====================================================
class RolViewSet(viewsets.ModelViewSet):
    """
    CRUD completo de roles del sistema.
    """
    queryset = Rol.objects.all()
    serializer_class = RolSerializer


# =====================================================
# CRUD DE USUARIOS
# =====================================================
class UsuarioViewSet(viewsets.ModelViewSet):
    """
    CRUD básico de usuarios.

    IMPORTANTE:
    Esta vista NO realiza biometría.
    El registro biométrico ocurre en access_control.
    """

    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer

    # Solo permite actualizar campos administrativos
    # El embedding lo genera el motor biométrico