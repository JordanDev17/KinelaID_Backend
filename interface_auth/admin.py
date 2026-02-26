from django.contrib import admin
from django.contrib.auth.hashers import make_password
from .models import InterfazUsuario

@admin.register(InterfazUsuario)
class InterfazUsuarioAdmin(admin.ModelAdmin):
    # Columnas que verás en la lista principal
    list_display = ('username', 'get_nombre', 'get_rol', 'require_2fa', 'is_active', 'ultimo_acceso')
    list_filter = ('is_active', 'require_2fa', 'perfil__rol')
    search_fields = ('username', 'perfil__nombre_completo', 'perfil__identificacion')

    # Métodos para traer datos del perfil vinculado
    def get_nombre(self, obj):
        return obj.perfil.nombre_completo
    get_nombre.short_description = 'Empleado'

    def get_rol(self, obj):
        return obj.perfil.rol.nombre
    get_rol.short_description = 'Rol de Sistema'

    # IMPORTANTE: Esto asegura que si cambias la contraseña desde el admin, se encripte
    def save_model(self, request, obj, form, change):
        if obj.password and not obj.password.startswith('pbkdf2_sha256$'):
            obj.password = make_password(obj.password)
        super().save_model(request, obj, form, change)