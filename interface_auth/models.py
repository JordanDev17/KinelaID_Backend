from django.db import models
from users_hub.models import Usuario, Rol
from django.contrib.auth.hashers import make_password

class InterfazUsuario(models.Model):
    # Vinculamos con el usuario existente en users_hub
    perfil = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='acceso_interfaz')
    
    # Credenciales de acceso
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=128) # Hasheada
    
    # Configuración de Seguridad
    require_2fa = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    # Registro de actividad
    ultimo_acceso = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Hashear password si es nueva
        if self.password and not self.password.startswith('pbkdf2_sha256$'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} - {self.perfil.rol.nombre}"

    @property
    def permisos_frontend(self):
        """Retorna los permisos según el rol definido en users_hub"""
        rol = self.perfil.rol.nombre
        config = {
            "Gerente": {"crud_empleados": True, "logs": True, "reportes": True, "config_sistema": True},
            "Administrador": {"crud_empleados": True, "logs": True, "reportes": True, "config_sistema": False},
            "Operador de Registro": {"crud_empleados": True, "logs": False, "reportes": False, "config_sistema": False},
            "Operador de Reportes": {"crud_empleados": False, "logs": True, "reportes": True, "config_sistema": False},
        }
        return config.get(rol, {"error": "Sin permisos"})